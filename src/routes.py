from fastapi import APIRouter, HTTPException
import logging
import os
from datetime import datetime

from src.services import chatbot_service
from .models import (
    RequestData, ExplanationRequest, ChatbotRequest, GeneralChatbotRequest,
    TranscriptionRequest, SlideEnhancementRequest, EnhancementResponse,
    BulkEnhancementRequest, EnhancementComparison
)
from .services.storage_service import StorageService
from .services.mcq_service import MCQService
from .services.ppt_explanation import PPTExplanationService 
from .services.chatbot_service import ChatbotService
from .services.general_chatbot_service import GeneralChatbotService
from .services.transcription_service import TranscriptionService
from .services.slide_enhancement_service import SlideEnhancementService
from .services.bulk_enhancement_service import BulkEnhancementService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()
storage_service = StorageService()
mcq_service = MCQService()
ppt_explanation_service = PPTExplanationService() 
chatbot_service = ChatbotService()
general_chatbot_service = GeneralChatbotService()
transcription_service = TranscriptionService()

# Initialize enhancement services
slide_enhancement_service = SlideEnhancementService()
bulk_enhancement_service = BulkEnhancementService()

@router.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and load balancers.
    """
    try:
        # Basic health check - you can add more sophisticated checks here
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "complyquick-ai",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.get("/")
async def root():
    """
    Root endpoint with service information.
    """
    return {
        "message": "ComplyQuick AI Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate_mcq": "/generate_mcq",
            "generate_explanations": "/generate_explanations",
            "chatbot": "/chatbot",
            "general_chatbot": "/general-chatbot",
            "transcribe_audio": "/transcribe_audio",
            "enhance_slide": "/enhance-slide",
            "enhance_all_slides": "/enhance-all-slides",
            "get_enhancement_suggestions": "/get-enhancement-suggestions",
            "compare_enhancements": "/compare-enhancements"
        }
    }

@router.post("/generate_mcq")
async def generate_mcq(data: RequestData):
    try:
        logger.info(f"Received generate_mcq request for presentation: {data.presentation_url}")
        content = storage_service.extract_content_from_ppt(data.presentation_url)
        mcqs = mcq_service.generate_mcqs(content)
        return {"mcqs": mcqs}
    except Exception as e:
        logger.error(f"Error in generate_mcq: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_explanations")
async def generate_explanations(data: ExplanationRequest):
    """
    Generate explanations for each slide in the PowerPoint presentation.
    """
    try:
        # Log incoming request
        logger.info("Received generate_explanations request:")
        logger.info(f"Presentation URL: {data.presentation_url}")
        logger.info(f"Company Name: {data.company_name}")
        logger.info(f"POCs: {[poc.dict() for poc in data.pocs]}")

        # Process the PPT to generate explanations
        logger.info("Generating explanations...")
        explanations = ppt_explanation_service.process_ppt(
            data.presentation_url, 
            data.company_name,
            [poc.dict() for poc in data.pocs]  # Convert POC models to dicts
        )
        logger.info(f"Generated {len(explanations)} explanations")

        # Log response
        logger.info("Sending response...")
        return {"explanations": explanations}
    except Exception as e:
        logger.error(f"Error in generate_explanations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/chatbot")
async def chatbot(data: ChatbotRequest):
    """
    Handle user queries and maintain conversation context.
    """
    try:
        response = chatbot_service.handle_query(data)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/general-chatbot")
async def general_chatbot(data: GeneralChatbotRequest):
    """
    Handle general queries about ComplyQuick and company-specific assigned courses.
    """
    try:
        response = general_chatbot_service.handle_query(data)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe_audio")
async def transcribe_audio(data: TranscriptionRequest):
    """
    Transcribe audio from a URL using Whisper-1 model
    """
    audio_path = None
    try:
        logger.info(f"Received transcription request for URL: {data.audio_url}")
        
        # Extract file extension from URL
        file_extension = os.path.splitext(data.audio_url)[1]
        if not file_extension:
            raise HTTPException(status_code=400, detail="Audio URL must include a file extension")
        
        # Download the audio file
        audio_path = storage_service.download_presentation(
            data.audio_url,
            download_path=f"audio{file_extension}"
        )
        
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Failed to download audio file")
        
        # Transcribe the audio
        transcription = transcription_service.transcribe_audio(audio_path)
        return {"transcription": transcription}
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")
    finally:
        # Clean up temporary files
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.warning(f"Failed to clean up audio file: {str(e)}")

@router.post("/enhance-slide", response_model=EnhancementResponse)
async def enhance_slide(request: SlideEnhancementRequest):
    """Enhance a specific slide's explanation."""
    try:
        logger.info(f"Received enhance-slide request for slide index: {request.query_index}")
        
        # Convert Pydantic models to dictionaries
        explanation_array = [item.model_dump() for item in request.explanation_array]
        
        result = await slide_enhancement_service.enhance_specific_slides(
            explanation_array=explanation_array,
            query_index=request.query_index,
            query_prompt=request.query_prompt
        )
        return EnhancementResponse(explanation_array=result['explanation_array'])
    except Exception as e:
        logger.error(f"Error in enhance-slide: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-all-slides", response_model=EnhancementResponse)
async def enhance_all_slides(request: BulkEnhancementRequest):
    """Enhance all slides' explanations."""
    try:
        logger.info("Received enhance-all-slides request")
        
        # Convert Pydantic models to dictionaries
        explanation_array = [item.model_dump() for item in request.explanation_array]
        
        result = await bulk_enhancement_service.enhance_all_slides(
            explanation_array=explanation_array,
            query_prompt=request.query_prompt,
            batch_size=request.batch_size
        )
        return EnhancementResponse(explanation_array=result['explanation_array'])
    except Exception as e:
        logger.error(f"Error in enhance-all-slides: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-enhancement-suggestions")
async def get_enhancement_suggestions(data: SlideEnhancementRequest):
    """
    Get suggestions for enhancing a specific slide.
    """
    try:
        logger.info(f"Received get-enhancement-suggestions request for slide index: {data.query_index}")
        
        suggestions = await slide_enhancement_service.get_enhancement_suggestions(
            explanation_array=data.explanation_array,
            query_index=data.query_index
        )
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error in get-enhancement-suggestions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-enhancements", response_model=EnhancementComparison)
async def compare_enhancements(data: SlideEnhancementRequest):
    """
    Compare original and enhanced explanations for a slide.
    """
    try:
        logger.info(f"Received compare-enhancements request for slide index: {data.query_index}")
        
        original = data.explanation_array[data.query_index]['explanation']
        enhanced = await slide_enhancement_service.enhance_specific_slides(
            explanation_array=data.explanation_array,
            query_index=data.query_index,
            query_prompt=data.query_prompt
        )
        
        comparison = await slide_enhancement_service.compare_enhancements(
            original_explanation=original,
            enhanced_explanation=enhanced['explanation_array'][data.query_index]['explanation']
        )
        
        return EnhancementComparison(
            **comparison['comparison'],
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in compare-enhancements: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

