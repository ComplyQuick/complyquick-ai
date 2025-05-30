import boto3
import os
from urllib.parse import urlparse, unquote_plus
from pptx import Presentation
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ]
        self._initialize_google_credentials()
        
        # Validate AWS credentials
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION")
        
        if not all([aws_access_key, aws_secret_key, aws_region]):
            logger.error("Missing AWS credentials. Please check your environment variables.")
            raise ValueError("AWS credentials not properly configured. Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION")
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            # Test the credentials by making a simple S3 call
            self.s3_client.list_buckets()
            logger.info("Successfully initialized AWS S3 client")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {str(e)}")
            raise ValueError(f"Failed to initialize AWS S3 client: {str(e)}")

    def _initialize_google_credentials(self):
        """Initialize Google Drive credentials from environment variables"""
        try:
            self.creds = Credentials(
                None,  # Token is not needed as we'll use refresh token
                client_id=os.getenv('GOOGLE_DRIVE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_DRIVE_CLIENT_SECRET'),
                token_uri='https://oauth2.googleapis.com/token',
                refresh_token=os.getenv('GOOGLE_DRIVE_REFRESH_TOKEN')
            )
            logger.info("Successfully initialized Google Drive credentials")
        except Exception as e:
            logger.error(f"Error initializing Google Drive credentials: {str(e)}")
            raise ValueError("Failed to initialize Google Drive credentials. Check your environment variables.")

    def _get_file_id_from_url(self, url: str) -> str:
        """Extract file ID from Google Docs URL"""
        try:
            parsed_url = urlparse(url)
            
            # Handle different Google Drive URL formats
            if 'docs.google.com' in parsed_url.netloc:
                path_parts = parsed_url.path.split('/')
                # The ID is usually after /d/ in the URL
                for i, part in enumerate(path_parts):
                    if part == 'd':
                        return path_parts[i + 1].split('/')[0]
            
            # Handle direct drive.google.com URLs
            if 'drive.google.com' in parsed_url.netloc:
                if 'id=' in url:
                    # Handle old-style URLs with id parameter
                    return parsed_url.query.split('id=')[1].split('&')[0]
                else:
                    # Handle new-style URLs
                    path_parts = parsed_url.path.split('/')
                    for i, part in enumerate(path_parts):
                        if part in ['d', 'file']:
                            return path_parts[i + 1]
            
            raise ValueError("Could not extract file ID from URL")
        except Exception as e:
            logger.error(f"Error extracting file ID from URL: {str(e)}")
            raise ValueError(f"Invalid Google Drive URL format: {url}")

    def download_presentation(self, presentation_url: str, download_path: str = None) -> str:
        """
        Download a presentation from either Google Drive or S3
        """
        try:
            logger.info(f"Starting download of presentation from URL: {presentation_url}")
            
            # If no download path is provided, extract extension from URL
            if not download_path:
                file_extension = os.path.splitext(presentation_url)[1]
                if not file_extension:
                    file_extension = '.pptx'  # Default to .pptx if no extension found
                download_path = f"downloaded_presentation{file_extension}"
            
            logger.info(f"Using download path: {download_path}")
            
            # Check if it's a Google Drive URL
            if 'docs.google.com' in presentation_url or 'drive.google.com' in presentation_url:
                logger.info("Detected Google Drive URL")
                return self._download_from_google_drive(presentation_url, download_path)
            # Check if it's an S3 URL
            elif 's3.' in presentation_url or '.amazonaws.com' in presentation_url:
                logger.info("Detected S3 URL")
                return self.download_ppt_from_s3(presentation_url, download_path)
            else:
                raise ValueError(f"Unsupported URL format: {presentation_url}. Must be either Google Drive or S3 URL.")
                
        except Exception as e:
            logger.error(f"Error downloading presentation: {str(e)}", exc_info=True)
            raise Exception(f"Failed to download presentation: {str(e)}")

    def _download_from_google_drive(self, url: str, download_path: str) -> str:
        """Download presentation from Google Drive"""
        try:
            file_id = self._get_file_id_from_url(url)
            if not file_id:
                raise ValueError("Invalid Google Drive URL")

            service = build('drive', 'v3', credentials=self.creds)
            
            # Get the file metadata
            file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
            mime_type = file_metadata.get('mimeType', '')
            
            # Different handling based on file type
            if mime_type == 'application/vnd.google-apps.presentation':
                # Native Google Slides
                request = service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
            else:
                # Uploaded PowerPoint file
                request = service.files().get_media(fileId=file_id)
            
            file_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

            file_handle.seek(0)
            with open(download_path, 'wb') as f:
                f.write(file_handle.read())

            logger.info(f"Successfully downloaded presentation to: {download_path}")
            return download_path

        except Exception as e:
            logger.error(f"Error downloading from Google Drive: {str(e)}", exc_info=True)
            raise Exception(f"Failed to download from Google Drive: {str(e)}")

    def download_ppt_from_s3(self, s3_url: str, download_path: str = "downloaded_presentation.pptx"):
        """
        Download a PowerPoint file from the given S3 URL and save it locally.
        """
        try:
            logger.info(f"Attempting to download from S3: {s3_url}")
            
            # Parse the S3 URL
            parsed_url = urlparse(s3_url)
            bucket_name = parsed_url.netloc.split('.')[0]
            
            # Fix double encoding issue
            key = parsed_url.path.lstrip('/')
            # First, decode %25 to % if it exists
            key = key.replace('%25', '%')
            # Then decode the remaining URL encoding
            key = unquote_plus(key)
            
            logger.info(f"Parsed S3 URL - Bucket: {bucket_name}, Key: {key}")
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
            except self.s3_client.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    raise Exception(f"Bucket '{bucket_name}' does not exist")
                elif error_code == '403':
                    raise Exception(f"Access denied to bucket '{bucket_name}'. Please check your AWS credentials and permissions.")
                else:
                    raise Exception(f"Error accessing bucket '{bucket_name}': {str(e)}")

            # Check if object exists and is accessible
            try:
                self.s3_client.head_object(Bucket=bucket_name, Key=key)
            except self.s3_client.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    raise Exception(f"File '{key}' not found in bucket '{bucket_name}'")
                elif error_code == '403':
                    raise Exception(f"Access denied to file '{key}' in bucket '{bucket_name}'. Please check your AWS credentials and permissions.")
                else:
                    raise Exception(f"Error accessing file '{key}' in bucket '{bucket_name}': {str(e)}")

            logger.info(f"Attempting to download file...")
            # Download the file
            self.s3_client.download_file(bucket_name, key, download_path)
            logger.info(f"Successfully downloaded file to: {download_path}")
            
            return download_path
            
        except self.s3_client.exceptions.NoSuchKey:
            logger.error(f"File not found in S3: {key}", exc_info=True)
            raise Exception(f"The object '{key}' does not exist in bucket '{bucket_name}'.")
        except Exception as e:
            logger.error(f"Error downloading from S3: {str(e)}", exc_info=True)
            raise Exception(f"Failed to download file from S3: {str(e)}")

    def extract_content_from_ppt(self, presentation_url: str):
        """
        Extract text content from a PowerPoint file from either Google Drive or S3
        """
        try:
            logger.info(f"Starting content extraction from presentation URL: {presentation_url}")
            
            # Use the generic download method instead of directly calling S3
            logger.info("Downloading presentation...")
            ppt_path = self.download_presentation(presentation_url)
            logger.info(f"Presentation downloaded to: {ppt_path}")
            
            logger.info("Opening presentation file...")
            presentation = Presentation(ppt_path)
            logger.info(f"Successfully opened presentation with {len(presentation.slides)} slides")
            
            structured_content = []
            
            for slide_number, slide in enumerate(presentation.slides, 1):
                logger.info(f"Processing slide {slide_number}")
                slide_content = {
                    "slide_number": slide_number,
                    "title": "",
                    "content": [],
                    "notes": ""
                }
                
                # Extract slide title
                if slide.shapes.title:
                    slide_content["title"] = slide.shapes.title.text.strip()
                    logger.info(f"Extracted title: {slide_content['title']}")
                
                # Extract text from shapes (bullet points, text boxes, etc.)
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        if shape != slide.shapes.title:  # Skip title as we already got it
                            content = shape.text.strip()
                            slide_content["content"].append(content)
                            logger.info(f"Extracted content: {content[:100]}...")
                
                # Extract speaker notes
                if slide.notes_slide and slide.notes_slide.notes_text_frame:
                    slide_content["notes"] = slide.notes_slide.notes_text_frame.text.strip()
                    logger.info(f"Extracted notes: {slide_content['notes'][:100]}...")
                
                structured_content.append(slide_content)
            
            # Create a comprehensive knowledge base
            logger.info("Creating knowledge base from structured content...")
            knowledge_base = self._create_knowledge_base(structured_content)
            logger.info(f"Knowledge base created with length: {len(knowledge_base)}")
            
            # Clean up the downloaded file
            try:
                logger.info("Cleaning up downloaded file...")
                os.remove(ppt_path)
                logger.info("File cleanup successful")
            except Exception as e:
                logger.warning(f"Failed to clean up file: {str(e)}")
            
            return knowledge_base
        except Exception as e:
            logger.error(f"Error extracting content from presentation: {str(e)}", exc_info=True)
            raise Exception(f"Failed to extract content from presentation: {str(e)}")

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