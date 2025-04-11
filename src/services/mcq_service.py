from openai import OpenAI
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

class MCQService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=self.api_key)

    def generate_mcqs(self, content: str):
        """
        Generate MCQs using the OpenAI Chat API based on the provided content.
        """
        prompt = (
            "You are an expert in compliance training. Based on the following content, "
            "generate multiple-choice questions (MCQs) with 4 options each, and indicate the correct answer "
            "using the exact format below for each question:\n\n"
            "Question: [Question text]\n"
            "a) [Option A]\n"
            "b) [Option B]\n"
            "c) [Option C]\n"
            "d) [Option D]\n"
            "Correct Answer: [letter]\n\n"
            f"{content}"
        )

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        raw_text = response.choices[0].message.content.strip()
        return self.parse_mcqs(raw_text)

    def parse_mcqs(self, raw_text: str):
        """
        Parse the raw text from the AI response into the desired MCQ format.
        """
        mcqs = []
        question_blocks = re.split(r"(?:\n\s*)?Question:", raw_text)[1:]

        for block in question_blocks:
            try:
                question_match = re.match(r"(.*?)(?:\n\s*a\))", block, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else "Question not found"

                choices = {}

                a_match = re.search(r"a\)(.*?)(?:\n\s*b\))", block, re.DOTALL)
                if a_match:
                    choices["a"] = a_match.group(1).strip()

                b_match = re.search(r"b\)(.*?)(?:\n\s*c\))", block, re.DOTALL)
                if b_match:
                    choices["b"] = b_match.group(1).strip()

                c_match = re.search(r"c\)(.*?)(?:\n\s*d\))", block, re.DOTALL)
                if c_match:
                    choices["c"] = c_match.group(1).strip()

                d_match = re.search(r"d\)(.*?)(?:\n\s*(?:Correct Answer:|$))", block, re.DOTALL)
                if d_match:
                    choices["d"] = d_match.group(1).strip()

                correct_answer_match = re.search(r"Correct Answer:\s*([a-d])", block, re.IGNORECASE)
                correct_answer = correct_answer_match.group(1).lower() if correct_answer_match else None

                if question_text and len(choices) == 4 and correct_answer:
                    mcqs.append({
                        "question": question_text,
                        "choices": choices,
                        "correctAnswer": correct_answer
                    })
            except Exception as e:
                print(f"Error parsing question block: {e}")
                continue

        return mcqs

    def parse_mcqs_alternative(self, raw_text: str):
        """
        Alternative parsing approach that processes the entire text using one regex pattern.
        """
        mcqs = []

        questions = re.finditer(
            r"Question:\s*(.*?)\s*\n\s*a\)(.*?)\s*\n\s*b\)(.*?)\s*\n\s*c\)(.*?)\s*\n\s*d\)(.*?)\s*\n\s*Correct Answer:\s*([a-d])",
            raw_text, re.DOTALL | re.IGNORECASE
        )

        for match in questions:
            question_text = match.group(1).strip()
            choices = {
                "a": match.group(2).strip(),
                "b": match.group(3).strip(),
                "c": match.group(4).strip(),
                "d": match.group(5).strip()
            }
            correct_answer = match.group(6).lower()

            mcqs.append({
                "question": question_text,
                "choices": choices,
                "correctAnswer": correct_answer
            })

        return mcqs
