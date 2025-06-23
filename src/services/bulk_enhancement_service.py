from typing import List, Dict, Any, Optional, Tuple
from .base_openai_service import BaseOpenAIService
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BulkEnhancementService(BaseOpenAIService):
    def __init__(self, max_concurrent_requests: int = 3):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.max_concurrent_requests = max_concurrent_requests
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_requests)

    def _validate_input(self, explanation_array: List[Dict[str, Any]], batch_size: int) -> None:
        """Validate input parameters."""
        if not explanation_array:
            raise ValueError("Explanation array cannot be empty")
        if not isinstance(explanation_array, list):
            raise TypeError("Explanation array must be a list")
        if not all(isinstance(item, dict) for item in explanation_array):
            raise TypeError("All items in explanation array must be dictionaries")
        if not all('slide' in item and 'content' in item and 'explanation' in item for item in explanation_array):
            raise ValueError("Each item must contain 'slide', 'content', and 'explanation' keys")
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("Batch size must be a positive integer")

    async def enhance_all_slides(
        self,
        explanation_array: List[Dict[str, Any]],
        query_prompt: str,
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Enhance all slides' explanations based on the query prompt.
        
        Args:
            explanation_array: List of dictionaries containing slide, content, and explanation
            query_prompt: Prompt describing what changes need to be made
            batch_size: Number of slides to process in each batch
            
        Returns:
            Dictionary containing the updated explanation array
        """
        try:
            self._validate_input(explanation_array, batch_size)
            
            # Get the full context from all slides
            context = "\n".join([
                f"Slide {item['slide']}: {item['content']}\nExplanation: {item['explanation']}"
                for item in explanation_array
            ])

            # Process slides in batches
            updated_array = explanation_array.copy()
            for i in range(0, len(explanation_array), batch_size):
                batch = explanation_array[i:i + batch_size]
                
                # Create the prompt for enhancement
                enhancement_prompt = f"""
                You are an expert at enhancing slide explanations. Given the following slides and their explanations:

                {context}

                Please enhance the explanations for the following slides based on this request:
                {query_prompt}

                Slides to enhance:
                {[f"Slide {item['slide']}: {item['content']}" for item in batch]}

                CRITICAL INSTRUCTIONS:
                1. Consider the full context of all slides while making the enhancements
                2. Maintain consistency with the overall presentation
                3. Ensure the enhanced explanations flow naturally with other slides
                4. You MUST return exactly {len(batch)} enhanced explanations, no more, no less
                5. Each explanation should be separated by exactly two newlines (\\n\\n)
                6. Do not include any prefixes like 'Explanation:', 'Slide X:', or numbering
                7. Do not include any additional text, formatting, or commentary
                8. Start directly with the first enhanced explanation
                9. End with the last enhanced explanation
                10. Do not add any summary, conclusion, or additional text after the explanations
                11. REPLACE AND ENHANCE: Create completely new explanations that convey all the original information but with improved delivery
                12. PRESERVE ALL INFORMATION: Ensure every fact, detail, number, and point from the original explanation is included
                13. IMPROVE DELIVERY: Use the enhancement request to make the explanation more engaging, clear, or appropriate for the target audience
                14. NATURAL FLOW: Make the explanation feel conversational and interesting while maintaining all original content
                15. AVOID REDUNDANCY: Do not repeat the original explanation - create a fresh, enhanced version that covers everything

                Expected format:
                [First enhanced explanation that replaces the original with better delivery]

                [Second enhanced explanation that replaces the original with better delivery]

                [Third enhanced explanation that replaces the original with better delivery]
                (and so on for exactly {len(batch)} explanations)
                """

                # Get enhanced explanations from OpenAI
                enhanced_explanation = self._make_openai_request(enhancement_prompt)
                
                # Clean and split the response
                explanations = self._parse_enhanced_explanations(enhanced_explanation, len(batch))
                
                # Handle cases where we get more or fewer explanations than expected
                if len(explanations) != len(batch):
                    self.logger.warning(f"Expected {len(batch)} explanations but got {len(explanations)}")
                    self.logger.debug(f"Raw response: {enhanced_explanation}")
                    
                    if len(explanations) > len(batch):
                        # Take only the first N explanations
                        explanations = explanations[:len(batch)]
                        self.logger.info(f"Truncated response to {len(batch)} explanations")
                    elif len(explanations) < len(batch):
                        # Pad with original explanations
                        while len(explanations) < len(batch):
                            explanations.append(batch[len(explanations)]['explanation'])
                        self.logger.info(f"Padded response with original explanations to reach {len(batch)} explanations")
                    
                    # Final validation
                    if len(explanations) != len(batch):
                        self.logger.error(f"Failed to normalize explanations count. Expected: {len(batch)}, Got: {len(explanations)}")
                        # Instead of raising an error, use the original explanations
                        self.logger.warning("Using original explanations due to parsing failure")
                        explanations = [item['explanation'] for item in batch]

                # Update the explanations in the array
                for j, item in enumerate(batch):
                    updated_array[i + j] = {
                        **item,
                        'explanation': explanations[j]
                    }

                # Add a small delay between batches to avoid rate limiting
                if i + batch_size < len(explanation_array):
                    await asyncio.sleep(1)

            return {
                'explanation_array': updated_array
            }

        except Exception as e:
            self.logger.error(f"Error in enhance_all_slides: {str(e)}")
            raise

    async def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        query_prompt: str,
        enhancement_type: Optional[str],
        max_tokens: Optional[int],
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Process a batch of slides concurrently."""
        async def process_slide(slide: Dict[str, Any], index: int) -> Dict[str, Any]:
            context = f"Slide {start_index + index + 1}: {slide['content']}\nExplanation: {slide['explanation']}"
            
            prompt = f"""
            Given this slide:
            {context}

            Please enhance the explanation based on this request:
            {query_prompt}

            CRITICAL INSTRUCTIONS:
            1. Create a completely new explanation that replaces the original
            2. Preserve ALL information from the original explanation
            3. Improve the delivery based on the enhancement request
            4. Make it more engaging and natural while keeping all facts intact
            5. Do not add the original explanation on top - create a fresh, enhanced version
            6. Ensure the explanation flows well and is appropriate for the target audience
            """

            if enhancement_type:
                prompt += f"\nEnhancement type: {enhancement_type}"

            enhanced_explanation = await self.get_completion(prompt, max_tokens=max_tokens)
            
            return {
                'explanation': enhanced_explanation,
                'timestamp': datetime.now().isoformat()
            }

        tasks = [process_slide(slide, i) for i, slide in enumerate(batch)]
        return await asyncio.gather(*tasks)

    async def get_enhancement_statistics(
        self,
        original_array: List[Dict[str, Any]],
        enhanced_array: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about the enhancements made.
        
        Args:
            original_array: Original explanation array
            enhanced_array: Enhanced explanation array
            
        Returns:
            Dictionary containing enhancement statistics
        """
        try:
            self._validate_input(original_array, 1)
            self._validate_input(enhanced_array, 1)

            if len(original_array) != len(enhanced_array):
                raise ValueError("Arrays must have the same length")

            prompt = f"""
            Analyze these pairs of explanations and provide statistics:
            
            {self._format_comparison_pairs(original_array, enhanced_array)}
            
            Provide:
            1. Average length change
            2. Key improvement patterns
            3. Quality metrics
            Format as JSON with these keys: length_change, patterns, metrics
            """

            analysis = await self.get_completion(prompt)
            
            return {
                'analysis': analysis,
                'total_slides': len(original_array),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in get_enhancement_statistics: {str(e)}")
            raise

    def _format_comparison_pairs(
        self,
        original_array: List[Dict[str, Any]],
        enhanced_array: List[Dict[str, Any]]
    ) -> str:
        """Format pairs of explanations for comparison."""
        pairs = []
        for i, (orig, enh) in enumerate(zip(original_array, enhanced_array)):
            pairs.append(f"""
            Slide {i + 1}:
            Original: {orig['explanation']}
            Enhanced: {enh['explanation']}
            """)
        return "\n".join(pairs)

    async def rollback_enhancements(
        self,
        enhanced_array: List[Dict[str, Any]],
        backup_array: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rollback enhancements to a previous version.
        
        Args:
            enhanced_array: Current enhanced array
            backup_array: Backup array to rollback to
            
        Returns:
            Rolled back explanation array
        """
        try:
            self._validate_input(enhanced_array, 1)
            self._validate_input(backup_array, 1)

            if len(enhanced_array) != len(backup_array):
                raise ValueError("Arrays must have the same length")

            # Create a new array with the backup explanations
            rolled_back = enhanced_array.copy()
            for i, backup in enumerate(backup_array):
                rolled_back[i] = {
                    **rolled_back[i],
                    'explanation': backup['explanation'],
                    'last_rollback': datetime.now().isoformat()
                }

            return rolled_back

        except Exception as e:
            self.logger.error(f"Error in rollback_enhancements: {str(e)}")
            raise

    def _parse_enhanced_explanations(self, response: str, expected_count: int) -> List[str]:
        """
        Parse enhanced explanations from the API response with robust error handling.
        
        Args:
            response: Raw response from the API
            expected_count: Number of explanations expected
            
        Returns:
            List of parsed explanations
        """
        try:
            # First, try to split by double newlines
            explanations = [exp.strip() for exp in response.split('\n\n') if exp.strip()]
            
            # If we got the right number, return them
            if len(explanations) == expected_count:
                return explanations
            
            # If we got more than expected, try to identify the actual explanations
            if len(explanations) > expected_count:
                # Look for patterns that might indicate the start of explanations
                # Remove any introductory text or commentary
                cleaned_explanations = []
                for exp in explanations:
                    # Skip if it looks like commentary or instructions
                    if any(skip_word in exp.lower() for skip_word in [
                        'here are', 'following are', 'below are', 'enhanced explanations',
                        'slide', 'explanation:', 'guidelines', 'instructions'
                    ]):
                        continue
                    cleaned_explanations.append(exp)
                
                # Take the first N valid explanations
                if len(cleaned_explanations) >= expected_count:
                    return cleaned_explanations[:expected_count]
                else:
                    # Fall back to original split
                    return explanations[:expected_count]
            
            # If we got fewer than expected, try alternative parsing
            if len(explanations) < expected_count:
                # Try splitting by single newlines and look for longer text blocks
                lines = response.split('\n')
                potential_explanations = []
                current_explanation = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_explanation:
                            potential_explanations.append(' '.join(current_explanation))
                            current_explanation = []
                    else:
                        # Skip lines that look like instructions or commentary
                        if not any(skip_word in line.lower() for skip_word in [
                            'here are', 'following are', 'below are', 'enhanced explanations',
                            'slide', 'explanation:', 'guidelines', 'instructions'
                        ]):
                            current_explanation.append(line)
                
                # Add the last explanation if there is one
                if current_explanation:
                    potential_explanations.append(' '.join(current_explanation))
                
                if len(potential_explanations) >= expected_count:
                    return potential_explanations[:expected_count]
            
            # If all else fails, return what we have and pad with placeholders
            self.logger.warning(f"Could not parse exactly {expected_count} explanations from response")
            while len(explanations) < expected_count:
                explanations.append(f"[Enhanced explanation {len(explanations) + 1}]")
            
            return explanations[:expected_count]
            
        except Exception as e:
            self.logger.error(f"Error parsing enhanced explanations: {str(e)}")
            # Return placeholder explanations
            return [f"[Enhanced explanation {i + 1}]" for i in range(expected_count)] 