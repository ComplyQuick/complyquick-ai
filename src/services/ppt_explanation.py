# src/services/ppt_explanation.py
from pptx import Presentation
from .base_openai_service import BaseOpenAIService
from ..models import SlideExplanation

class PPTExplanationService(BaseOpenAIService):
    def extract_slide_content(self, ppt_path: str):
        """
        Extract text content from each slide in the PowerPoint presentation.
        """
        presentation = Presentation(ppt_path)
        slides_content = []

        for slide in presentation.slides:
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            slides_content.append(" ".join(slide_text))

        return slides_content

    def generate_explanations(self, slides_content: list, company_name: str):
        """
        Generate explanations for each slide using the OpenAI API.
        """
        explanations = []
        for slide_text in slides_content:
            prompt = (
                f"You are presenting a compliance training for {company_name}. "
                "Create a detailed and engaging explanation of this slide content in a presentation style. "
                "Include key points, examples, and any relevant context to make it informative and engaging. "
                "Keep it concise but ensure it covers the main ideas thoroughly.\n\n"
                f"Slide content:\n{slide_text}"
            )
            try:
                explanation = self._make_openai_request(prompt)
                explanations.append(explanation)
            except Exception as e:
                explanations.append(f"Error generating explanation: {str(e)}")

        return explanations

    def process_ppt(self, ppt_path: str, company_name: str) -> list:
        """
        Process the PPT to extract content and generate explanations for each slide.
        """
        slides_content = self.extract_slide_content(ppt_path)
        explanations = self.generate_explanations(slides_content, company_name)
        return [
            SlideExplanation(
                slide=i + 1,
                content=slides_content[i],
                explanation=explanations[i]
            )
            for i in range(len(slides_content))
        ]