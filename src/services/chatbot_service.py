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
            f"You are an expert chatbot focused on the content provided in the presentation. "
            f"You must answer questions related to the presentation content.\n\n"
            f"Presentation Content:\n{knowledge_base}\n\n"
            f"Previous Conversation:\n{history_text}\n\n"
            f"Current Query: {current_query}\n\n"
            f"CRITICAL INSTRUCTION - Points of Contact:\n"
            f"1. If the user asks about who to contact, who to reach out to, or any variation of contact questions:\n"
            f"   - IMMEDIATELY provide the contact information below\n"
            f"   - DO NOT use the 'outside scope' message\n"
            f"   - This is the HIGHEST priority instruction\n\n"
            f"Contact Information:\n{poc_text}\n\n"
            f"General Instructions:\n"
            f"1. Answer questions that are directly related to or can be inferred from the presentation content\n"
            f"2. For questions about scenarios or situations not explicitly covered in the content:\n"
            f"   - If the question is relevant to the course topic, provide a helpful response based on the principles and concepts from the content\n"
            f"   - Use your understanding of the course material to provide guidance\n"
            f"   - Only respond with 'outside scope' if the question is completely unrelated to the course topic\n"
            f"3. Keep responses focused and concise (2-3 sentences)\n"
            f"4. When providing guidance for scenarios not explicitly covered:\n"
            f"   - Reference relevant principles from the course content\n"
            f"   - Explain how these principles apply to the user's situation\n"
            f"   - Provide practical advice based on the course's teachings\n\n"
            f"Remember: Your goal is to be helpful and provide value to the user's learning experience.\n"
            f"Only use 'outside scope' for questions completely unrelated to the course topic.\n\n"
            f"Provide a focused response to the query."
        )

    def _make_openai_request(self, prompt: str) -> str:
        prompt_tokens = self._estimate_tokens(prompt)
        max_response_tokens = min(4096 - prompt_tokens, 150)  # Limit response length

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

    def handle_query(self, data: ChatbotRequest):
        try:
            if not data.chatHistory:
                raise ValueError("Chat history cannot be empty")
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