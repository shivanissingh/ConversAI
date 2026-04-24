from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Duration(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"

class VisualType(str, Enum):
    ABSTRACT_CONCEPT = "abstract_concept"
    PROCESS_FLOW = "process_flow"
    STRUCTURE_DIAGRAM = "structure_diagram"
    COMPARISON = "comparison"
    METAPHOR = "metaphor"
    ICON_COMPOSITION = "icon_composition"
    PLACEHOLDER = "placeholder"

class Segment(BaseModel):
    text: str
    startTime: float
    endTime: float

class VisualPlan(BaseModel):
    segmentId: str
    visualType: VisualType
    prompt: str
    startTime: float
    endTime: float
    metadata: dict

class Visual(BaseModel):
    url: str
    startTime: float
    endTime: float
    type: VisualType
    metadata: Optional[dict] = None

class AvatarState(BaseModel):
    startTime: float
    endTime: float
    state: str  # "speaking" | "idle"
    intensity: str  # "low" | "medium" | "high"

class AnimationCue(BaseModel):
    timestamp: float
    cueType: str  # "segment_start" | "segment_end" | "emphasis"
    metadata: dict

class AvatarData(BaseModel):
    states: List[AvatarState]
    cues: List[AnimationCue]
    metadata: dict

class ResponseMetadata(BaseModel):
    duration: float
    segmentCount: int
    hasAvatar: bool

class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=100, max_length=5000, description="Input text to explain")
    duration: Duration = Field(default=Duration.MEDIUM)
    instruction: Optional[str] = Field(None, description="Custom instruction, e.g., 'Like I'm 5'")
    avatarEnabled: bool = Field(default=True)

class FollowUpRequest(BaseModel):
    originalText: str = Field(..., min_length=10, max_length=5000, description="Original text that was explained")
    followUpQuestion: str = Field(..., min_length=5, max_length=500, description="Follow-up question from the user")
    duration: Duration = Field(default=Duration.SHORT)
    avatarEnabled: bool = Field(default=True)

class TopicRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=2000, description="Topic or question to explain, e.g. 'Explain quantum computing'")
    duration: Duration = Field(default=Duration.MEDIUM)
    instruction: Optional[str] = Field(None, max_length=2000, description="Custom instruction, e.g., 'Like I'm 5'")
    avatarEnabled: bool = Field(default=True)


class ExplainResponse(BaseModel):
    audio: str = Field(..., description="Base64 encoded audio or URL")
    visuals: List[Visual]
    avatar: Optional[AvatarData] = None
    metadata: ResponseMetadata
