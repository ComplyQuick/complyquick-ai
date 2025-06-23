from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

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
    """Model for data requests"""
    presentation_url: str = Field(
        ...,
        description="URL to the presentation (supports both Google Drive and S3 URLs)"
    )

class TenantDetails(BaseModel):
    """Model for tenant contact details"""
    hrContactName: Optional[str] = None
    hrContactEmail: Optional[str] = None
    hrContactPhone: Optional[str] = None
    ceoName: Optional[str] = None
    ceoEmail: Optional[str] = None
    ceoContact: Optional[str] = None
    ctoName: Optional[str] = None
    ctoEmail: Optional[str] = None
    ctoContact: Optional[str] = None

class POC(BaseModel):
    """Model for Point of Contact"""
    role: str
    name: str
    contact: str

class ExplanationRequest(BaseModel):
    """Model for explanation generation requests"""
    presentation_url: str  # Changed from s3_url to be more generic
    company_name: str
    pocs: List[POC]  # List of Points of Contact instead of tenant_details

class SlideExplanation(BaseModel):
    """Model for slide explanations"""
    slide: int
    content: str
    explanation: str

class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str  # "user" or "assistant"
    content: str

class CourseInfo(BaseModel):
    """Model for course information"""
    name: str
    description: str

class ChatbotRequest(BaseModel):
    """Model for chatbot requests"""
    chatHistory: List[ChatMessage]
    presentation_url: str  # Changed from s3_url to presentation_url
    pocs: List[POC]  # List of Points of Contact instead of emergency_details

class GeneralChatbotRequest(BaseModel):
    """Model for general chatbot requests"""
    chatHistory: List[ChatMessage]
    company_name: str
    tenant_details: TenantDetails
    assigned_courses: List[CourseInfo]

class TranscriptionRequest(BaseModel):
    """Model for audio transcription requests"""
    audio_url: str  # URL to the audio file

class SlideEnhancementRequest(BaseModel):
    """Model for slide enhancement requests"""
    explanation_array: List[SlideExplanation]
    query_index: int
    query_prompt: Optional[str] = None

class EnhancementResponse(BaseModel):
    """Model for enhancement responses"""
    explanation_array: List[SlideExplanation]

class BulkEnhancementRequest(BaseModel):
    """Model for bulk enhancement requests"""
    explanation_array: List[SlideExplanation]
    query_prompt: str
    batch_size: int = 5

class EnhancementComparison(BaseModel):
    """Model for enhancement comparisons"""
    original_length: int
    enhanced_length: int
    similarity_score: float
    key_differences: List[str]
    timestamp: datetime
