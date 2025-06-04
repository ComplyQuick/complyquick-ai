# src/services/ppt_explanation.py
from pptx import Presentation
from .base_openai_service import BaseOpenAIService
from .storage_service import StorageService
from ..models import SlideExplanation
import logging
import os

logger = logging.getLogger(__name__)

class PPTExplanationService(BaseOpenAIService):
    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()

    def extract_slide_content(self, ppt_path: str):
        """
        Extract text content from each slide in the PowerPoint presentation.
        """
        logger.info(f"Extracting content from PPT: {ppt_path}")
        presentation = Presentation(ppt_path)
        slides_content = []

        for slide_number, slide in enumerate(presentation.slides, 1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            content = " ".join(slide_text)
            slides_content.append(content)
            logger.debug(f"Extracted content from slide {slide_number}: {content[:100]}...")

        logger.info(f"Extracted content from {len(slides_content)} slides")
        return slides_content

    

    def _create_prompt(self, index: int, total_slides: int, slide_text: str, company_name: str, pocs: list, relevant_contacts: dict) -> str:
        """
        Create the appropriate prompt based on slide position and content.
        """
        # Create role introductions and personalized examples
        role_introductions = []
        personalized_examples = []
        
        for poc in pocs:
            role_lower = poc['role'].lower()
            # First introduce the person with their role
            role_introductions.append(f"{poc['name']} as {poc['role']}")
            
            # Then create examples using just their name
            if 'ceo' in role_lower:
                personalized_examples.append(f"{poc['name']} leads with a vision for excellence")
            elif 'cto' in role_lower:
                personalized_examples.append(f"{poc['name']} drives technological innovation")
            elif 'hr' in role_lower:
                personalized_examples.append(f"{poc['name']} ensures a supportive and inclusive workplace")
            elif 'risk' in role_lower:
                personalized_examples.append(f"{poc['name']} maintains our security framework")
            elif 'legal' in role_lower:
                personalized_examples.append(f"{poc['name']} upholds compliance standards")
            else:
                personalized_examples.append(f"{poc['name']} contributes to our company's success")

        # Create a personalized leadership section that introduces roles once
        leadership_section = "Our leadership team includes " + ", ".join(role_introductions) + ". " + ", ".join(personalized_examples) + "."

        if index == 0:
            # First slide
            prompt = (
                f"Create a warm, engaging introduction for {company_name}'s training presentation. "
                f"The explanation should be natural and suitable for text-to-speech narration. "
                f"Make it friendly and professional, about 4-5 sentences long. "
                f"Don't use time-specific greetings like 'good morning/evening'. "
                f"Focus on welcoming the audience and introducing the topic. "
                f"{leadership_section} "
                f"Emphasize the company's commitment to the topic.\n\n"
                f"Slide content:\n{slide_text}"
            )
        elif index == total_slides - 1:
            # Last slide
            prompt = (
                f"Create a friendly conclusion for {company_name}'s training presentation. "
                f"The explanation should be natural for text-to-speech narration. "
                f"Keep it warm and professional, about 3-4 sentences. "
                f"Thank the audience and emphasize the importance of the training material. "
                f"{leadership_section} "
                f"Don't use phrases like 'thank you for your time today'.\n\n"
                f"Slide content:\n{slide_text}"
            )
        else:
            # Regular slides
            # Determine the appropriate tone based on content
            tone_instruction = ""
            
            if any(keyword in slide_text.lower() for keyword in ['harassment', 'posh', 'sexual harassment']):
                tone_instruction = (
                    "Use a professional and supportive tone. "
                    "Emphasize the company's commitment to a safe and respectful workplace. "
                )
            elif any(keyword in slide_text.lower() for keyword in ['security', 'compliance', 'data protection']):
                tone_instruction = (
                    "Use a professional and authoritative tone. "
                    "Reference our commitment to protecting company assets. "
                )
            elif any(keyword in slide_text.lower() for keyword in ['benefits', 'leave', 'policy', 'employee']):
                tone_instruction = (
                    "Use a warm and informative tone. "
                    "Emphasize the company's commitment to employee well-being. "
                )
            elif any(keyword in slide_text.lower() for keyword in ['training', 'development', 'learning']):
                tone_instruction = (
                    "Use an encouraging and motivational tone. "
                    "Emphasize the company's investment in employee growth. "
                )
            
            prompt = (
                f"Create an engaging explanation of this slide for {company_name}'s training. "
                f"The explanation should be natural and suitable for text-to-speech narration. "
                f"Make it comprehensive but clear, about 5-6 sentences long. "
                f"Use a conversational tone while maintaining professionalism. "
                f"Break down complex concepts into clear explanations. "
                f"{tone_instruction}"
                f"{leadership_section} "
                f"Include relevant examples or scenarios that reflect {company_name}'s work environment. "
                f"Avoid using bullet points or lists - structure the content in flowing paragraphs. "
                f"Don't use transition phrases like 'moving on' or 'in this slide'.\n\n"
                f"Slide content:\n{slide_text}"
            )
        
        return prompt

    def generate_explanations(self, slides_content: list, company_name: str, pocs: list):
        """
        Generate explanations for each slide using the OpenAI API.
        """
        logger.info(f"Generating explanations for {len(slides_content)} slides")
        logger.info(f"Company name: {company_name}")
        
        explanations = []
        total_slides = len(slides_content)
        
        for index, slide_text in enumerate(slides_content):
            logger.info(f"Processing slide {index + 1}/{total_slides}")
            try:
                prompt = self._create_prompt(index, total_slides, slide_text, company_name, pocs, {})
                
                explanation = self._make_openai_request(prompt)
                cleaned_explanation = (explanation
                    .replace("•", "")
                    .replace("-", "")
                    .replace("...", ".")
                    .replace("\n\n", " ")
                    .strip())
                explanations.append(cleaned_explanation)
                
                logger.debug(f"Generated explanation for slide {index + 1}: {cleaned_explanation[:200]}...")
            except Exception as e:
                logger.error(f"Error processing slide {index + 1}: {str(e)}", exc_info=True)
                explanations.append(f"Error generating explanation: {str(e)}")

        logger.info(f"Completed generating {len(explanations)} explanations")
        return explanations

    def process_ppt(self, presentation_url: str, company_name: str, pocs: list) -> list:
        """
        Process the PPT to extract content and generate explanations for each slide.
        """
        logger.info(f"Starting PPT processing for {company_name}")
        try:
            # Use storage_service to download and get the file path
            ppt_path = self.storage_service.download_presentation(presentation_url)
            slides_content = self.extract_slide_content(ppt_path)
            explanations = self.generate_explanations(slides_content, company_name, pocs)
            
            result = []
            for i in range(len(slides_content)):
                # Generate a concise gist for the content
                gist_prompt = (
                    f"Create a concise title or gist for the following slide content. "
                    f"Focus on the main topic or key message. Be brief and direct, but ensure it captures the complete topic:\n\n"
                    f"{slides_content[i]}"
                )
                gist = self._make_openai_request(gist_prompt)
                cleaned_gist = gist.strip().replace('"', '').replace("'", '')
                
                # If the gist is too long, try to make it more concise
                if len(cleaned_gist.split()) > 8:
                    gist_prompt = (
                        f"Create a very concise title (4-6 words) for the following slide content. "
                        f"Focus on the main topic only:\n\n"
                    f"{slides_content[i]}"
                )
                gist = self._make_openai_request(gist_prompt)
                cleaned_gist = gist.strip().replace('"', '').replace("'", '')
                
                result.append(
                    SlideExplanation(
                        slide=i + 1,
                        content=cleaned_gist,
                        explanation=explanations[i]
                    )
                )
            
            # Clean up the downloaded file
            try:
                os.remove(ppt_path)
            except:
                pass  # Ignore if file couldn't be deleted
            
            logger.info(f"Successfully processed PPT with {len(result)} slides")
            return result
        except Exception as e:
            logger.error("Error in process_ppt", exc_info=True)
            raise