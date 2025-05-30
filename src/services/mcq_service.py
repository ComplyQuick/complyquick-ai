from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

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
        try:
            logger.info("Starting MCQ generation")
            logger.info(f"Content length: {len(content)} characters")
            
            prompt = (
                "You are an expert in compliance training. Based on the following content, "
                "generate exactly 10 multiple-choice questions (MCQs) with 4 options each. "
                "The question must be 40 percent related to the content and 60 percent should be scenario based questions. For the scenario based questions, make sure the scenario is related to the content. "
                "For each question, also provide a helpful hint that guides the user towards "
                "the correct answer without directly giving it away. "
                "Use the exact format below for each question:\n\n"
                "Question: [Question text]\n"
                "a) [Option A]\n"
                "b) [Option B]\n"
                "c) [Option C]\n"
                "d) [Option D]\n"
                "Correct Answer: [letter]\n"
                "Hint: [A helpful hint that guides towards the correct answer without revealing it directly. Dont be very direct. Be little vague in the hints]\n\n"
                f"{content}"
            )

            logger.info("Making OpenAI API request")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Changed from gpt-4o-mini to gpt-4
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates multiple choice questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,  # Increased token limit to accommodate 10 questions with hints
                temperature=0.7
            )

            raw_text = response.choices[0].message.content.strip()
            logger.info(f"Received response from OpenAI, length: {len(raw_text)} characters")
            
            mcqs = self.parse_mcqs_alternative(raw_text)
            logger.info(f"Successfully parsed {len(mcqs)} MCQs")
            
            if not mcqs:
                logger.warning("No MCQs were generated. Raw response:")
                logger.warning(raw_text)
            
            return mcqs
            
        except Exception as e:
            logger.error(f"Error generating MCQs: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate MCQs: {str(e)}")

    def parse_mcqs(self, raw_text: str):
        """
        Parse the raw text from the AI response into the desired MCQ format.
        """
        try:
            logger.info("Starting MCQ parsing")
            mcqs = []
            
            # Split by "Question:" and remove any empty blocks
            question_blocks = [block.strip() for block in raw_text.split("Question:") if block.strip()]
            logger.info(f"Found {len(question_blocks)} question blocks")

            for i, block in enumerate(question_blocks, 1):
                try:
                    logger.info(f"Parsing question block {i}")
                    
                    # Extract question text (everything before the first option)
                    question_text = block.split("a)")[0].strip()
                    logger.info(f"Question text: {question_text[:100]}...")

                    # Extract options
                    choices = {}
                    options_text = block.split("Correct Answer:")[0]
                    
                    # Extract option a
                    a_parts = options_text.split("a)")[1].split("b)")[0]
                    choices["a"] = a_parts.strip()
                    
                    # Extract option b
                    b_parts = options_text.split("b)")[1].split("c)")[0]
                    choices["b"] = b_parts.strip()
                    
                    # Extract option c
                    c_parts = options_text.split("c)")[1].split("d)")[0]
                    choices["c"] = c_parts.strip()
                    
                    # Extract option d
                    d_parts = options_text.split("d)")[1]
                    choices["d"] = d_parts.strip()

                    # Extract correct answer
                    correct_answer_section = block.split("Correct Answer:")[1].split("Hint:")[0]
                    correct_answer = correct_answer_section.strip().lower()

                    # Extract hint (everything after "Hint:" until the next "Question:" or end of text)
                    hint_section = block.split("Hint:")[1]
                    # Remove any trailing question text
                    hint = hint_section.split("Question:")[0].strip()

                    if question_text and len(choices) == 4 and correct_answer and hint:
                        mcqs.append({
                            "question": question_text,
                            "choices": choices,
                            "correctAnswer": correct_answer,
                            "hint": hint
                        })
                        logger.info(f"Successfully parsed question {i}")
                    else:
                        logger.warning(f"Failed to parse question {i}. Missing required fields:")
                        logger.warning(f"Question text: {bool(question_text)}")
                        logger.warning(f"Choices count: {len(choices)}")
                        logger.warning(f"Correct answer: {correct_answer}")
                        logger.warning(f"Hint: {bool(hint)}")
                except Exception as e:
                    logger.error(f"Error parsing question block {i}: {str(e)}")
                    continue

            logger.info(f"Successfully parsed {len(mcqs)} MCQs")
            return mcqs
            
        except Exception as e:
            logger.error(f"Error in parse_mcqs: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse MCQs: {str(e)}")

    def parse_mcqs_alternative(self, raw_text: str):
        try:
            logger.info("Starting alternative MCQ parsing")
            mcqs = []

            # Split the text into individual questions on "Question [number]:"
            questions = re.split(r'Question\s*\d+:', raw_text)
            questions = [q.strip() for q in questions if q.strip()]
            logger.info(f"Found {len(questions)} questions")

            for i, question_text in enumerate(questions, 1):
                try:
                    logger.info(f"Processing question {i}")

                    # Extract the main question (before option a))
                    main_question = question_text.split("a)")[0].strip()

                    # Extract options text (up to Correct Answer)
                    options_text = question_text.split("Correct Answer:")[0]
                    options = {}

                    # Extract each option a-d
                    for opt in ['a', 'b', 'c', 'd']:
                        opt_parts = options_text.split(f"{opt})")
                        if len(opt_parts) > 1:
                            next_opt = chr(ord(opt) + 1) if opt != 'd' else 'Correct Answer'
                            opt_text = opt_parts[1].split(f"{next_opt})")[0].strip()
                            options[opt] = opt_text

                    # Extract correct answer
                    correct_answer_section = question_text.split("Correct Answer:")[1].split("Hint:")[0]
                    correct_answer = correct_answer_section.strip().lower()

                    # Extract hint
                    hint_section = question_text.split("Hint:")[1]
                    hint = hint_section.strip()

                    if main_question and len(options) == 4 and correct_answer and hint:
                        mcqs.append({
                            "question": main_question,
                            "choices": options,
                            "correctAnswer": correct_answer,
                            "hint": hint
                        })
                        logger.info(f"Successfully parsed question {i}")
                    else:
                        logger.warning(f"Failed to parse question {i}. Missing fields")
                except Exception as e:
                    logger.error(f"Error processing question {i}: {str(e)}")
                    continue

            logger.info(f"Successfully parsed {len(mcqs)} MCQs")
            return mcqs

        except Exception as e:
            logger.error(f"Error in parse_mcqs_alternative: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse MCQs: {str(e)}")
