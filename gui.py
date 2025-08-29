import sys
import threading
import speech_recognition as sr
import pyttsx3
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, QObject

from main import get_weather_response

class VoiceWorker(QObject):
    """
    A worker that handles continuous recording and subsequent processing.
    It runs in a separate thread and communicates with the GUI via signals.
    """
    message = Signal(str, str)
    finished = Signal()

    def __init__(self, recognizer, microphone):
        super().__init__()
        self.recognizer = recognizer
        self.microphone = microphone
        self._is_recording = False
        self.audio_frames = []

    def run_recording(self):
        """
        This method is the entry point for the worker's thread.
        It records audio until stop() is called, then processes the audio.
        """
        self._is_recording = True
        self.audio_frames = []

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record in a loop until stop() is called
            while self._is_recording:
                try:
                    buffer = source.stream.read(source.CHUNK)
                    if buffer:
                        self.audio_frames.append(buffer)
                except IOError:
                    break
        
        # Recording has stopped, now process the collected audio
        if not self.audio_frames:
            self.message.emit("Bot: No audio was recorded. Please try again.", "System")
            self.finished.emit()
            return
        
        frame_data = b''.join(self.audio_frames)
        audio_data = sr.AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

        try:
            self.message.emit("Bot: Processing...", "System")
            question = self.recognizer.recognize_google(audio_data)
            self.message.emit(f"You: {question}", "User")

            response = get_weather_response(question)
            self.message.emit(f"Bot: {response}", "Bot")
        except sr.UnknownValueError:
            self.message.emit("Bot: Sorry, I could not understand the audio.", "Bot")
        except sr.RequestError as e:
            self.message.emit(f"Bot: Could not request results; {e}", "Bot")
        finally:
            self.finished.emit()

    def stop(self):
        """Signals the recording loop to stop."""
        self._is_recording = False

class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather AI Assistant")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.layout.addWidget(self.chat_area)

        self.record_button = QPushButton("Press to Talk")
        self.record_button.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.record_button)

        self.is_recording = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.tts_engine = pyttsx3.init()

        # Setup the worker and thread
        self.worker_thread = None
        self.worker = VoiceWorker(self.recognizer, self.microphone)
        self.worker.message.connect(self.add_message)
        self.worker.finished.connect(self.on_worker_finished)

        self.add_message("Bot: Hello! Press the button to start recording your question.")

    def add_message(self, message, sender="Bot"):
        self.chat_area.append(message)
        if sender != "User": # Add spacing after non-user messages
             self.chat_area.append("")

        if sender == "Bot":
            threading.Thread(target=self.speak, args=(message,), daemon=True).start()

    def speak(self, text):
        if text.startswith("Bot: "):
            text = text[5:]
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def toggle_recording(self):
        if not self.is_recording:
            # --- Start Recording ---
            self.is_recording = True
            self.record_button.setText("Stop Recording")
            self.add_message("Bot: Listening...", "System")
            
            # Start the worker in a new thread
            self.worker_thread = threading.Thread(target=self.worker.run_recording, daemon=True)
            self.worker_thread.start()
        else:
            # --- Stop Recording ---
            self.record_button.setText("Processing...")
            self.record_button.setEnabled(False)
            self.worker.stop()

    def on_worker_finished(self):
        """Slot to handle the worker's finished signal."""
        self.is_recording = False
        self.record_button.setText("Press to Talk")
        self.record_button.setEnabled(True)
        self.worker_thread = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())
