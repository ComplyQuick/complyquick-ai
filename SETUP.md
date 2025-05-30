# ComplyQuick AI Setup Guide

This document provides step-by-step instructions to set up and run the ComplyQuick AI service.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- Git

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd complyquick-ai
```

2. Create and activate a virtual environment:
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Google API Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# AWS Configuration (if using AWS services)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
```

Replace the placeholder values with your actual API keys and credentials.

## Project Structure

The project is organized as follows:
- `app.py`: Main FastAPI application entry point
- `src/`: Source code directory
  - `routes.py`: API route definitions
  - `models.py`: Data models
  - `services/`: Service implementations
  - `types/`: Type definitions

## Running the Application

1. Start the FastAPI server:
```bash
python app.py
```

The server will start on `http://localhost:8000`

2. For development, you can use hot-reload:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Important Notes

1. The application is configured to allow CORS from `http://localhost:7000`. If you need to allow other origins, modify the CORS settings in `app.py`.

2. Make sure all required API keys and credentials are properly set in the `.env` file before starting the application.

3. The application uses several external services:
   - OpenAI API for LLM capabilities
   - Google APIs for authentication and services
   - AWS services (if configured)

## Troubleshooting

1. If you encounter dependency issues:
   - Ensure your virtual environment is activated
   - Try running `pip install -r requirements.txt` again
   - Check Python version compatibility

2. If the server fails to start:
   - Check if port 8000 is available
   - Verify all environment variables are set correctly
   - Check the console for error messages

3. For API-related issues:
   - Verify API keys are correct
   - Check service quotas and limits
   - Ensure proper network connectivity

## Support

For additional support or questions, please contact the project maintainers. 