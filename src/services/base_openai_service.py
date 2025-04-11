from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class BaseOpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=self.api_key)

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4  # Rough estimate

    def _make_openai_request(self, prompt: str) -> str:
        prompt_tokens = self._estimate_tokens(prompt)
        max_response_tokens = 4096 - prompt_tokens

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_response_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
