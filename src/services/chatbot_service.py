# src/services/chatbot_service.py
from typing import List
from ..models import ChatbotRequest, ChatMessage
from .base_openai_service import BaseOpenAIService
from .storage_service import StorageService
import logging

logger = logging.getLogger(__name__)

class ChatbotService(BaseOpenAIService):
    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()

    def format_conversation_history(self, chat_history: List[ChatMessage]):
        """
        Format conversation history with better context awareness and structure.
        """
        formatted_history = []
        for i, msg in enumerate(chat_history[:-1]):  # Exclude the current query
            # Add context markers for better understanding
            if i == 0:
                formatted_history.append("=== Conversation Start ===")
            
            # Format the message with role and content
            formatted_msg = f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
            formatted_history.append(formatted_msg)
            
            # Add context about the flow of conversation
            if i < len(chat_history) - 2:  # Don't add after the last message
                formatted_history.append("---")
        
        return "\n".join(formatted_history)

    def format_poc_details(self, pocs: List[dict]):
        print("Received POCs:", pocs)  # Debug log
        contacts = []
        
        for poc in pocs:
            contact_info = f"{poc['role']}: {poc['name']} (Contact: {poc['contact']})"
            contacts.append(contact_info)
        
        formatted_contacts = "Points of Contact:\n" + "\n".join(contacts) if contacts else "No contacts available."
        print("Formatted POC contacts:", formatted_contacts)  # Debug log
        return formatted_contacts

    def generate_prompt(self, chat_history: List[ChatMessage], presentation_url: str, pocs: List[dict]):
        print("Generating prompt with POCs:", pocs)  # Debug log
        history_text = self.format_conversation_history(chat_history)
        poc_text = self.format_poc_details(pocs)
        current_query = chat_history[-1].content if chat_history else ""
        
        knowledge_base = self.storage_service.extract_content_from_ppt(presentation_url)

        return (
            f"You are a friendly and knowledgeable guide helping someone understand the presentation content. "
            f"Think of yourself as a friend explaining concepts to another friend - be warm, conversational, and engaging.\n\n"
            f"Presentation Content:\n{knowledge_base}\n\n"
            f"CONVERSATION CONTEXT:\n"
            f"The following is the conversation history. Use this to understand the context and flow of the discussion:\n"
            f"{history_text}\n\n"
            f"Current Query: {current_query}\n\n"
            f"RESPONSE GUIDELINES:\n"
            f"1. CONVERSATIONAL TONE:\n"
            f"   - Use a warm, friendly tone like you're explaining to a friend\n"
            f"   - Avoid formal or technical language unless necessary\n"
            f"   - Use everyday examples and relatable scenarios\n"
            f"   - Feel free to use casual language while maintaining professionalism\n\n"
            f"2. CONTENT EXPLANATION:\n"
            f"   - Explain concepts in your own words, not just repeating the presentation\n"
            f"   - Use real-world examples that make the content more relatable\n"
            f"   - Break down complex ideas into simpler terms\n"
            f"   - Share examples that help illustrate the points\n\n"
            f"3. EXAMPLE HANDLING:\n"
            f"   - Provide relatable examples that make the content more understandable\n"
            f"   - Use scenarios that people can easily relate to\n"
            f"   - Make examples practical and relevant to everyday situations\n"
            f"   - Keep examples appropriate and professional\n\n"
            f"4. SCOPE AND RELEVANCE (CRITICAL):\n"
            f"   - ONLY answer questions that are directly related to the presentation content\n"
            f"   - Questions about the presentation's main topics are IN SCOPE\n"
            f"   - Questions asking for examples or clarification about presentation topics are IN SCOPE\n"
            f"   - Questions about how to apply the presentation concepts are IN SCOPE\n"
            f"   - Questions completely unrelated to the presentation (math problems, general advice, unrelated topics) are OUT OF SCOPE\n"
            f"   - For OUT OF SCOPE questions, respond with: 'I'm here to help with questions about the presentation content. Could you please ask something related to the topics covered in the presentation?'\n\n"
            f"5. CONTACT INFORMATION (HIGHEST PRIORITY):\n"
            f"   - If the user asks about who to contact or any variation of contact questions:\n"
            f"   - IMMEDIATELY provide ONLY the contact information below\n"
            f"   - DO NOT add any additional information\n\n"
            f"Contact Information:\n{poc_text}\n\n"
            f"6. RESPONSE FORMAT:\n"
            f"   - Keep responses concise but friendly (2-3 sentences)\n"
            f"   - Use a conversational, approachable tone\n"
            f"   - Make explanations feel natural and easy to understand\n"
            f"   - Maintain the friendly context while staying relevant to the presentation\n\n"
            f"Remember: You're a friend helping another friend understand the presentation content.\n"
            f"Be warm, conversational, and make the content relatable through examples and explanations.\n\n"
            f"CRITICAL: Before responding, check if the question is related to the presentation content:\n"
            f"- If the question is about the presentation topics, provide a helpful response\n"
            f"- If the question is completely unrelated (math problems, general life advice, etc.), use the exact response: 'I'm here to help with questions about the presentation content. Could you please ask something related to the topics covered in the presentation?'\n\n"
            f"Provide a friendly, helpful response to the query."
        )

    def _make_openai_request(self, prompt: str) -> str:
        prompt_tokens = self._estimate_tokens(prompt)
        max_response_tokens = min(4096 - prompt_tokens, 150)  

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Provide brief, direct answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_response_tokens,
            temperature=0.7,
            presence_penalty=0.6  # Encourages focused responses
        )
        
        return response.choices[0].message.content.strip()

    def call_openai_api(self, prompt: str):
        return self._make_openai_request(prompt)

    def _is_clearly_unrelated_question(self, question: str) -> bool:
        """
        Check if a question is clearly unrelated to presentation content.
        This helps avoid unnecessary API calls for obvious off-topic questions.
        """
        question_lower = question.lower().strip()
        
        # Common patterns for unrelated questions
        unrelated_patterns = [
            # Math problems
            r'^\d+[\+\-\*\/]\d+',  # e.g., "2+2", "5*3"
            r'what is \d+[\+\-\*\/]\d+',  # e.g., "what is 2+2"
            
            # General life advice
            r'can i (cheat|steal|lie)',
            r'how to (cheat|steal)',
            r'should i (cheat|steal|lie)',
            
            # Weather, time, personal questions
            r'what.*weather',
            r'what.*time',
            r'how old are you',
            r'what.*your name',
        ]
        
        import re
        for pattern in unrelated_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False

    def handle_query(self, data: ChatbotRequest):
        try:
            if not data.chatHistory:
                raise ValueError("Chat history cannot be empty")
            
            current_question = data.chatHistory[-1].content if data.chatHistory else ""
            
            # Quick check for obviously unrelated questions
            if self._is_clearly_unrelated_question(current_question):
                response = "I'm here to help with questions about the presentation content. Could you please ask something related to the topics covered in the presentation?"
            else:
                prompt = self.generate_prompt(
                    data.chatHistory,
                    data.presentation_url,
                    [poc.dict() for poc in data.pocs]  # Convert POC models to dicts
                )
                response = self._make_openai_request(prompt)
            
            # Create updated chat history with the new response
            updated_chat_history = data.chatHistory + [
                ChatMessage(role="assistant", content=response)
            ]
            
            return {
                "response": response,
                "chatHistory": updated_chat_history
            }

        except Exception as e:
            logger.error(f"Error in handle_query: {str(e)}")
            raise Exception(f"Failed to process query: {str(e)}")