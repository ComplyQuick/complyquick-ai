# src/services/__init__.py
import os
from dotenv import load_dotenv
from .slide_enhancement_service import SlideEnhancementService
from .bulk_enhancement_service import BulkEnhancementService

load_dotenv()

# Ensure the OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

__all__ = [
    'SlideEnhancementService',
    'BulkEnhancementService'
]