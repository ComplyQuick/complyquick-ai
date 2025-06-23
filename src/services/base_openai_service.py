from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import random
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class BaseOpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.max_retries = 3
        self.base_delay = 1  # Base delay in seconds

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of tokens in text."""
        return len(text) // 4  # Rough estimate

    def _make_openai_request(self, prompt: str) -> str:
        """Make a request to OpenAI API with retry logic."""
        last_exception = None
        
        # Log the request details
        prompt_tokens = self._estimate_tokens(prompt)
        logger.info(f"Making OpenAI request with {prompt_tokens} estimated tokens")
        
        for attempt in range(self.max_retries):
            try:
                # Calculate max tokens for response (4096 is max for GPT-4)
                max_response_tokens = max(1000, 4096 - prompt_tokens)
                
                logger.info(f"Attempt {attempt + 1}/{self.max_retries} with max_response_tokens={max_response_tokens}")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Using latest GPT-4 model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_response_tokens,
                    temperature=0.7
                )
                
                # Log successful response
                response_tokens = len(response.choices[0].message.content.split())
                logger.info(f"Request successful. Response tokens: {response_tokens}")
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < self.max_retries - 1:  # Don't sleep on the last attempt
                    # Calculate delay with exponential backoff and jitter
                    delay = (self.base_delay * (2 ** attempt)) + (random.random() * 0.1)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                
        # If we've exhausted all retries, raise the last exception
        error_msg = f"Error code: {getattr(last_exception, 'status_code', 500)} - {str(last_exception)}"
        logger.error(f"All retries failed. Final error: {error_msg}")
        raise Exception(error_msg)
