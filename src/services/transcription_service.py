from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import mimetypes

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.supported_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']

    def _validate_file_format(self, file_path: str) -> bool:
        """Validate if the file format is supported by Whisper."""
        # Get file extension
        _, ext = os.path.splitext(file_path)
        if not ext:
            return False
        
        # Remove the dot from extension and convert to lowercase
        format_type = ext[1:].lower()
        
        # Special case for mp3/mpeg
        if format_type in ['mp3', 'mpeg']:
            return True
            
        return format_type in self.supported_formats

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file using OpenAI's Whisper-1 model and return VTT format.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcription in VTT format
        """
        try:
            logger.info(f"Starting transcription of audio file: {audio_file_path}")
            
            # Validate file format
            if not self._validate_file_format(audio_file_path):
                raise ValueError(f"Unsupported file format. Supported formats are: {', '.join(self.supported_formats)}")
            
            # Open the audio file
            with open(audio_file_path, "rb") as audio_file:
                # Call the Whisper API
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="vtt"
                )
            
            logger.info("Transcription completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            raise Exception(f"Failed to transcribe audio: {str(e)}") 