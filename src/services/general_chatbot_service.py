from typing import List, Dict
from .base_openai_service import BaseOpenAIService
from ..models import ChatMessage, CourseInfo, GeneralChatbotRequest, TenantDetails

class GeneralChatbotService(BaseOpenAIService):
    def format_company_info(self, company_name: str, tenant_details: Dict) -> str:
        return (
            f"Company Information:\n"
            f"Company Name: {company_name}\n"
            f"Website: ComplyQuick - A compliance training platform\n"
        )

    def format_assigned_courses(self, courses: List[CourseInfo]) -> str:
        courses_text = "Your Company's Assigned Compliance Training Courses:\n"
        for course in courses:
            courses_text += f"- {course.name}: {course.description}\n"
        return courses_text

    def generate_prompt(self, chat_history: List[ChatMessage], company_name: str, 
                       tenant_details: TenantDetails, assigned_courses: List[CourseInfo]) -> str:
        history_text = "\n".join([
            f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}" 
            for msg in chat_history
        ])
        current_query = chat_history[-1].content if chat_history else ""
        
        # Format company info and courses
        company_info = self.format_company_info(company_name, tenant_details)
        courses_info = self.format_assigned_courses(assigned_courses)
        
        return (
            f"You are ComplyQuick's AI assistant for {company_name}. You have access to the following information:\n\n"
            f"{company_info}\n"
            f"{courses_info}\n\n"
            f"About ComplyQuick Platform:\n"
            f"ComplyQuick is a compliance learning platform designed for organizations to train their employees on critical regulatory and ethical subjects. "
            f"Courses are selected and assigned by the organization's admin.\n\n"
            f"Key Functionalities:\n"
            f"1. Course Selection: Your admin will assign courses based on your role and organizational requirements.\n"
            f"2. Completion Requirements:\n"
            f"   - After completing a course, learners must take a quiz to test their understanding\n"
            f"   - If the quiz is passed, a completion certificate will be generated\n"
            f"   - If the learner does not pass, they will be required to retake the quiz until they achieve a passing score\n\n"
            f"Chatbot Functionality:\n"
            f"There are two chatbots on the platform:\n"
            f"1. General Chatbot (You): Available across the platform to answer broad queries related to:\n"
            f"   - Navigation\n"
            f"   - Account access\n"
            f"   - Certification\n"
            f"   - Timelines\n"
            f"   - General usage\n"
            f"2. Course-Specific Chatbot: Accessible within each course to assist learners with:\n"
            f"   - Course-specific doubts\n"
            f"   - Content clarifications\n\n"
            f"The platform is structured to ensure compliance readiness, clarity in learning, and efficient support through intelligent chatbot interaction.\n\n"
            f"Instructions for responding:\n"
            f"1. When someone asks for contact information, ALWAYS provide the specific email and phone number\n"
            f"2. Be direct and provide the exact contact details requested\n"
            f"3. For technical issues, provide CTO contact information\n"
            f"4. For HR related queries, provide HR contact details\n"
            f"5. Keep responses professional but friendly\n"
            f"6. Include relevant contact information in every response where applicable\n"
            f"7. When asked about courses, refer to the assigned courses list above\n"
            f"8. For course-specific questions, direct users to use the course-specific chatbot\n"
            f"9. For platform-related questions, provide clear and concise information\n\n"
            f"Chat History:\n{history_text}\n\n"
            f"Current Query: {current_query}\n\n"
            f"Provide a helpful response with specific contact details when relevant."
        )

    def handle_query(self, request_data: GeneralChatbotRequest) -> dict:
        try:
            prompt = self.generate_prompt(
                request_data.chatHistory,
                request_data.company_name,
                request_data.tenant_details,
                request_data.assigned_courses
            )
            response = self._make_openai_request(prompt)
            
            # Create updated chat history with the new response
            updated_chat_history = request_data.chatHistory + [
                ChatMessage(role="assistant", content=response)
            ]
            
            return {
                "response": response,
                "chatHistory": updated_chat_history
            }
        except Exception as e:
            raise Exception(f"Failed to process query: {str(e)}") 