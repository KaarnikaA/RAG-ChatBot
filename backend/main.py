#backend/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.agent import call_agent, test_connection, get_model_info
from backend.db_utils import get_last_update_date
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main")

app = FastAPI(title="Federal Documents RAG Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
@app.get("/system-info")
async def system_info():
    """Get system information including model and data stats."""
    try:
        last_update = await get_last_update_date()
        model_info = await get_model_info()
        
        return {
            "model": model_info,
            "data": last_update
        }
    except Exception as e:
        logger.error(f"Error retrieving system info: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve system information: {str(e)}"}
        )
@app.get("/health")
async def health_check():
    """Check if the API and Ollama connection are working."""
    is_connected = await test_connection()
    last_update = await get_last_update_date()
    model_info = await get_model_info()
    
    if is_connected:
        return {
            "status": "healthy", 
            "ollama_connected": True,
            "model_info": model_info,
            "data_info": last_update
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "ollama_connected": False, 
                "message": "Could not connect to Ollama service",
                "data_info": last_update
            }
        )

@app.post("/chat")
async def chat(req: Request):
    """Process a chat request and return a response."""
    try:
        data = await req.json()
        user_msg = data.get("message", "")
        
        if not user_msg:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Received chat request: {user_msg[:50]}...")
        
        # Start a background task to process the request
        # This prevents the request from timing out at the HTTP level
        answer = await call_agent(user_msg)
        
        return {"response": answer}
    except asyncio.TimeoutError:
        logger.error(f"Timeout processing chat request")
        return JSONResponse(
            status_code=504,  # Gateway Timeout
            content={"response": "The request timed out. The model might be busy or the query too complex."}
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"response": f"An error occurred: {str(e)}"}
        )

@app.get("/recent-documents")
async def recent_documents():
    """Get recent federal documents directly."""
    try:
        from backend.tools import get_recent_documents
        docs = await get_recent_documents()
        return {"documents": docs}
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve documents: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

