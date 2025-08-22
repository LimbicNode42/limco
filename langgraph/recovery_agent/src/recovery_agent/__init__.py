import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure LANGSMITH_API_KEY is available
if not os.getenv("LANGSMITH_API_KEY"):
    print("Warning: LANGSMITH_API_KEY not found in environment variables")
