from fastapi import APIRouter
from src.shared.types import ExplainRequest, FollowUpRequest, TopicRequest
from src.api.controllers.explanation_controller import ExplanationController
from src.api.controllers.topic_controller import TopicController

router = APIRouter()

@router.post("/explain")
async def explain(request: ExplainRequest):
    """
    Generate a narrated, multimodal explanation for the given text.
    
    Returns a unified response with narration, segments, visuals, audio, and optional avatar.
    """
    return await ExplanationController.process_request(request)


@router.post("/explain/topic")
async def explain_topic(request: TopicRequest):
    """
    Topic Mode: generate a full multimodal explanation from a topic string.

    The backend expands the topic into source text via Gemini, then runs it
    through the identical pipeline as /api/explain.  The response schema is
    identical so the frontend can reuse the same handler.

    Body:
        topic (str, 5-200 chars): e.g. "Explain quantum computing"
        duration ("short" | "medium", default "medium")
        instruction (str, optional): e.g. "Explain like I'm 5"
        avatarEnabled (bool, default true)
    """
    return await TopicController.process_topic(request)


@router.post("/explain/followup")
async def followup(request: FollowUpRequest):
    """
    Generate a follow-up explanation based on a previous context + new question.
    
    Takes the original text as context and a follow-up question,
    then generates a new multimodal explanation focused on answering the question.
    """
    return await ExplanationController.process_followup(request)

