from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
from googletrans import Translator
from pydub import AudioSegment
import io

app = Flask(__name__)
CORS(app, resources={r"/voice": {"origins": "http://localhost:5173"}})

recognizer = sr.Recognizer()
translator = Translator()

@app.route('/voice', methods=['POST'])
def voice_recognition():
    if request.method == 'POST':
        audio = request.files['audio']
        lang = request.form.get('lang')

        # Convert audio file to WAV format if it's not already
        audio_file = io.BytesIO(audio.read())
        audio_segment = AudioSegment.from_file(audio_file)
        audio_wav = io.BytesIO()
        audio_segment.export(audio_wav, format='wav')
        audio_wav.seek(0)

        # Use SpeechRecognition to process the audio
        with sr.AudioFile(audio_wav) as source:
            audio_data = recognizer.record(source)
            try:
                # Recognize the speech in the audio file
                text = recognizer.recognize_google(audio_data, language=lang)
            except sr.UnknownValueError:
                return jsonify({'error': 'Speech Recognition could not understand the audio'}), 400
            except sr.RequestError as e:
                return jsonify({'error': f'Could not request results; {e}'}), 500

        # Translate to English if needed
        if lang in ['hi', 'pa', 'gu', 'bn', 'ta', 'te', 'ml', 'kn', 'mr', 'ur']:
            text = translator.translate(text, src=lang, dest='en').text

        # Determine the page
        if 'wheat' in text.lower():
            page = 'wheat'
        elif 'jowar' in text.lower():
            page = 'jowar'
        elif 'bajra' in text.lower():
            page = 'bajra'
        else:
            page = 'home'

        return jsonify({'page': page, 'text': text})

    return "This endpoint is for voice recognition. Please send a POST request with an audio file."

if __name__ == '__main__':
    app.run(debug=True)
