from fastapi import Request, status
from fastapi.responses import JSONResponse
import uuid
from src.shared.logger import logger

class ConversAIException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    logger.error(f"Error handling request {request_id}: {str(exc)}")
    
    error_code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred."
    
    if isinstance(exc, ConversAIException):
        error_code = exc.code
        message = exc.message
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "requestId": request_id
            }
        }
    )
