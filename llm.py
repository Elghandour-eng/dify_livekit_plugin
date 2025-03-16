from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiohttp
from livekit.agents import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    llm,
    utils,
)
from livekit.agents.llm import LLMCapabilities
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions

from .log import logger

@dataclass
class LLMOptions:
    api_key: str
    api_base: str
    temperature: float | None
    conversation_id: str | None

class LLM(llm.LLM):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float | None = None,
        conversation_id: str | None = None,
    ) -> None:
        """
        Create a new instance of Dify LLM.

        api_key (str | None): The Dify API key. Defaults to DIFY_API_KEY env var.
        api_base (str | None): The base URL for the Dify API. Defaults to https://api.dify.ai
        temperature (float | None): The temperature for generation. Defaults to None.
        conversation_id (str | None): The conversation ID to continue. Defaults to None.
        """
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = LLMCapabilities(
            supports_choices_on_int=False,
        )

        api_key = api_key or os.environ.get("DIFY_API_KEY")
        if api_key is None:
            raise ValueError("Dify API key is required")

        self._opts = LLMOptions(
            api_key=api_key,
            api_base=api_base or "https://api.dify.ai",
            temperature=temperature,
            conversation_id=conversation_id,
        )

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        temperature: float | None = None,
        fnc_ctx: Any = None,
    ) -> "LLMStream":
        """Start a chat completion stream"""
        if temperature is None:
            temperature = self._opts.temperature

        # Extract the last user message
        last_message = next(
            (msg for msg in reversed(chat_ctx.messages) if msg.role == "user"), 
            None
        )
        if not last_message:
            raise ValueError("No user message found in chat context")

        # Prepare the request payload
        payload = {
            "inputs": {},
            "query": last_message.content,
            "response_mode": "streaming",
            "conversation_id": self._opts.conversation_id or "",
            "user": "user"
        }

        if temperature is not None:
            payload["temperature"] = temperature

        # Create headers
        headers = {
            "Authorization": f"Bearer {self._opts.api_key}",
            "Content-Type": "application/json"
        }

        # Create or reuse the session
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        # Create the stream
        stream = self._session.post(
            f"{self._opts.api_base}/v1/chat-messages",
            headers=headers,
            json=payload
        )

        return LLMStream(
            self,
            dify_stream=stream,
            chat_ctx=chat_ctx,
            conn_options=conn_options,
            fnc_ctx=fnc_ctx,
        )

    async def close(self) -> None:
        """Close the LLM client and cleanup resources"""
        if self._session is not None:
            await self._session.close()
            self._session = None

    @classmethod
    def from_env(cls) -> "LLM":
        """Create a DifyLLM instance from environment variables"""
        api_key = os.getenv("DIFY_API_KEY")
        if not api_key:
            raise ValueError("DIFY_API_KEY environment variable is required")
            
        api_base = os.getenv("DIFY_API_BASE", "https://api.dify.ai")
        
        return cls(
            api_key=api_key,
            api_base=api_base,
        )

class LLMStream(llm.LLMStream):
    def __init__(
        self,
        llm: LLM,
        *,
        dify_stream: aiohttp.ClientResponse,
        chat_ctx: llm.ChatContext,
        conn_options: APIConnectOptions,
        fnc_ctx: Any = None,
    ) -> None:
        super().__init__(
            llm, 
            chat_ctx=chat_ctx,
            conn_options=conn_options,
            fnc_ctx=fnc_ctx
        )
        self._awaitable_dify_stream = dify_stream
        self._dify_stream: aiohttp.ClientResponse | None = None
        self._request_id: str = ""
        self._input_tokens = 0
        self._output_tokens = 0

    async def _run(self) -> None:
        retryable = True
        try:
            if not self._dify_stream:
                self._dify_stream = await self._awaitable_dify_stream

            async with self._dify_stream as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIStatusError(
                        f"Dify API error: {error_text}",
                        status_code=response.status,
                        body=error_text,
                    )

                async for line in response.content:
                    if line:
                        try:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = json.loads(line[6:])
                                chat_chunk = self._parse_event(data)
                                if chat_chunk is not None:
                                    self._event_ch.send_nowait(chat_chunk)
                                    retryable = False
                        except Exception as e:
                            logger.error(f"Error processing stream: {e}")
                            continue

                # Send final usage stats
                self._event_ch.send_nowait(
                    llm.ChatChunk(
                        request_id=self._request_id,
                        usage=llm.CompletionUsage(
                            completion_tokens=self._output_tokens,
                            prompt_tokens=self._input_tokens,
                            total_tokens=self._input_tokens + self._output_tokens,
                        ),
                    )
                )

        except aiohttp.ClientError as e:
            raise APIConnectionError(retryable=retryable) from e
        except Exception as e:
            raise APIConnectionError(retryable=retryable) from e

    def _parse_event(self, event: Dict[str, Any]) -> llm.ChatChunk | None:
        """Parse a Dify event into a ChatChunk"""
        event_type = event.get("event")

        if event_type == "message_end":
            # Update usage statistics
            if "metadata" in event and "usage" in event["metadata"]:
                usage = event["metadata"]["usage"]
                self._input_tokens = usage.get("prompt_tokens", 0)
                self._output_tokens = usage.get("completion_tokens", 0)
            return None

        elif event_type == "agent_message":
            # Extract message content
            answer = event.get("answer", "")
            if not answer:
                return None

            return llm.ChatChunk(
                request_id=event.get("message_id", ""),
                choices=[
                    llm.Choice(
                        delta=llm.ChoiceDelta(
                            content=answer,
                            role="assistant"
                        )
                    )
                ],
            )

        return None