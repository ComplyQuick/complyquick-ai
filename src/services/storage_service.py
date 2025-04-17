import boto3
import os
from urllib.parse import urlparse
from pptx import Presentation

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )

    def download_ppt_from_s3(self, s3_url: str, download_path: str = "downloaded_presentation.pptx"):
        """
        Download a PowerPoint file from the given S3 URL and save it locally.
        """
        try:
            # Parse the S3 URL
            parsed_url = urlparse(s3_url)
            bucket_name = parsed_url.netloc.split('.')[0]  # Extract bucket name
            key = parsed_url.path.lstrip('/')  # Extract object key

            # Handle URL encoding issues
            key = key.replace('+', ' ')  # Replace '+' with spaces

            # Log the parsed values
            print(f"Bucket Name: {bucket_name}")
            print(f"Object Key: {key}")

            # Download the file
            self.s3_client.download_file(bucket_name, key, download_path)
            return download_path
        except self.s3_client.exceptions.NoSuchKey:
            raise Exception(f"The object '{key}' does not exist in bucket '{bucket_name}'.")
        except Exception as e:
            raise Exception(f"Failed to download file from S3: {str(e)}")

    def extract_content_from_ppt(self, s3_url: str):
        """
        Extract text content from a PowerPoint file stored in S3 in a structured format.
        """
        ppt_path = self.download_ppt_from_s3(s3_url)
        presentation = Presentation(ppt_path)
        
        
        structured_content = []
        
        for slide_number, slide in enumerate(presentation.slides, 1):
            slide_content = {
                "slide_number": slide_number,
                "title": "",
                "content": [],
                "notes": ""
            }
            
            # Extract slide title
            if slide.shapes.title:
                slide_content["title"] = slide.shapes.title.text.strip()
            
            # Extract text from shapes (bullet points, text boxes, etc.)
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    if shape != slide.shapes.title:  # Skip title as we already got it
                        slide_content["content"].append(shape.text.strip())
            
            # Extract speaker notes (these often contain detailed explanations)
            if slide.notes_slide and slide.notes_slide.notes_text_frame:
                slide_content["notes"] = slide.notes_slide.notes_text_frame.text.strip()
            
            structured_content.append(slide_content)
        
        # Create a comprehensive knowledge base
        knowledge_base = self._create_knowledge_base(structured_content)
        
        # Clean up the downloaded file
        try:
            os.remove(ppt_path)
        except:
            pass  # Ignore if file couldn't be deleted
            
        return knowledge_base

    def _create_knowledge_base(self, structured_content):
        """
        Convert structured PPT content into a detailed knowledge base format.
        """
        knowledge_base = []
        
        for slide in structured_content:
            # Start with the topic/title
            section = f"Topic: {slide['title']}\n\n"
            
            # Add main content points with context
            section += "Key Points:\n"
            for point in slide['content']:
                # Clean up bullet points and formatting
                clean_point = point.replace('•', '').strip()
                if clean_point:
                    section += f"- {clean_point}\n"
            
            # Add detailed explanation from notes if available
            if slide['notes']:
                section += f"\nDetailed Explanation:\n{slide['notes']}\n"
            
            knowledge_base.append(section)
        
        # Join all sections with clear separators
        return "\n\n" + "="*50 + "\n\n".join(knowledge_base)