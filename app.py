from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from src.routes import router
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL"), "http://192.168.1.30:5000"],  # Get from environment variable
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the router from routes.py
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)