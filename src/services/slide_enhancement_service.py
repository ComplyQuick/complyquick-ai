from typing import List, Dict, Any, Optional
from .base_openai_service import BaseOpenAIService
import logging

class SlideEnhancementService(BaseOpenAIService):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def _clean_explanation(self, explanation: str) -> str:
        """Remove 'Explanation:' prefix if present."""
        return explanation.replace("Explanation:", "").strip()

    def _validate_input(self, explanation_array: List[Dict[str, Any]], query_index: int) -> None:
        """Validate input parameters."""
        if not explanation_array:
            raise ValueError("Explanation array cannot be empty")
        if not isinstance(explanation_array, list):
            raise TypeError("Explanation array must be a list")
        if not all(isinstance(item, dict) for item in explanation_array):
            raise TypeError("All items in explanation array must be dictionaries")
        if not all('slide' in item and 'content' in item and 'explanation' in item for item in explanation_array):
            raise ValueError("Each item must contain 'slide', 'content', and 'explanation' keys")
        if not isinstance(query_index, int):
            raise TypeError("Query index must be an integer")
        if query_index < 0 or query_index >= len(explanation_array):
            raise ValueError(f"Query index must be between 0 and {len(explanation_array) - 1}")

    async def enhance_specific_slides(
        self,
        explanation_array: List[Dict[str, Any]],
        query_index: int,
        query_prompt: str
    ) -> Dict[str, Any]:
        """
        Enhance specific slides based on query index and prompt, considering the full context.
        
        Args:
            explanation_array: List of dictionaries containing slide, content, and explanation
            query_index: Index of the slide to enhance
            query_prompt: Prompt describing what changes need to be made
            
        Returns:
            Dictionary containing the updated explanation array
        """
        try:
            self._validate_input(explanation_array, query_index)
            
            # Clean explanations before creating context
            cleaned_array = [
                {
                    **item,
                    'explanation': self._clean_explanation(item['explanation'])
                }
                for item in explanation_array
            ]
            
            # Get the full context from all slides
            context = "\n".join([
                f"Slide {item['slide']}: {item['content']}\nExplanation: {item['explanation']}"
                for item in cleaned_array
            ])

            # Create the prompt for enhancement
            enhancement_prompt = f"""
            You are an expert at enhancing slide explanations. Given the following slides and their explanations:

            {context}

            Please enhance ONLY the explanation for slide {explanation_array[query_index]['slide']} based on this request:
            {query_prompt}

            Important guidelines:
            1. Consider the full context of all slides while making the enhancement
            2. Maintain consistency with the overall presentation
            3. Ensure the enhanced explanation flows naturally with other slides
            4. Return only the enhanced explanation for the specified slide
            5. Do not modify any other slides' explanations
            6. Do not include any prefixes like 'Explanation:' in your response
            """

            # Get enhanced explanation from OpenAI
            enhanced_explanation = self._make_openai_request(enhancement_prompt)

            # Create a copy of the explanation array to avoid modifying the original
            updated_array = explanation_array.copy()
            updated_array[query_index] = {
                **updated_array[query_index],
                'explanation': self._clean_explanation(enhanced_explanation)
            }

            return {
                'explanation_array': updated_array
            }

        except Exception as e:
            self.logger.error(f"Error in enhance_specific_slides: {str(e)}")
            raise

    async def get_enhancement_suggestions(
        self,
        explanation_array: List[Dict[str, Any]],
        query_index: int
    ) -> List[str]:
        """
        Get suggestions for possible enhancements for a specific slide.
        
        Args:
            explanation_array: List of dictionaries containing slide, content, and explanation
            query_index: Index of the slide to get suggestions for
            
        Returns:
            List of enhancement suggestions
        """
        try:
            self._validate_input(explanation_array, query_index)
            
            # Clean explanations before creating context
            cleaned_array = [
                {
                    **item,
                    'explanation': self._clean_explanation(item['explanation'])
                }
                for item in explanation_array
            ]
            
            # Get the full context
            context = "\n".join([
                f"Slide {item['slide']}: {item['content']}\nExplanation: {item['explanation']}"
                for item in cleaned_array
            ])
            
            prompt = f"""
            Given the following slides and their explanations:

            {context}

            Suggest 3-5 different ways the explanation for slide {explanation_array[query_index]['slide']} could be enhanced.
            Consider the full context of all slides while making suggestions.
            Return only the suggestions as a bulleted list.
            Do not include any prefixes like 'Explanation:' in your suggestions.
            """

            suggestions = self._make_openai_request(prompt)
            return [s.strip('- ') for s in suggestions.strip().split('\n') if s.strip()]

        except Exception as e:
            self.logger.error(f"Error in get_enhancement_suggestions: {str(e)}")
            raise

    async def compare_enhancements(
        self,
        original_explanation: str,
        enhanced_explanation: str
    ) -> Dict[str, Any]:
        """
        Compare original and enhanced explanations to highlight changes.
        
        Args:
            original_explanation: The original explanation
            enhanced_explanation: The enhanced explanation
            
        Returns:
            Dictionary containing comparison metrics and analysis
        """
        try:
            # Clean explanations before comparison
            original = self._clean_explanation(original_explanation)
            enhanced = self._clean_explanation(enhanced_explanation)
            
            prompt = f"""
            Compare these two explanations and provide analysis:
            
            Original:
            {original}
            
            Enhanced:
            {enhanced}
            
            Provide:
            1. Key changes made
            2. Improvement areas
            3. Quality assessment
            Format as JSON with these keys: changes, improvements, assessment
            """

            comparison = self._make_openai_request(prompt)
            return {
                'comparison': comparison
            }

        except Exception as e:
            self.logger.error(f"Error in compare_enhancements: {str(e)}")
            raise 