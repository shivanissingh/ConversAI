from fastapi import APIRouter
from src.shared.types import ExplainRequest, FollowUpRequest
from src.api.controllers.explanation_controller import ExplanationController

router = APIRouter()

@router.post("/explain")
async def explain(request: ExplainRequest):
    """
    Generate a narrated, multimodal explanation for the given text.
    
    Returns a unified response with narration, segments, visuals, audio, and optional avatar.
    """
    return await ExplanationController.process_request(request)


@router.post("/explain/followup")
async def followup(request: FollowUpRequest):
    """
    Generate a follow-up explanation based on a previous context + new question.
    
    Takes the original text as context and a follow-up question,
    then generates a new multimodal explanation focused on answering the question.
    """
    return await ExplanationController.process_followup(request)
