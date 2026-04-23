"""
Explanation Controller - API Layer

This controller handles HTTP requests for the /api/explain endpoint.
It delegates all orchestration to the Aggregation Engine.

The controller is THIN and only handles:
- HTTP request/response
- Error boundary (ValidationError → 400, AggregationError → 500)
- Logging at the HTTP layer

It does NOT:
- Call engines directly
- Orchestrate engine calls
- Manipulate segments, visuals, or metadata
"""

from fastapi import HTTPException
from src.shared.types import ExplainRequest, FollowUpRequest
from src.engines.aggregation import aggregate, AggregationError, ValidationError
from src.shared.logger import logger


class ExplanationController:
    @staticmethod
    async def process_request(request: ExplainRequest) -> dict:
        """
        Process explanation request by delegating to Aggregation Engine.
        
        Args:
            request: ExplainRequest with text, duration, instruction, avatarEnabled
            
        Returns:
            Unified multimodal response from Aggregation Engine
            
        Raises:
            HTTPException: 400 for validation errors, 500 for aggregation failures
        """
        logger.info(f"Received explanation request: text={len(request.text)} chars, duration={request.duration}")
        
        try:
            # Delegate to Aggregation Engine
            response = await aggregate(
                text=request.text,
                duration=request.duration, 
                instruction=request.instruction,
                avatar_enabled=request.avatarEnabled
            )
            
            logger.info(
                f"Request completed successfully: "
                f"{len(response['segments'])} segments, "
                f"{response['audioDuration']:.1f}s audio, "
                f"visuals: {response['metadata']['visualStats']['generated']}/{response['metadata']['visualStats']['requested']}"
            )
            
            return response
            
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
            
        except AggregationError as e:
            logger.error(f"Aggregation failed: component={e.component}, error={e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Aggregation failed",
                    "component": e.component,
                    "message": str(e)
                }
            )
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    @staticmethod
    async def process_followup(request: FollowUpRequest) -> dict:
        """
        Process a follow-up question by constructing enriched context.
        
        Takes the original text + follow-up question and runs it through
        the same aggregation pipeline with a focused instruction.
        """
        logger.info(f"Received follow-up request: question='{request.followUpQuestion[:80]}...'")
        
        # Construct enriched text that includes context
        enriched_text = (
            f"Original Context:\n{request.originalText}\n\n"
            f"Follow-up Question:\n{request.followUpQuestion}"
        )
        
        # Create a focused instruction for the LLM
        followup_instruction = (
            f"The user previously received an explanation of the above context. "
            f"Now they are asking a follow-up question: \"{request.followUpQuestion}\". "
            f"Create a focused, concise explanation that directly answers their follow-up question. "
            f"Reference the original context when relevant but focus on the new question."
        )
        
        try:
            response = await aggregate(
                text=enriched_text,
                duration=request.duration,
                instruction=followup_instruction,
                avatar_enabled=request.avatarEnabled
            )
            
            logger.info(f"Follow-up completed: {len(response['segments'])} segments")
            return response
            
        except ValidationError as e:
            logger.warning(f"Follow-up validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        except AggregationError as e:
            logger.error(f"Follow-up aggregation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Follow-up failed", "component": e.component, "message": str(e)}
            )
            
        except Exception as e:
            logger.error(f"Follow-up unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
