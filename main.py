import streamlit as st
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
import requests
import pyttsx3
import time
import os
import wave
from threading import Thread
from gtts import gTTS
from io import BytesIO
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
# Add these imports for proper thread context handling
from streamlit.runtime.scriptrunner import get_script_run_ctx, add_script_run_ctx
# Add Gmail API imports
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import re
# Add import for language detection
from langdetect import detect, LangDetectException

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🤖",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_recorder_state" not in st.session_state:
    st.session_state.audio_recorder_state = "stopped"

# Add speaking state to session state
if "speaking" not in st.session_state:
    st.session_state.speaking = False

# Add stop event to control speech
if "stop_speech" not in st.session_state:
    st.session_state.stop_speech = False

# Add audio playback state to session state
if "play_audio" not in st.session_state:
    st.session_state.play_audio = False

if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# Add input_key to session state
if "input_key" not in st.session_state:
    st.session_state.input_key = 0  # We'll use this to force text input refresh

# Add language preference to session state
if "language" not in st.session_state:
    st.session_state.language = "auto"  # Options: "auto", "en", "bn"

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone."""
    st.session_state.audio_recorder_state = "recording"
    
    # Record audio
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    
    with st.spinner("Recording..."):
        # Wait for the recording to complete
        sd.wait()
    
    st.session_state.audio_recorder_state = "stopped"
    return recording, sample_rate

def save_audio(recording, sample_rate, filename="output.wav"):
    """Save the recorded audio to a file."""
    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", filename)
    sf.write(file_path, recording, sample_rate)
    return file_path

def detect_language(text):
    """Detect the language of the input text."""
    try:
        lang = detect(text)
        # Map language codes to our supported languages
        if lang == 'bn':
            return 'bn'  # Bengali
        else:
            return 'en'  # Default to English for all other languages
    except LangDetectException:
        return 'en'  # Default to English if detection fails

def transcribe_audio(audio_file):
    """Transcribe audio using SpeechRecognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
            # Try to transcribe with the selected language or auto-detect
            if st.session_state.language == "bn":
                # Use Bengali language
                text = recognizer.recognize_google(audio_data, language="bn-BD")
            elif st.session_state.language == "auto":
                # First try with general English
                try:
                    text = recognizer.recognize_google(audio_data)
                except:
                    # If English fails, try Bengali
                    text = recognizer.recognize_google(audio_data, language="bn-BD")
            else:
                # Default to English
                text = recognizer.recognize_google(audio_data)
                
            return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError as e:
        return f"Speech recognition service error: {e}"
    except Exception as e:
        return f"Error during transcription: {str(e)}"

