# src/services/__init__.py
import os
from dotenv import load_dotenv

load_dotenv()

# Ensure the OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")