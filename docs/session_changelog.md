# ConversAI — Complete Agent Session Changelog

> **Session Date:** April 22–23, 2026  
> **Project:** ConversAI — AI-Powered Multimodal Explanation System  
> **Objective:** Finalize the Digital Human experience, implement real AI visuals, replace emojis with professional icons, integrate TalkingHead.js 3D avatar, and polish the end-to-end pipeline for Major Project submission.

---

## Table of Contents

1. [Session Overview](#1-session-overview)
2. [Prior Session Recap (Truncated Context)](#2-prior-session-recap)
3. [Changes Made — Backend](#3-changes-made--backend)
4. [Changes Made — Frontend](#4-changes-made--frontend)
5. [New Files Created](#5-new-files-created)
6. [Files Modified](#6-files-modified)
7. [Packages Installed](#7-packages-installed)
8. [Debugging & Issue Resolution](#8-debugging--issue-resolution)
9. [Architecture Decisions](#9-architecture-decisions)
10. [Final System State](#10-final-system-state)
11. [Remaining Work](#11-remaining-work)

---

## 1. Session Overview

This session transformed ConversAI from a **text-card-based explanation system** into a **full Digital Human experience** with:

| Feature | Before | After |
|---|---|---|
| **Visuals** | Gemini-generated text cards (headline, bullet points, emoji flow) | Real AI-generated 1280×720 images via Pollinations.ai |
| **Icons** | Emoji characters (📖, ✍️, 🎨, etc.) | Professional Lucide React SVG icons |
| **Avatar** | CSS-animated circle with pulsing effects | TalkingHead.js 3D WebGL avatar with lip-sync |
| **Loading View** | Rotating message carousel | Step-by-step pipeline progress with timer |
| **Image Pre-warming** | None — images generated on frontend demand | Backend pre-warms all Pollinations URLs concurrently |

### Timeline of Work

| Time | Action |
|---|---|
| 12:59 PM | Upgraded LoadingView from rotating messages → pipeline steps |
| 1:00 PM | Updated LoadingView CSS for pipeline step layout |
| **— User reconnects after network issues —** |
| 2:13 PM | Installed `lucide-react` npm package |
| 2:15 PM | Rewrote `planner.py` — Gemini now generates image prompts + Pollinations.ai URLs |
| 2:15 PM | Rewrote `generator.py` — visuals now carry real image URLs |
| 2:16 PM | Rewrote `VisualDisplay.jsx` — renders `<img>` from Pollinations URLs |
| 2:17 PM | Rewrote `VisualDisplay.css` — 16:9 image container, shimmer, overlay |
| 2:18 PM | Rewrote `LandingPage.jsx` — all emojis → Lucide icons |
| 2:18 PM | Updated `LandingPage.css` — icon wrapper styles |
| 2:19 PM | Updated `LoadingView.jsx` — emoji pipeline steps → Lucide icons |
| 2:19 PM | Updated `LoadingView.css` — icon color styles |
| 2:23 PM | Installed `@met4citizen/talkinghead` from GitHub |
| 2:31 PM | Created `DigitalHuman.jsx` — TalkingHead.js integration |
| 2:32 PM | Created `DigitalHuman.css` — avatar card styles |
| 2:32 PM | Updated `PlaybackView.jsx` — replaced `Avatar` with `DigitalHuman` |
| 2:33 PM | Updated `vite.config.js` — excluded TalkingHead from dep optimizer |
| **— User reports "Visual unavailable" and "Avatar unavailable" —** |
| 3:54 PM | Rewrote `VisualDisplay.jsx` with retry logic (3 retries, pre-loading) |
| **— Session resumes next morning —** |
| 4:26 AM | Passed `allVisuals` prop to VisualDisplay for pre-loading |
| 4:27 AM | Updated VisualDisplay CSS — error fallback styles |
| 4:29 AM | Added loading-subtext CSS |
| 4:30 AM | Added backend pre-warming of Pollinations URLs |
| 4:31–5:36 AM | Multiple iterations fixing TalkingHead.js Vite compatibility |
| 5:36 AM | Final fix: `@talkinghead` alias in vite.config.js + vendor folder |

---

## 2. Prior Session Recap

Before this session, the following features were already implemented (in a truncated prior conversation):

- **Landing Page** (`LandingPage.jsx`) — premium entry point with hero, stats, pipeline diagram, features grid
- **Voice Input** (`useSpeechRecognition.js`) — Web Speech API mic button for hands-free text input
- **Follow-Up Loop** — `/api/explain/followup` backend endpoint + follow-up input bar in PlaybackView
- **State Management** — `LANDING → INPUT → LOADING → PLAYBACK` flow in App.jsx
- **Framer Motion** animations on all state transitions

---

## 3. Changes Made — Backend

### 3.1 Visual Engine: Text Cards → Real AI Images

#### [planner.py](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/src/engines/visual/planner.py) — Complete Rewrite (266 lines)

**Before:** Gemini generated structured JSON "visual cards" with fields like `headline`, `keyPoints`, `analogy`, `emojiFlow`, `icon`, `cardType`. The frontend rendered these as animated text slides.

**After:** Gemini generates vivid **image prompts** (2-3 sentence scene descriptions) for each segment. The backend then:
1. Builds a Pollinations.ai URL from each prompt
2. Pre-warms ALL URLs concurrently (fires GET requests to trigger image generation while audio is still being synthesized)
3. Returns the URLs in the response — frontend renders them as `<img>` tags

**Key changes:**
- New system prompt `IMAGE_PROMPT_SYSTEM` — instructs Gemini to think like a "documentary filmmaker" and describe specific visual scenes (colors, lighting, composition)
- New function `generate_image_prompts_via_gemini()` replacing `generate_visual_cards_via_gemini()`
- URL format: `https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&seed={hash}`
- Pre-warming via `asyncio.gather()` with 45s timeout per image
- Backward-compat aliases kept so the generator module still works
- Fallback prompts use generic educational visuals (glowing networks, brain synapses, etc.)

```python
# Pre-warm all Pollinations URLs concurrently
async def _prewarm(url: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=45.0) as c:
            await c.get(url)
    except Exception:
        pass  # Best-effort

await asyncio.gather(*[_prewarm(item["imageUrl"]) for item in image_data])
```

#### [generator.py](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/src/engines/visual/generator.py) — Complete Rewrite (157 lines)

**Before:** Created visual objects with `url: None` and `cardData: {...}` (text card data).

**After:** Creates visual objects with:
- `url`: Real Pollinations.ai image URL
- `headline`: Short overlay text for the image
- `imagePrompt`: The full Gemini-generated prompt (for debugging)
- `style`: cinematic / 3d_render / photorealistic / illustration
- No more `cardData` field

```python
# Old output per visual:
{"url": None, "cardData": {"headline": "...", "keyPoints": [...], "emojiFlow": "💡→✨"}}

# New output per visual:
{"url": "https://image.pollinations.ai/prompt/...", "headline": "...", "imagePrompt": "..."}
```

### 3.2 Follow-Up Endpoint (from prior session)

- [explanation.py](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/src/api/routes/explanation.py) — Added `POST /api/explain/followup`
- [explanation_controller.py](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/src/api/controllers/explanation_controller.py) — Added `process_followup()` method
- [types.py](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/src/shared/types.py) — Added `FollowUpRequest` Pydantic model

---

## 4. Changes Made — Frontend

### 4.1 VisualDisplay — Text Cards → AI Images

#### [VisualDisplay.jsx](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/VisualDisplay/VisualDisplay.jsx) — Complete Rewrite (194 lines)

**Before:** Rendered Gemini text cards as animated glassmorphism slides with headline, bullet points, emoji flow, and analogy sections.

**After:** Renders real AI-generated images from Pollinations.ai URLs with:

| Feature | Implementation |
|---|---|
| **Loading shimmer** | Animated gradient background while Pollinations generates the image (5-30s on first request) |
| **Retry logic** | Up to 3 retries with cache-busting (`&_retry=N&_t=timestamp`), delays of 3s/6s/9s |
| **Error fallback** | Gradient background + headline text + prompt excerpt (not a broken icon) |
| **Pre-loading** | `new window.Image()` preloads the NEXT segment's image in background |
| **Headline overlay** | Gradient overlay at bottom of image with white headline text |
| **Segment badge** | Numbered circle in top-right corner |
| **Ken Burns effect** | Subtle 20s zoom cycle on loaded images |
| **`allVisuals` prop** | Receives all segment visuals for pre-loading logic |

#### [VisualDisplay.css](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/VisualDisplay/VisualDisplay.css) — Complete Rewrite (233 lines)

- 16:9 `aspect-ratio` image wrapper with `border-radius` and `box-shadow`
- Shimmer animation (`background-size: 200% 200%` with gradient shift)
- Spinner rotation keyframe
- Gradient headline overlay (`linear-gradient(to top, rgba(0,0,0,0.75), transparent)`)
- Error fallback with centered layout
- Narration text panel below image with glassmorphism

### 4.2 LandingPage — Emojis → Lucide Icons

#### [LandingPage.jsx](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/LandingPage/LandingPage.jsx) — Rewritten (287 lines)

**All emoji replacements:**

| Location | Before (Emoji) | After (Lucide) |
|---|---|---|
| CTA button | ✨ | `<Sparkles>` |
| See How link | → | `<ChevronRight>` |
| Float card 1 | 🧠 | `<Brain>` |
| Float card 2 | 🎙️ | `<Mic>` |
| Float card 3 | 🎨 | `<Image>` |
| Pipeline step 1 | 🧠 | `<Brain>` |
| Pipeline step 2 | 🎨 | `<Image>` |
| Pipeline step 3 | 🎙️ | `<Mic>` |
| Pipeline step 4 | ⚡ | `<Activity>` |
| Feature: Narration | 🎭 | `<Brain>` |
| Feature: Visuals | 🖼️ | `<Image>` |
| Feature: Voice | 🔊 | `<Mic>` |
| Feature: Playback | 🔄 | `<RefreshCw>` |
| Feature: Responsive | 📱 | `<Smartphone>` |
| Feature: Fast | ⚡ | `<Zap>` |

#### [LandingPage.css](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/LandingPage/LandingPage.css) — Updated

- Added `.landing__float-icon` styles for Lucide SVG icons in float cards
- Replaced `.landing__step-icon` (emoji) with `.landing__step-icon-wrap` (flexbox container for Lucide icon, 44×44px with background)
- Replaced `.landing__feature-icon` (emoji block) with `.landing__feature-icon-wrap` (48×48px container with purple tint background)

### 4.3 LoadingView — Pipeline Steps + Lucide Icons

#### [LoadingView.jsx](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/LoadingView/LoadingView.jsx) — Rewritten (163 lines)

**Before:** Rotating carousel of 5 messages with emoji icons, cycling every 4 seconds. Progress dots at bottom.

**After:** Step-by-step pipeline progress showing each backend engine:

| Step | Text | Icon (Lucide) | Simulated Duration |
|---|---|---|---|
| 1 | Analyzing your content | `<BookOpen>` | 3s |
| 2 | Crafting story-driven narration | `<PenLine>` | 12s |
| 3 | Generating AI visuals | `<Image>` | 8s |
| 4 | Synthesizing natural voice | `<Mic>` | 6s |
| 5 | Synchronizing all components | `<Layers>` | 3s |
| 6 | Preparing your experience | `<Sparkles>` | 2s |

**Step states:**
- **Done** → Green `<CheckCircle2>` icon, opacity 0.6
- **Active** → Colored icon with animated `...` dots, highlighted background
- **Pending** → Muted icon, opacity 0.3

**Elapsed timer** at bottom: `"42s elapsed • Usually takes 30-60 seconds"`

#### [LoadingView.css](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/LoadingView/LoadingView.css) — Rewritten

- Removed `.loading-view__content`, `.loading-view__message`, `.loading-view__dots` (old carousel)
- Added `.loading-view__pipeline` (flex column, 320-420px width)
- Added `.loading-view__step` with `--done`, `--active`, `--pending` modifiers
- Added `.loading-view__step-done-icon` (green for `CheckCircle2`)
- Added `.loading-view__timer` (tabular-nums, purple accent)

### 4.4 DigitalHuman — TalkingHead.js 3D Avatar (NEW)

#### [DigitalHuman.jsx](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/DigitalHuman/DigitalHuman.jsx) — NEW (205 lines)

**Purpose:** Renders a Ready Player Me GLB 3D avatar via TalkingHead.js with real-time lip-sync from the backend audio.

**Implementation details:**

1. **Dynamic import** — TalkingHead imported from `src/vendor/talkinghead/` via `@talkinghead` alias to bypass Vite's public file restrictions
2. **Avatar URL** — Ready Player Me model: `https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb?morphTargets=ARKit,Oculus+Visemes&textureAtlas=1024`
3. **Camera config** — `cameraView: 'upper'`, `cameraDistance: 1.3`, good lighting
4. **Lip-sync flow:**
   - Receives `audioBase64` prop (base64 MP3 from backend)
   - Decodes to `ArrayBuffer` via `atob()` + `Uint8Array`
   - Calls `head.speakAudio(arrayBuffer, options, onEnd)`
   - TalkingHead internally runs audio analysis → drives mouth visemes
5. **De-duplication** — `lastAudioRef` prevents re-triggering `speakAudio` for the same audio
6. **States:** `idle → loading (with progress bar) → ready → error`
7. **Cleanup** — Calls `head.stopSpeaking()` and `head.dispose()` on unmount

#### [DigitalHuman.css](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/DigitalHuman/DigitalHuman.css) — NEW (119 lines)

- 180×240px card with `border-radius`, `box-shadow`, glassmorphism border
- Three.js canvas fills container, fades in on ready
- Loading overlay with circular placeholder (dashed border + `<User2>` icon)
- Animated progress bar with gradient fill
- Error state with `<AlertCircle>` and hint text
- Responsive: 140×185px on mobile

### 4.5 PlaybackView Updates

#### [PlaybackView.jsx](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/src/components/PlaybackView/PlaybackView.jsx) — Updated

**Change 1:** Replaced `Avatar` import with `DigitalHuman`:
```diff
-import Avatar from '../Avatar/Avatar.jsx';
+import DigitalHuman from '../DigitalHuman/DigitalHuman.jsx';
```

**Change 2:** Replaced Avatar component usage:
```diff
-<Avatar shouldAnimate={...} animationSpeed={...} scaleFactor={...} intensity={...} playbackSpeed={...} />
+<DigitalHuman audioBase64={response?.audio} isPlaying={isPlaying} />
```

**Change 3:** Added `allVisuals` prop to VisualDisplay:
```diff
-<VisualDisplay visual={currentVisual} segmentText={...} segmentIndex={...} />
+<VisualDisplay visual={currentVisual} segmentText={...} segmentIndex={...} allVisuals={response?.segments?.map(s => s.visual)} />
```

### 4.6 Vite Configuration

#### [vite.config.js](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-frontend/vite.config.js) — Rewritten (33 lines)

```javascript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@talkinghead': path.resolve(__dirname, 'src/vendor/talkinghead'),
    },
  },
  optimizeDeps: {
    exclude: ['@met4citizen/talkinghead'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'framer': ['framer-motion'],
          'lucide': ['lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
})
```

---

## 5. New Files Created

| File | Lines | Purpose |
|---|---|---|
| `src/components/DigitalHuman/DigitalHuman.jsx` | 205 | TalkingHead.js 3D avatar with lip-sync |
| `src/components/DigitalHuman/DigitalHuman.css` | 119 | Avatar card styling |
| `src/vendor/talkinghead/*.mjs` (8 files) | ~50K+ | TalkingHead.js runtime modules (copied from node_modules) |
| `public/talkinghead/*.mjs` (8 files) | ~50K+ | TalkingHead.js static copies (created during debugging, still present) |

---

## 6. Files Modified

| File | Type | Change Summary |
|---|---|---|
| `conversai-backend/src/engines/visual/planner.py` | **Rewritten** | Gemini image prompts + Pollinations URLs + pre-warming |
| `conversai-backend/src/engines/visual/generator.py` | **Rewritten** | Visual objects now carry real image URLs |
| `conversai-frontend/src/components/VisualDisplay/VisualDisplay.jsx` | **Rewritten** | Image rendering with retry, pre-load, error fallback |
| `conversai-frontend/src/components/VisualDisplay/VisualDisplay.css` | **Rewritten** | 16:9 image layout, shimmer, overlay styles |
| `conversai-frontend/src/components/LandingPage/LandingPage.jsx` | **Rewritten** | All emojis → Lucide icons |
| `conversai-frontend/src/components/LandingPage/LandingPage.css` | **Updated** | Icon wrapper styles |
| `conversai-frontend/src/components/LoadingView/LoadingView.jsx` | **Rewritten** | Pipeline steps + Lucide + timer |
| `conversai-frontend/src/components/LoadingView/LoadingView.css` | **Rewritten** | Pipeline step layout + icon styles |
| `conversai-frontend/src/components/PlaybackView/PlaybackView.jsx` | **Updated** | Avatar→DigitalHuman, allVisuals prop |
| `conversai-frontend/vite.config.js` | **Rewritten** | @talkinghead alias, optimizeDeps |

---

## 7. Packages Installed

| Package | Source | Purpose |
|---|---|---|
| `lucide-react` | npm | Professional SVG icon library (replaced all emojis) |
| `@met4citizen/talkinghead` | GitHub (`met4citizen/TalkingHead`) | 3D avatar with lip-sync via Three.js WebGL |

---

## 8. Debugging & Issue Resolution

### 8.1 "Visual unavailable" — Images Failing

**Symptom:** Playback view showed "Visual unavailable" error icon instead of AI images.

**Root causes identified:**
1. Pollinations.ai takes 5-30 seconds to generate images on first request — the browser `<img>` tag was timing out
2. No retry mechanism — any network hiccup = permanent failure
3. `nologo=true` parameter was unnecessary and could cause issues
4. No pre-warming — images weren't generated until the browser requested them

**Fixes applied:**
- Added 3-retry mechanism with exponential delay (3s, 6s, 9s) and cache-busting query params
- Added backend pre-warming: all Pollinations URLs requested concurrently via `asyncio.gather()` during audio synthesis
- Removed `nologo=true` from all URL construction
- Added `crossOrigin="anonymous"` and `loading="eager"` to `<img>` tag
- Added pre-loading of next segment's image via `new window.Image()`
- Added rich error fallback (gradient + headline text) instead of bare error icon

### 8.2 "Avatar unavailable" — TalkingHead.js Import Failures

**Symptom:** Avatar area showed "Avatar unavailable" error immediately.

**Root cause:** Vite's `vite:import-analysis` plugin blocks any `import()` of JavaScript files from `/public/`. Error: *"Cannot import non-asset file /talkinghead/talkinghead.mjs which is inside /public."*

**Attempted fixes (chronological):**

| Attempt | Approach | Result |
|---|---|---|
| 1 | `import('@met4citizen/talkinghead/modules/talkinghead.mjs')` | Failed — lipsync-en.mjs not found in .vite/deps/ |
| 2 | `optimizeDeps.exclude` in vite.config.js | Fixed bundling, but lipsync module still not resolved |
| 3 | Copy files to `public/talkinghead/` + `import('/talkinghead/talkinghead.mjs')` | Blocked by Vite: "Cannot import non-asset file from /public" |
| 4 | `import(/* @vite-ignore */ '/talkinghead/talkinghead.mjs')` | Still blocked — Vite checks path at transform time |
| 5 | `window.location.origin + '/talkinghead/talkinghead.mjs'` | Still blocked — Vite's static analysis sees the path |
| 6 | `new Function('url', 'return import(url)')` | Bypassed Vite's AST analysis but still errored on cached transform |
| 7 | Copy to `src/vendor/talkinghead/` + relative import | Vite couldn't resolve the relative .mjs path |
| **8 ✅** | `src/vendor/talkinghead/` + `@talkinghead` Vite alias | **Works** — alias resolves to correct path, `@vite-ignore` on dynamic import |

**Final working solution:**
```javascript
// vite.config.js
resolve: { alias: { '@talkinghead': path.resolve(__dirname, 'src/vendor/talkinghead') } }

// DigitalHuman.jsx
const { TalkingHead } = await import(/* @vite-ignore */ '@talkinghead/talkinghead.mjs');
```

**Verification:** `curl http://localhost:5173/src/vendor/talkinghead/talkinghead.mjs` returns HTTP 200 with `text/javascript`. Same for `lipsync-en.mjs`.

---

## 9. Architecture Decisions

### 9.1 Why Pollinations.ai for Images

| Alternative | Why Not |
|---|---|
| Stable Diffusion XL (local) | 15-40s per image, requires GPU, heavy dependencies |
| DALL-E / Midjourney API | Costs money — user requirement was zero cost |
| Gemini Imagen | Not free / not available in free tier |
| **Pollinations.ai** ✅ | Free, no API key, URL-based, CDN-cached, 1280×720, CORS enabled |

### 9.2 Why TalkingHead.js for Avatar

| Alternative | Why Not |
|---|---|
| CSS animations (existing Avatar) | Not a real 3D model, no lip-sync, looks amateur |
| D-ID / HeyGen | Paid APIs, requires subscription |
| Custom Three.js + Viseme mapping | Too much work, reinventing the wheel |
| **TalkingHead.js** ✅ | Free, open source, Ready Player Me GLB models, built-in lip-sync, idle animations |

### 9.3 Why Lucide React for Icons

| Alternative | Why Not |
|---|---|
| Emojis | Unprofessional, inconsistent across platforms, can't style |
| Font Awesome | Heavier bundle, license complexity |
| Heroicons | Fewer icons, less maintained |
| **Lucide React** ✅ | 1000+ icons, tree-shakeable, customizable size/color/strokeWidth, MIT license |

### 9.4 Backend Pre-warming Strategy

The pre-warming fires **concurrently** with `asyncio.gather()` — all 6 image URLs are requested simultaneously. Each GET request triggers Pollinations to generate the image and cache it on their CDN. By the time the frontend loads the PlaybackView (after audio synthesis), most images are already cached and load instantly.

```
Timeline:
  t=0    Gemini prompt generation starts
  t=10   Prompts ready, Pollinations URLs built
  t=10   Pre-warming starts (all 6 URLs concurrent)  ←── NEW
  t=10   Audio synthesis starts (parallel)
  t=35   Pre-warming completes (images now cached)
  t=40   Audio synthesis completes
  t=40   Response sent to frontend
  t=40   Frontend renders <img> → images load INSTANTLY from CDN cache
```

---

## 10. Final System State

### Backend API Response Structure

```json
{
  "segments": [
    {
      "id": "segment_1",
      "text": "Narration text...",
      "startTime": 0,
      "endTime": 12.8,
      "visual": {
        "url": "https://image.pollinations.ai/prompt/...",
        "headline": "The Digital Ledger Revolution",
        "imagePrompt": "A massive holographic ledger floating...",
        "style": "cinematic",
        "startTime": 0,
        "endTime": 12.8,
        "type": "abstract_concept",
        "metadata": {
          "segmentId": "segment_1",
          "concept": "blockchain",
          "generationMethod": "pollinations_ai"
        }
      }
    }
  ],
  "audio": "base64_mp3_string...",
  "avatar": { "states": [...] },
  "narration": "Full narration text...",
  "metadata": { "concepts": [...], "difficulty": "intermediate" }
}
```

### Frontend Component Tree

```
App.jsx
├── LandingPage (Lucide icons, premium CTA)
├── InputSection (voice mic + textarea)
├── LoadingView (pipeline steps + timer)
└── PlaybackView
    ├── VisualDisplay (Pollinations images + headline overlay)
    ├── DigitalHuman (TalkingHead.js 3D avatar + lip-sync)
    ├── Controls (play/pause, seek, speed)
    └── FollowUp input bar
```

### Servers

| Service | URL | Status |
|---|---|---|
| Backend (FastAPI + Uvicorn) | `http://localhost:8000` | Running with --reload |
| Frontend (Vite dev) | `http://localhost:5173` | Running |

---

## 11. Remaining Work

1. **End-to-end browser test** — Verify images load with shimmer→image transition and avatar loads with progress bar
2. **Black Book documentation** — User will provide headings, agent provides content
3. **Final UI polish** — Micro-interactions, transitions between states
4. **Production build test** — `npm run build` to ensure everything bundles correctly
5. **Avatar fallback** — If TalkingHead fails to load GLB, show the old CSS Avatar as graceful degradation
