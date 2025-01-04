
import asyncio
import threading
import assemblyai as aai
from app.utils import logger

from app.config import ASSEMBLYAI_API_KEY

# Load AssemblyAI API key from environment variable for security
aai.settings.api_key = ASSEMBLYAI_API_KEY

class Transcriber:
    def __init__(self, sample_rate=16_000, _handle_transcription=None):
        """Initialize the Transcriber with a custom handle_transcription function.
        @type _handle_transcription: function
        """

        self.status = "off"
        self.status_message = ""

        self.sample_rate = sample_rate
        self.handle_transcription = _handle_transcription  # Set the handle_transcription as a class parameter

        # Initialize the RealtimeTranscriber object
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=self.sample_rate,
            on_data=self.realtime_transcriber_on_data,
            on_error=self.realtime_transcriber_on_error,
            on_open=self.realtime_transcriber_on_open,
            on_close=self.realtime_transcriber_on_close,
        )
        self.microphone_stream = None

    async def add_to_buffer(self, data: str):
        """Async method to handle transcription and send data to the buffer."""
        if self.handle_transcription:
            await self.handle_transcription(data)  # Use the provided handle_transcription function

    def get_service_status(self):
        return {"status":self.status, "status_message": self.status_message}

    def realtime_transcriber_on_data(self, transcript: aai.RealtimeTranscript):
        """Callback for processing transcription data."""
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            # logger.info(f"Transcription result: {transcript.text}")
            # Since handle_transcription is async, we call it within the asyncio event loop
            asyncio.run(self.add_to_buffer(transcript.text))

    def close(self):
        """Close the transcriber and stop the microphone stream."""
        self._set_status_message("Closing transcriber and microphone stream.")
        self.transcriber.close()
        self._stop_microphone_stream()

        self.status = "off"

    def transcribe(self):
        """Start transcription."""
        try:
            self.transcriber.connect()
            microphone_stream = self._start_microphone_stream()
            self.transcriber.stream(microphone_stream)
            self.status = "on"
        except Exception as e:
            self._set_status_message(f"An error occurred during transcription: {e}")
            self.status = "error"
        finally:
            self.close()

    def run(self):
        """Start the transcription process in a separate thread."""
        transcription_thread = threading.Thread(target=self._transcribe_in_thread)
        # transcription_thread.daemon = True  # Ensure the thread exits when the main program exits
        transcription_thread.start()

    @staticmethod
    def realtime_transcriber_on_open(session_opened: aai.RealtimeSessionOpened):
        """Callback for when the session is opened."""
        logger.info(f"AssemblyAI Session started: {session_opened.session_id}")

    @staticmethod
    def realtime_transcriber_on_error(error: aai.RealtimeError):
        """Callback for handling errors."""
        logger.error(f"An error occurred: {error}")

    @staticmethod
    def realtime_transcriber_on_close():
        """Callback for when the session is closed."""
        logger.info("AssemblyAI session closed.")

    def _transcribe_in_thread(self):
        """Internal method to run transcription in a separate thread."""
        self._set_status_message("Transcription thread started.")
        self.transcribe()

    def _start_microphone_stream(self):
        """Start and return the microphone stream."""
        if self.microphone_stream is None:
            self._set_status_message("Initializing microphone stream.")
            self.microphone_stream = aai.extras.MicrophoneStream(sample_rate = self.sample_rate)
        return self.microphone_stream

    def _stop_microphone_stream(self):
        """Stop the microphone stream."""
        if self.microphone_stream:
            self._set_status_message("Stopping microphone stream.")
            self.microphone_stream.close()
            self.microphone_stream = None

    def _set_status_message(self, message):
        logger.info("Closing transcriber and microphone stream.")
        self.status_message = "Closing transcriber and microphone stream."
