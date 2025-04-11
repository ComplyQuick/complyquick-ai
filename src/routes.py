from fastapi import APIRouter, HTTPException

from src.services import chatbot_service
from .models import RequestData, ExplanationRequest, ChatbotRequest  # Import models from models.py
from .services.storage_service import StorageService
from .services.mcq_service import MCQService
from .services.ppt_explanation import PPTExplanationService 
from .services.chatbot_service import ChatbotService # Import the new service

router = APIRouter()
storage_service = StorageService()
mcq_service = MCQService()
ppt_explanation_service = PPTExplanationService() 
chatbot_service = ChatbotService()

@router.post("/generate_mcq")
async def generate_mcq(data: RequestData):
    try:
        content = storage_service.extract_content_from_ppt(data.s3_url)
        mcqs = mcq_service.generate_mcqs(content)
        return {"mcqs": mcqs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_explanations")
async def generate_explanations(data: ExplanationRequest):
    """
    Generate explanations for each slide in the PowerPoint presentation.
    """
    try:
        # Download the PPT from the S3 URL
        ppt_path = storage_service.download_ppt_from_s3(data.s3_url)

        # Process the PPT to generate explanations with company name
        explanations = ppt_explanation_service.process_ppt(ppt_path, data.company_name)

        return {"explanations": explanations}
    except Exception as e:
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

