# Dify Plugin for LiveKit

A LiveKit plugin that integrates with Dify.ai to provide LLM (Large Language Model) capabilities for conversational AI applications.

## Overview

This plugin enables LiveKit applications to use Dify.ai's API for natural language processing and conversation management. It provides a streaming interface for real-time chat responses and handles conversation context management.

## Features

- Real-time streaming responses
- Environment variable configuration
- Conversation context management
- Customizable temperature settings
- Detailed debug logging
- Proper session management and cleanup
- Error handling with retries

## Installation

### Option 1: Install from GitHub Repository

1. Clone the repository:
```bash
git clone https://github.com/Elghandour-eng/dify_livekit_plugin.git
```

2. Copy the `dify` folder to your project's plugins directory:
```bash
cp -r dify_livekit_plugin/livekit/plugins/dify backend/src/livekit/plugins/
```

3. Install the required dependencies:
```bash
pip install aiohttp
```

### Option 2: Manual Installation

1. Ensure you have the required dependencies:
```bash
pip install aiohttp
```

2. Add the plugin to your LiveKit project structure:
```
livekit/
└── plugins/
    └── dify/
        ├── __init__.py
        ├── llm.py
        └── log.py
```

## Configuration

### Environment Variables

- `DIFY_API_KEY` (required): Your Dify API key
- `DIFY_API_BASE` (optional): Custom API base URL (defaults to "https://api.dify.ai")

Example `.env` file:
```env
DIFY_API_KEY=your_api_key_here
DIFY_API_BASE=https://api.dify.ai  # Optional
```

## Usage

### Basic Usage

```python
from livekit.plugins.dify import LLM

# Initialize with environment variables
llm = LLM()

# Or initialize with explicit configuration
llm = LLM(
    api_key="your-api-key",
    api_base="https://api.dify.ai",
    conversation_id="optional-conversation-id"
)

# Use in a chat context
response = await llm.chat(chat_ctx=context)
```

### Integration with LiveKit Agent

```python
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins.dify import LLM

# Initialize Dify LLM
llm_client = LLM()

# Create agent with Dify LLM
agent = VoicePipelineAgent(
    vad=vad,
    stt=stt,
    llm=llm_client,
    tts=tts,
    chat_ctx=initial_ctx,
)
```

## Advanced Configuration

### Conversation Management

Track conversations with IDs:

```python
llm = LLM(conversation_id="user-123-session-456")
```

## Error Handling

The plugin includes comprehensive error handling:

- `ValueError`: Missing or invalid configuration
- `APIConnectionError`: Network or connection issues
- `APIStatusError`: API response errors

Example error handling:

```python
try:
    response = await llm.chat(chat_ctx=context)
except ValueError as e:
    print(f"Configuration error: {e}")
except APIConnectionError as e:
    print(f"Connection error: {e}")
except APIStatusError as e:
    print(f"API error: {e}")
```

## Debugging

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

The plugin will log:
- Chat context messages
- API request details
- Error information
- Session management events

## Best Practices

1. **Environment Variables**
   - Use environment variables for sensitive information
   - Keep API keys secure

2. **Session Management**
   - Let the plugin handle session lifecycle
   - Sessions are automatically cleaned up

3. **Error Handling**
   - Implement proper error handling
   - Check logs for detailed error information

4. **Performance**
   - Reuse LLM instances when possible
   - Close sessions when done

## Troubleshooting

### Common Issues

1. **"Dify API key is required" Error**
   - Ensure DIFY_API_KEY is set in environment
   - Check API key validity

2. **Connection Errors**
   - Verify internet connection
   - Check API base URL
   - Ensure firewall allows connection

3. **Empty Responses**
   - Check query content
   - Verify API key permissions
   - Check conversation context

### Debug Mode

Enable debug mode for detailed logs:

```python
import logging
logging.getLogger("livekit.plugins.dify").setLevel(logging.DEBUG)
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This plugin is part of the LiveKit project and follows its licensing terms.