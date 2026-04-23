# ConversAI V1 - Backend API Plan

> [!IMPORTANT]
> This document reflects the **implemented** backend API for ConversAI V1.

> [!NOTE]
> **Updates from original design**: The `VisualType` enum has been simplified. The `Visual` model now carries `headline` and `imagePrompt` fields (Pollinations.ai approach). A `/api/explain/followup` endpoint has been added. The `ExplainResponse` returns a `segments` array (not separate `visuals` + `audio` at top level).

## 1. Backend Folder Structure

Strict adherence to the architecture documentation. All code resides in `conversai-backend/src/`.

```text
conversai-backend/
├── src/
│   ├── api/                          # API Orchestration Layer
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── explanation.py         # POST /api/explain
│   │   │   └── health.py              # GET /api/health
│   │   ├── controllers/
│   │   │   ├── __init__.py
│   │   │   └── explanation_controller.py  # Orchestrates pipeline
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py           # Input validation logic
│   │   │   └── error_handler.py       # Global exception handler
│   │   └── main.py                    # FastAPI app entry point
│   │
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── explanation/               # Explanation Engine
│   │   │   ├── __init__.py            # Facade
│   │   │   ├── analyzer.py
│   │   │   ├── structurer.py
│   │   │   └── narrator.py
│   │   ├── visual/                    # Visual Engine
│   │   │   ├── __init__.py            # Facade
│   │   │   ├── planner.py
│   │   │   └── generator.py
│   │   ├── voice/                     # Voice Engine
│   │   │   ├── __init__.py            # Facade
│   │   │   ├── tts.py
│   │   │   └── avatar.py
│   │   └── aggregation/               # Aggregation Engine
│   │       ├── __init__.py            # Facade
│   │       ├── synchronizer.py
│   │       └── composer.py
│   │
│   └── shared/                        # Shared Utilities
│       ├── __init__.py
│       ├── config.py                  # Env vars
│       ├── logger.py                  # Central logging
│       └── types.py                   # Shared Pydantic models
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 2. API Endpoint Contracts

### Shared Types (`src/shared/types.py`)

```python
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

class Visual(BaseModel):
    url: str              # Pollinations.ai CDN URL (1280×720, 16:9)
    startTime: float
    endTime: float
    type: VisualType
    headline: str         # Short overlay text shown on image in player
    imagePrompt: str      # Full Gemini-generated prompt (for debug)
    metadata: dict        # segmentId, concept, generationMethod

class AvatarState(BaseModel):
    startTime: float
    endTime: float
    state: str            # "speaking" | "idle"
    intensity: str        # "low" | "medium" | "high"

class AvatarData(BaseModel):
    states: List[AvatarState]
    cues: List[dict]

class Segment(BaseModel):
    id: str
    text: str
    startTime: float
    endTime: float
    visual: Optional[Visual] = None   # Attached by synchronizer

class ResponseMetadata(BaseModel):
    duration: float
    segmentCount: int
    hasAvatar: bool
```

### POST `/api/explain` (`src/api/routes/explanation.py`)

**Request Schema:**
```python
class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=100, max_length=5000)
    duration: Duration = Field(default=Duration.MEDIUM)
    instruction: Optional[str] = Field(None)
    avatarEnabled: bool = Field(default=True)
```

**Response Schema (actual implemented format):**
```python
class ExplainResponse(BaseModel):
    narration: str              # Full narration text
    segments: List[Segment]     # Segments with visual attached to each
    audio: str                  # Raw base64 MP3 (no data: URI prefix)
    audioDuration: float
    avatar: Optional[AvatarData]
    metadata: ResponseMetadata
```

**Example response shape:**
```json
{
  "narration": "Blockchain is a distributed ledger...",
  "segments": [
    {
      "id": "segment_1",
      "text": "A blockchain is a digital ledger...",
      "startTime": 0.0,
      "endTime": 12.8,
      "visual": {
        "url": "https://image.pollinations.ai/prompt/...",
        "headline": "A Shared Record Open to Everyone",
        "imagePrompt": "A massive holographic ledger...",
        "type": "abstract_concept",
        "startTime": 0.0,
        "endTime": 12.8,
        "metadata": {"segmentId": "segment_1", "generationMethod": "pollinations_ai"}
      }
    }
  ],
  "audio": "//uQxAAAAAAA...",
  "audioDuration": 45.3,
  "avatar": {"states": [...], "cues": [...]},
  "metadata": {"duration": 45.3, "segmentCount": 6, "hasAvatar": true}
}
```

### POST `/api/explain/followup` (`src/api/routes/explanation.py`)

**Purpose**: Process a follow-up question using the existing explanation as context.

**Request Schema:**
```python
class FollowUpRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    context: str = Field(..., description="Original narration text as context")
```

**Response Schema:**
```python
# Same as ExplainResponse — generates a fresh short explanation
# scoped to the follow-up question, with new audio and visuals
```

**Response Schema:**
```python
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
```

## 3. Controller Orchestration Flow

**Module:** `src/api/controllers/explanation_controller.py`
**Class:** `ExplanationController`
**Method:** `process_request(request: ExplainRequest) -> ExplainResponse`

**Deep Orchestration Steps:**
1.  **Input:** Controller receives validated `ExplainRequest`.
2.  **Explanation Engine**: Call `explanation.process(text, duration, instruction)`
    *   *Returns:* Narration text string, List of Segments.
3.  **Visual Engine**: Call `visual.generate(segments)`
    *   *Returns:* List of Visual objects (images).
4.  **Voice Engine**: Call `voice.synthesize(narration, avatar_enabled)`
    *   *Returns:* Audio data (base64/path), Optional Avatar data.
5.  **Aggregation Engine**: Call `aggregation.compose(audio, visuals, avatar)`
    *   *Returns:* Final aligned structure.
6.  **Output:** Construct and return `ExplainResponse`.

## 4. Error Handling Strategy

**Module:** `src/api/middleware/error_handler.py`

1.  **Global Exception Handler**:
    *   Decorate FastAPI app with `@app.exception_handler(Exception)` to catch unhandled errors.
    *   Catch specific `ConversAIException` for known errors.

2.  **Standard Error Response Format**:
    All errors must return this JSON structure:
    ```json
    {
      "error": {
        "code": "ERROR_CODE_STRING",
        "message": "Human readable message",
        "requestId": "correlation-id"
      }
    }
    ```

3.  **Exception Hierarchy**:
    *   `ConversAIException` (Base)
        *   `ValidationError` (Input issues)
        *   `EngineError` (When an engine fails)
            *   `ExplanationEngineError`
            *   `VisualEngineError`
            *   `VoiceEngineError`

## 5. Implementation Strategy (Stub vs Real)

**Files to Implement Now (Skeleton):**
*   **`src/main.py`**: FastAPI app setup, CORS, middleware attachment.
*   **`src/api/routes/*`**: Route definitions, Pydantic models, controller invocation.
*   **`src/api/controllers/explanation_controller.py`**: Full class structure. `process_request` method will exist but will call stubs.
*   **`src/shared/types.py`**: Complete Pydantic type definitions.
*   **`src/engines/*/init.py`**: Public facade functions signature (e.g., `def process(...)`). Implementation will be `pass` or return dummy response.

**Files to Stub (Empty/Pass):**
*   **`src/engines/*/*.py`** (Internal logic like `analyzer.py`): Create empty files or empty classes.
*   **`src/shared/logger.py`**: Simple print-based or basic logging setup.
*   **`src/shared/config.py`**: Basic `BaseSettings` setup.
