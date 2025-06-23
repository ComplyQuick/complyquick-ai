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
git clone https://github.com/ComplyQuick/complyquick-ai.git
cd complyquick-ai
```

2. Create and activate a virtual environment (recommended):

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**Note:** While not strictly necessary, using a virtual environment is highly recommended to avoid dependency conflicts and keep your system Python clean.

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
    - `ppt_explanation.py`: PowerPoint explanation service with concurrent processing
    - `bulk_enhancement_service.py`: Bulk slide enhancement service
    - `transcription_service.py`: Audio transcription service with concurrent processing
    - `chatbot_service.py`: AI chatbot service
    - `base_openai_service.py`: Base OpenAI service with retry logic
    - `storage_service.py`: File storage and management service
  - `types/`: Type definitions

## Key Features

### 🚀 **Concurrent Processing**

- **PPT Explanation Service**: Processes multiple slides simultaneously (3-8x faster)
- **Transcription Service**: Handles multiple audio files concurrently (2-4x faster)
- **Smart worker allocation** based on content length and API rate limits

### 🧠 **Advanced AI Capabilities**

- **Semantic Verification**: Uses sentence transformers for intelligent content coverage checking
- **TTS Optimization**: Natural speech-friendly formatting for text-to-speech systems
- **Comprehensive Content Coverage**: Ensures all slide content is addressed

### 📊 **Enhanced Services**

- **Bulk Enhancement**: Preserves all original information while adding enhancements
- **Intelligent Error Handling**: Graceful fallbacks and detailed error reporting
- **Progress Tracking**: Real-time completion status and performance statistics

## Running the Application

1. Start the development server with hot-reload:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Services

- `POST /generate_explanations`: Generate PPT explanations with concurrent processing
- `POST /enhance-all-slides`: Bulk enhance slide explanations
- `POST /transcribe-audio`: Transcribe audio files with concurrent processing
- `POST /chatbot`: AI chatbot for presentation queries

### Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Performance Optimizations

### Concurrent Processing

The application uses ThreadPoolExecutor for parallel processing:

- **PPT Explanations**: 3-8 workers based on content length
- **Audio Transcription**: Configurable workers (default: 3)
- **Batch Processing**: Memory-efficient handling of large datasets

### Semantic Verification

- Uses `all-MiniLM-L6-v2` model for content coverage verification
- 60% similarity threshold for comprehensive coverage
- Fallback to regex verification if semantic model unavailable

## Important Notes

1. **CORS Configuration**: The application allows CORS from `http://localhost:7000`. Modify CORS settings in `app.py` if needed.

2. **API Rate Limits**: The concurrent processing is designed to respect API rate limits while maximizing performance.

3. **Memory Management**: Large presentations are processed in batches to manage memory efficiently.

4. **Error Resilience**: Individual failures don't stop the entire process - the system continues with available results.

## Troubleshooting

### Common Issues

1. **Dependency Issues**:

   ```bash
   # Ensure virtual environment is activated
   pip install -r requirements.txt --upgrade
   ```

2. **API Key Issues**:

   - Verify all environment variables are set correctly
   - Check API key permissions and quotas

3. **Concurrent Processing Issues**:

   - Reduce `max_workers` if experiencing rate limit issues
   - Check system resources (CPU, memory)

4. **Semantic Verification Issues**:
   - The system automatically falls back to regex verification
   - Check internet connection for model downloads

### Performance Tuning

- **For large presentations**: Reduce concurrent workers to avoid rate limits
- **For memory constraints**: Use batch processing with smaller batch sizes
- **For faster processing**: Increase workers (monitor API rate limits)

## Support

For additional support or questions, please contact the project maintainers or create an issue on the [GitHub repository](https://github.com/ComplyQuick/complyquick-ai.git).
