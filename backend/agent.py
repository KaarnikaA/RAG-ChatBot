# File: backend/agent.py
import httpx
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent")

# Load environment variables
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "Mistral:latest")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # Increased timeout
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))  # Control response length

async def test_connection() -> bool:
    """Test the connection to Ollama API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            response.raise_for_status()
            logger.info(f"Successfully connected to Ollama API. Available models: {response.json()}")
            return True
    except Exception as e:
        logger.error(f"Failed to connect to Ollama API: {str(e)}")
        return False

async def call_agent(user_query: str, include_documents: bool = True) -> str:
    """Call the Ollama model with the user query."""
    start_time = asyncio.get_event_loop().time()
    logger.info(f"Starting query processing: {user_query}")
    
    # Try to get recent documents if requested
    documents = []
    if include_documents:
        try:
            from backend.tools import get_recent_documents
            documents = await get_recent_documents()
            logger.info(f"Retrieved {len(documents)} documents in {asyncio.get_event_loop().time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
    
    # Format the prompt with context from documents
    context = ""
    if documents:
        context = "Here's some recent information that might be helpful:\n\n"
        for i, doc in enumerate(documents, 1):
            # Limit number of documents to prevent context overflow
            if i > 3:  # Only use the 3 most recent documents
                break
            context += f"Document {i}:\n"
            context += f"Title: {doc['title']}\n"
            context += f"Date: {doc['date']}\n"
            # Limit summary length
            summary = doc['summary']
            if len(summary) > 300:
                summary = summary[:300] + "..."
            context += f"Summary: {summary}\n\n"
    
    full_prompt = f"{context}\nUser question: {user_query}\n\nPlease provide a brief, helpful response:"
    
    # Log the prompt for debugging
    logger.info(f"Prompt length: {len(full_prompt)} chars")
    logger.info(f"Sending prompt to model (truncated): {full_prompt[:100]}...")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "num_predict": MAX_TOKENS,  # Limit token generation
        "options": {
            "num_ctx": 4096,  # Context window size
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9
        }
    }

    # Try to connect to the model with retries
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt} to connect to Ollama API")
            
            # Create a timeout mechanism
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    logger.info(f"Sending request to {OLLAMA_BASE_URL.rstrip('/')}/api/generate")
                    response = await client.post(
                        f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate", 
                        json=payload,
                        timeout=REQUEST_TIMEOUT  # Explicit timeout setting
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Calculate total time taken
                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Received response in {elapsed:.2f}s")
                    
                    model_response = result.get("response", "No response from model.")
                    
                    # Trim extremely long responses
                    if len(model_response) > 2000:
                        model_response = model_response[:2000] + "... [Response truncated due to length]"
                    
                    return model_response
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout on attempt {attempt} after {REQUEST_TIMEOUT}s")
            if attempt == max_retries:
                return f"Request timed out after {REQUEST_TIMEOUT} seconds. The model might be processing a complex query or experiencing high load."
            await asyncio.sleep(1)  # Wait before retrying
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {str(e)}")
            return f"Error processing request: {str(e)}"
async def get_model_info() -> Dict[str, Any]:
    """Return basic information about the model setup."""
    return {
        "model_name": MODEL_NAME,
        "base_url": OLLAMA_BASE_URL,
        "max_tokens": MAX_TOKENS,
        "timeout": REQUEST_TIMEOUT
    }

if __name__ == "__main__":
    # This allows for testing the module directly
    async def test():
        # Test the connection
        is_connected = await test_connection()
        print(f"Connection test result: {is_connected}")
        
        if is_connected:
            # Test the model with a simple query
            response = await call_agent("What are the most recent federal documents?")
            print(f"Model response: {response}")
    
    asyncio.run(test())



