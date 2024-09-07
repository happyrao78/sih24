from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import os
import re
import io
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API_KEY environment variable
api_key = os.getenv("API_KEY")
if api_key is None:
    raise ValueError("API_KEY environment variable not set")

genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app, resources={r"/voice": {"origins": "http://localhost:5173"}})

recognizer = sr.Recognizer()
audio_dir = "audio_output"
os.makedirs(audio_dir, exist_ok=True)  # Ensure directory exists

def clean_text(text):
    # Remove numericals and special characters, keeping basic punctuation
    cleaned_text = re.sub(r'[0-9]', '', text)  # Remove numericals
    cleaned_text = re.sub(r'[^\w\s.,!?]', '', cleaned_text)  # Remove special characters
    return cleaned_text

def summarize_text(text, max_words=50):
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Split text into words
    words = cleaned_text.split()
    
    # Initialize variables
    summary = ""
    word_count = 0
    
    # Build the summary ensuring it ends at the end of a sentence
    for word in words:
        if word_count < max_words:
            summary += word + " "
            word_count += 1
        else:
            break
    
    # Ensure the summary ends with a full stop if it doesn't already
    if not summary.strip().endswith(('.', '!', '?')):
        summary = summary.strip() + '.'
    
    return summary.strip()

@app.route('/voice', methods=['POST'])
def voice_recognition():
    if request.method == 'POST':
        if 'audio' not in request.files:
            return jsonify({'error': 'Missing required file: audio'}), 400

        audio = request.files['audio']
        lang = request.form.get('lang', 'en')

        # Convert audio file to WAV format if it's not already
        try:
            audio_file = io.BytesIO(audio.read())
            audio_segment = AudioSegment.from_file(audio_file)
            audio_wav = io.BytesIO()
            audio_segment.export(audio_wav, format='wav')
            audio_wav.seek(0)
        except Exception as e:
            return jsonify({'error': f'Failed to process audio file: {e}'}), 400

        # Use SpeechRecognition to process the audio
        try:
            with sr.AudioFile(audio_wav) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language=lang)
        except sr.UnknownValueError:
            return jsonify({'error': 'Speech Recognition could not understand the audio'}), 400
        except sr.RequestError as e:
            return jsonify({'error': f'Could not request results; {e}'}), 500

        # Generate content with Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(text)

        # Summarize the response
        summary = summarize_text(response.text)
        final_text = f"{summary} Thank you."

        # Generate audio from the final text
        audio_file_path = os.path.join(audio_dir, "output.mp3")
        tts = gTTS(text=final_text, lang='en')
        tts.save(audio_file_path)

        # Determine the page
        page = 'home'
        if 'wheat' in text.lower():
            page = 'wheat'
        elif 'jowar' in text.lower():
            page = 'jowar'
        elif 'bajra' in text.lower():
            page = 'bajra'

        return jsonify({
            'page': page,
            'text': final_text,
            'audio_url': f'/audio/output.mp3'
        })

    return "This endpoint is for voice recognition. Please send a POST request with an audio file."

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(audio_dir, filename)

if __name__ == '__main__':
    app.run(debug=True)
