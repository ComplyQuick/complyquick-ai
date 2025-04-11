from typing import List, Optional, Union
from pydantic import BaseModel

# API Request/Response Models
class GeminiPart(BaseModel):
    text: str

class GeminiContent(BaseModel):
    parts: List[GeminiPart]

class GeminiRequest(BaseModel):
    contents: List[GeminiContent]

class GeminiCandidate(BaseModel):
    content: GeminiContent

class GeminiResponse(BaseModel):
    candidates: List[GeminiCandidate]

# Application Models
class RequestData(BaseModel):
    s3_url: str

class ExplanationRequest(BaseModel):
    """Model for explanation generation requests"""
    s3_url: str
    company_name: str

class SlideExplanation(BaseModel):
    """Model for slide explanations"""
    slide: int
    content: str
    explanation: str

class ChatMessage(BaseModel):
    """Model for individual chat messages"""
    role: str  # 'user' or 'assistant'
    content: str

class ChatbotRequest(BaseModel):
    """Model for chatbot requests"""
    chatHistory: List[ChatMessage]
    s3_url: str  # The extracted content from the PPT
    emergency_details: dict  # Emergency contact details

# API Configuration Constants
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_HEADERS = {
    "Content-Type": "application/json"
}
