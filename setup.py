from setuptools import setup, find_namespace_packages

setup(
    name="livekit-plugins-dify",
    version="0.1.0",
    description="A LiveKit plugin that integrates with Dify.ai for LLM capabilities",
    author="Abdelwahab Elghandour",
    author_email="",  # Add your email if you want
    url="https://github.com/Elghandour-eng/dify_livekit_plugin",
    packages=find_namespace_packages(include=["livekit.*"]),
    install_requires=[
        "aiohttp>=3.8.0"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)