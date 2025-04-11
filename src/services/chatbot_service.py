# src/services/chatbot_service.py
from typing import List
from ..models import ChatbotRequest, ChatMessage
from .base_openai_service import BaseOpenAIService
from .storage_service import StorageService

class ChatbotService(BaseOpenAIService):
    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()

    def format_conversation_history(self, chat_history: List[ChatMessage]):
        return "\n".join([
            f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}" 
            for msg in chat_history[:-1]
        ])

    def format_emergency_details(self, emergency_details: dict):
        return (
            f"Presiding Officer: {emergency_details.get('presiding_officer_name')} "
            f"(Email: {emergency_details.get('presiding_officer_email')}). "
            f"POSH Committee Email: {emergency_details.get('posh_committee_email')}. "
            f"HR Contact: {emergency_details.get('hr_contact_name')} "
            f"(Email: {emergency_details.get('hr_contact_email')}, "
            f"Phone: {emergency_details.get('hr_contact_phone')})."
        )

    def generate_prompt(self, chat_history: List[ChatMessage], s3_url: str, emergency_details: dict):
        history_text = self.format_conversation_history(chat_history)
        emergency_text = self.format_emergency_details(emergency_details)
        current_query = chat_history[-1].content if chat_history else ""
        
        knowledge_base = self.storage_service.extract_content_from_ppt(s3_url)

        return (
            f"You are an expert compliance chatbot specializing in POSH (Prevention of Sexual Harassment) policies. "
            f"You have access to detailed training material that includes both presentation content and detailed explanations.\n\n"
            f"Emergency Contact Information:\n{emergency_text}\n\n"
            f"Training Material Content:\n{knowledge_base}\n\n"
            f"Previous Conversation:\n{history_text}\n\n"
            f"Current Query: {current_query}\n\n"
            f"Instructions:\n"
            f"1. Use the detailed training material to provide comprehensive answers\n"
            f"2. If the presentation notes provide specific examples or procedures, include them\n"
            f"3. Always reference emergency contacts when relevant to the query\n"
            f"4. Maintain a professional yet approachable tone\n"
            f"5. If multiple slides cover the topic, combine the information coherently\n"
            f"6. Keep responses concise but informative\n"
            f"7. If the query involves reporting or immediate action, always include relevant contact information\n\n"
            f"Please provide a detailed response to the query."
        )

    def call_openai_api(self, prompt: str):
        return self._make_openai_request(prompt)

    def handle_query(self, data: ChatbotRequest):
        try:
            if not data.chatHistory:
                raise ValueError("Chat history cannot be empty")

            prompt = self.generate_prompt(
                data.chatHistory,
                data.s3_url,
                data.emergency_details
            )

            response = self.call_openai_api(prompt)

            return response

        except Exception as e:
            print(f"Error in handle_query: {str(e)}")
            raise Exception(f"Failed to process query: {str(e)}")