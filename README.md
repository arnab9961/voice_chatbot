# Voice Chatbot with LLaMA 4

A Streamlit-based voice chatbot that allows you to speak with LLaMA 4 using your microphone.

## Features

- Voice input via microphone
- Speech-to-text with OpenAI Whisper
- LLaMA 4 integration via OpenRouter API
- Text-to-speech responses
- Chat history display

## Setup

1. Install the required packages:
```
pip install -r requirements.txt
```

2. Set your OpenRouter API key as an environment variable:
```
export OPENROUTER_API_KEY="your_api_key_here"
```

3. Run the Streamlit app:
```
streamlit run main.py
```

## Usage

1. Click the "🎤 Speak" button
2. Speak your question or prompt
3. Wait for the response
4. The bot will reply in both text and speech

## Requirements

- Python 3.8+
- Microphone access
- OpenRouter API key
```

