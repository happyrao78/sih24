import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, useNavigate, useLocation } from 'react-router-dom';
import Wheat from './pages/Wheat';
import Jowar from './pages/Jowar';
import Bajra from './pages/Bajra';

// Component for handling voice input and navigation
function VoiceButton() {
  const navigate = useNavigate();
  const [generatedText, setGeneratedText] = useState('');
  const [audioUrl, setAudioUrl] = useState('');

  // Function to handle voice input
  async function handleVoiceInput() {
    try {
      const audioBlob = await getAudioBlob();
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('lang', 'en'); // Set the language as needed (e.g., 'en', 'hi', 'pa')

      const response = await fetch('http://localhost:5000/voice', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();

      if (data.page) {
        navigate(`/${data.page}`);
      } else if (data.text && data.audio_url) {
        // Update state to display the generated text and audio
        setGeneratedText(data.text);
        setAudioUrl(data.audio_url);
      } else {
        console.error('No page or text returned from server.');
      }
    } catch (error) {
      console.error('Error handling voice input:', error);
    }
  }

  // Function to record audio from the user's microphone
  async function getAudioBlob() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    mediaRecorder.start();

    // Record for 10 seconds
    await new Promise(resolve => setTimeout(resolve, 10000));
    mediaRecorder.stop();

    // Wait until recording is stopped
    await new Promise(resolve => {
      mediaRecorder.onstop = resolve;
    });

    // Create a Blob from the recorded audio chunks
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    return audioBlob;
  }

  return (
    <div>
      <button
        className="bg-blue-500 text-white p-2 rounded m-4"
        onClick={handleVoiceInput}
      >
        Start Voice Command
      </button>
      {generatedText && (
        <div className="p-4">
          <h2 className="text-xl font-semibold">Generated Text:</h2>
          <p>{generatedText}</p>
          {audioUrl && (
            <div className="mt-4">
              <h2 className="text-xl font-semibold">Generated Audio:</h2>
              <audio controls>
                <source src={audioUrl} type="audio/mp3" />
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Main App component
function App() {
  return (
    <Router>
      <div className="App">
        <h1 className="text-center text-2xl font-bold">Voice Navigation App</h1>
        <Routes>
          <Route path="/wheat" element={<Wheat />} />
          <Route path="/jowar" element={<Jowar />} />
          <Route path="/bajra" element={<Bajra />} />
        </Routes>
        <VoiceButton /> {/* Render the button component for handling voice commands */}
      </div>
    </Router>
  );
}

export default App;