def extract_email_details(text):
    """Extract email address and message from text."""
    # Basic pattern for extracting email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Try to find email addresses in the text
    email_matches = re.findall(email_pattern, text)
    
    if not email_matches:
        return None, None, "Could not find a valid email address in your message."
    
    recipient = email_matches[0]
    
    # Try to extract subject
    subject_match = re.search(r'subject[:\s]+([^\n.]+)', text, re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else "Message from Voice Assistant"
    
    # Remove email address and subject from message to isolate content
    message = text
    for email in email_matches:
        message = message.replace(email, "")
    if subject_match:
        message = message.replace(subject_match.group(0), "")
    
    # Clean up message
    message = re.sub(r'send\s+(?:an?\s+)?email\s+(?:to\s+)?', '', message, flags=re.IGNORECASE)
    message = re.sub(r'with\s+(?:the\s+)?message\s+', '', message, flags=re.IGNORECASE)
    message = message.strip()
    
    if not message:
        return recipient, subject, "I found an email address but couldn't understand the message content."
    
    return recipient, subject, message

def get_gmail_credentials():
    """Get or refresh Gmail credentials."""
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'
    
    # Client ID from configuration
    CLIENT_ID = "900054230602-oi3h58bb73fa38k0hs7fl5fe8fn2jqrq.apps.googleusercontent.com"
    
    # Check if token.json exists
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()), SCOPES)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    # If no valid credentials available, prompt login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None
        
        # If credentials still not valid, try OAuth flow
        if not creds:
            try:
                # Check if credentials.json exists first
                if os.path.exists(credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                else:
                    # Use client ID directly if credentials.json doesn't exist
                    flow = InstalledAppFlow.from_client_config({
                        "installed": {
                            "client_id": CLIENT_ID,
                            "project_id": "voice-chatbot-gmail",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                        }
                    }, SCOPES)
                
                # Run the flow
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                return None, f"Error during authentication: {str(e)}"
    
    return creds, None

def send_email(recipient, subject, message):
    """Send an email using Gmail API."""
    try:
        creds, error = get_gmail_credentials()
        if error:
            return False, error
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create message
        email_message = MIMEText(message)
        email_message['to'] = recipient
        email_message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
        
        # Send message
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True, f"Email sent successfully to {recipient}!"
    
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def handle_email_request(text):
    """Process a request to send an email."""
    recipient, subject, message = extract_email_details(text)
    
    if not recipient:
        return message  # This will be the error message from extract_email_details
    
    # Send the email
    success, result = send_email(recipient, subject, message)
    
    if success:
        return result
    else:
        return f"Failed to send email: {result}"

def get_bot_response(prompt):
    """Get response from LLaMA 4 via OpenRouter API."""
    # Check if this is an email request
    if any(keyword in prompt.lower() for keyword in ["send email", "send an email", "send a mail", "send mail"]):
        return handle_email_request(prompt)
    
    # Detect language
    if st.session_state.language == "auto":
        detected_lang = detect_language(prompt)
    else:
        detected_lang = st.session_state.language
    
    # Get API key from environment variable loaded from .env
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    
    if not api_key:
        return "Error: OpenRouter API key not found. Please check your .env file."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # For Bengali, add instruction to respond in Bengali
    if detected_lang == "bn":
        system_message = "Please respond in Bengali (Bangla) language."
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    else:
        messages = [{"role": "user", "content": prompt}]
    
    data = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": messages,
        "max_tokens": 1024
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def speak_text(text):
    """Convert text to speech using pyttsx3 or gTTS based on language."""
    try:
        # Set speaking state to True
        st.session_state.speaking = True
        st.session_state.stop_speech = False
        
        # Detect language if set to auto
        if st.session_state.language == "auto":
            detected_lang = detect_language(text)
        else:
            detected_lang = st.session_state.language
        
        # For Bengali, always use gTTS
        if detected_lang == "bn":
            speak_with_gtts(text, lang="bn")
            return
        
        # For English, use pyttsx3
        engine = pyttsx3.init()
        
        # Split text into sentences to enable stopping between sentences
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            if st.session_state.stop_speech:
                break
            
            engine.say(sentence)
            engine.runAndWait()
            
            # Small delay to check stop condition
            time.sleep(0.1)
            
        # Reset speaking state
        st.session_state.speaking = False
    except Exception as e:
        # Don't use st.error in a thread
        print(f"Error with pyttsx3: {e}")
        # Fallback to gTTS
        speak_with_gtts(text)
        st.session_state.speaking = False

def speak_with_gtts(text, lang=None):
    """Alternative TTS using Google's Text-to-Speech with language support."""
    try:
        st.session_state.speaking = True
        st.session_state.stop_speech = False
        
        # If language not specified, detect it
        if lang is None:
            if st.session_state.language == "auto":
                lang = detect_language(text)
            else:
                lang = st.session_state.language
        
        # Create a list to hold file paths for cleanup
        temp_files = []
        
        # Split text into shorter segments for better control
        segments = []
        current_segment = ""
        
        for word in text.split():
            current_segment += word + " "
            if len(current_segment) > 100:  # Break into ~100 character segments
                segments.append(current_segment)
                current_segment = ""
        
        if current_segment:  # Add the last segment if it exists
            segments.append(current_segment)
        
        for segment in segments:
            if st.session_state.stop_speech:
                break
                
            tts = gTTS(text=segment, lang=lang)
            
            # Create a temp file and save the path for cleanup
            with NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                file_path = fp.name
                temp_files.append(file_path)
                tts.save(file_path)
                
                # Use the main thread's context to play audio
                st.session_state.audio_file = file_path
                # Signal the main thread to play it
                st.session_state.play_audio = True
                
                # Wait until it's played or stopped
                time.sleep(0.5)
                
            if st.session_state.stop_speech:
                break
                
            time.sleep(0.1)  # Brief pause to check stop condition
        
        # Cleanup temp files
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass
            
        st.session_state.speaking = False
    except Exception as e:
        # Don't use st.error in a thread
        print(f"Error with gTTS: {e}")
        st.session_state.speaking = False

def speak_in_background(text):
    """Speak text in a background thread to not block the UI."""
    # Get the current Streamlit context
    ctx = get_script_run_ctx()
    thread = Thread(target=speak_text, args=(text,))
    thread.daemon = True  # Set as daemon so it doesn't block app shutdown
    # Add the context to the thread
    add_script_run_ctx(thread, ctx)
    thread.start()

def stop_speaking():
    """Stop the current speech."""
    if st.session_state.speaking:
        st.session_state.stop_speech = True
        # Give slightly more time for the speech engine to respond to the stop flag
        time.sleep(0.5)
        st.session_state.speaking = False
        st.success("Speech stopped")

# App title
st.title("Voice Chatbot")
st.markdown("Talk to LLaMA 4 using your voice 🎤 or text 💬")

# Replace the sidebar with a version that includes language selection
with st.sidebar:
    st.title("Settings")
    
    # Language selection
    st.subheader("Language")
    language_option = st.radio(
        "Select language:",
        options=["Auto Detect", "English", "Bengali"],
        index=0,
        key="language_selector"
    )
    
    # Map the radio button selection to language codes
    if language_option == "Bengali":
        st.session_state.language = "bn"
    elif language_option == "English":
        st.session_state.language = "en"
    else:
        st.session_state.language = "auto"
    
    st.divider()
    
    st.title("About")
    st.markdown("""
    This voice chatbot uses:
    - SpeechRecognition for transcription
    - OpenRouter API to access LLaMA 4
    - Text-to-speech for responses
    - Supports English and Bengali
    """)

# Audio player for gTTS segments
if st.session_state.play_audio and st.session_state.audio_file:
    # Only play if we're not stopping
    if not st.session_state.stop_speech:
        try:
            st.audio(st.session_state.audio_file)
        except:
            pass
    # Reset the flag
    st.session_state.play_audio = False
    st.session_state.audio_file = None

# Chat container for history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Function to process user input (both text and voice)
def process_user_input(user_text):
    """Process user input and generate bot response"""
    # Display user message
    with st.chat_message("user"):
        st.write(user_text)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Get bot response
    with st.spinner("Thinking..."):
        bot_response = get_bot_response(user_text)
    
    # Display bot message
    with st.chat_message("assistant"):
        st.write(bot_response)
    
    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    # Speak response
    speak_in_background(bot_response)
    
    return bot_response

# Text input for chat
with st.container():
    st.write("### Type your message")
    col_text1, col_text2 = st.columns([4, 1])
    
    with col_text1:
        # Use dynamic key based on counter to force refresh
        user_text_input = st.text_input("Message", key=f"text_input_{st.session_state.input_key}", label_visibility="collapsed")
    
    with col_text2:
        send_button = st.button("Send", use_container_width=True)
    
    if send_button and user_text_input:
        user_text = user_text_input  # Store the input text
        process_user_input(user_text)
        
        # Increment the key to create a new text input on next rerun
        st.session_state.input_key += 1
        st.rerun()

# Voice control elements
st.write("### Or use your voice")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Mic button
    button_text = "🎤 Speak" if st.session_state.audio_recorder_state == "stopped" else "🔴 Recording..."
    if st.button(button_text, type="primary", disabled=st.session_state.audio_recorder_state == "recording"):
        # Record audio
        recording, sample_rate = record_audio()
        audio_file = save_audio(recording, sample_rate)
        
        # Transcribe
        user_text = transcribe_audio(audio_file)
        
        # Process the transcribed text
        process_user_input(user_text)

with col2:
    # Stop speaking button
    if st.button("🔇 Stop Speaking", disabled=not st.session_state.speaking):
        stop_speaking()
        st.rerun()

with col3:
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Add some instructions at the bottom
with st.expander("ℹ️ How to use"):
    st.markdown("""
    **Text Chat:**
    1. Type your message in the text field (English or Bengali)
    2. Click "Send" or press Enter
    
    **Voice Chat:**
    1. Click the "🎤 Speak" button
    2. Speak clearly into your microphone (English or Bengali)
    3. Wait for the response
    
    **Language Selection:**
    - Use the sidebar to select your preferred language
    - Auto Detect will try to determine the language from your input
    - Selecting Bengali will force responses in Bengali
    
    The bot will answer both in text and speech.
    
    **Note:** Make sure your microphone is working and allowed in your browser.
    """)
