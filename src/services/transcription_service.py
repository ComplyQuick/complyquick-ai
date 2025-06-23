from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, max_concurrent_transcriptions: int = 3):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.supported_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']
        self.max_concurrent_transcriptions = max_concurrent_transcriptions
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_transcriptions)

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

    def _transcribe_single_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe a single audio file. This method is designed for concurrent processing.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            Dict containing the file path and transcription result
        """
        try:
            logger.info(f"Starting concurrent transcription of: {audio_file_path}")
            start_time = time.time()
            
            # Validate file format
            if not self._validate_file_format(audio_file_path):
                raise ValueError(f"Unsupported file format: {audio_file_path}")
            
            # Open the audio file
            with open(audio_file_path, "rb") as audio_file:
                # Call the Whisper API
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="vtt"
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Completed transcription of {audio_file_path} in {duration:.2f} seconds")
            
            return {
                'file_path': audio_file_path,
                'transcription': response,
                'duration': duration,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error transcribing {audio_file_path}: {str(e)}", exc_info=True)
            return {
                'file_path': audio_file_path,
                'transcription': None,
                'error': str(e),
                'success': False
            }

    def transcribe_multiple_audio(self, audio_file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio files concurrently for faster processing.
        
        Args:
            audio_file_paths (List[str]): List of paths to audio files
            
        Returns:
            List[Dict]: List of transcription results with file paths and results
        """
        if not audio_file_paths:
            raise ValueError("No audio files provided for transcription")
        
        logger.info(f"Starting concurrent transcription of {len(audio_file_paths)} audio files")
        logger.info(f"Using {self.max_concurrent_transcriptions} concurrent workers")
        
        results = []
        
        # Process audio files concurrently
        with ThreadPoolExecutor(max_workers=self.max_concurrent_transcriptions) as executor:
            # Submit all transcription tasks
            future_to_file = {
                executor.submit(self._transcribe_single_audio, file_path): file_path 
                for file_path in audio_file_paths
            }
            
            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    logger.info(f"Completed {completed_count}/{len(audio_file_paths)} transcriptions")
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Error in concurrent transcription for {file_path}: {str(e)}")
                    results.append({
                        'file_path': file_path,
                        'transcription': None,
                        'error': str(e),
                        'success': False
                    })
                    completed_count += 1
        
        # Sort results to maintain original order
        results.sort(key=lambda x: audio_file_paths.index(x['file_path']))
        
        logger.info(f"Completed concurrent transcription of {len(audio_file_paths)} files")
        return results

    def transcribe_audio_batch(self, audio_file_paths: List[str], batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Transcribe audio files in batches to manage memory and API rate limits.
        
        Args:
            audio_file_paths (List[str]): List of paths to audio files
            batch_size (int): Number of files to process in each batch
            
        Returns:
            List[Dict]: List of transcription results
        """
        if not audio_file_paths:
            raise ValueError("No audio files provided for transcription")
        
        logger.info(f"Starting batch transcription of {len(audio_file_paths)} audio files")
        logger.info(f"Batch size: {batch_size}, Max concurrent workers: {self.max_concurrent_transcriptions}")
        
        all_results = []
        
        # Process files in batches
        for i in range(0, len(audio_file_paths), batch_size):
            batch = audio_file_paths[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(audio_file_paths) + batch_size - 1)//batch_size}")
            
            # Process current batch concurrently
            batch_results = self.transcribe_multiple_audio(batch)
            all_results.extend(batch_results)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(audio_file_paths):
                logger.info("Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        logger.info(f"Completed batch transcription of {len(audio_file_paths)} files")
        return all_results

    def get_transcription_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the transcription results.
        
        Args:
            results (List[Dict]): List of transcription results
            
        Returns:
            Dict: Statistics about the transcription process
        """
        total_files = len(results)
        successful_transcriptions = sum(1 for r in results if r.get('success', False))
        failed_transcriptions = total_files - successful_transcriptions
        
        total_duration = sum(r.get('duration', 0) for r in results if r.get('success', False))
        avg_duration = total_duration / successful_transcriptions if successful_transcriptions > 0 else 0
        
        return {
            'total_files': total_files,
            'successful_transcriptions': successful_transcriptions,
            'failed_transcriptions': failed_transcriptions,
            'success_rate': (successful_transcriptions / total_files) * 100 if total_files > 0 else 0,
            'total_processing_time': total_duration,
            'average_processing_time': avg_duration,
            'concurrent_workers_used': self.max_concurrent_transcriptions
        } 