# ConversAI Frontend

A polished, production-grade frontend for ConversAI — transforming text into a **Digital Human experience** with AI-generated cinematic visuals, neural voice narration, and a real-time 3D lip-synced avatar.

## Features

- 🎨 **Premium Dark Theme** — Glassmorphism UI with CSS Variables design system
- 🎵 **Neural Voice Playback** — Synchronized narration via edge-tts (Microsoft AriaNeural)
- 🖼️ **AI-Generated Visuals** — Pollinations.ai cinematic images (1280×720, 16:9) per segment
- 🤖 **3D Digital Human** — TalkingHead.js + Ready Player Me GLB avatar with real-time lip-sync
- ⏯️ **Playback Controls** — Play/pause, seek, replay functionality
- 🎤 **Voice Input** — Web Speech API mic button for hands-free text input
- 💬 **Follow-Up Q&A** — Ask follow-up questions after each explanation
- 🌙 **Theme Toggle** — Light/Dark mode with localStorage persistence
- 📱 **Responsive Design** — Works on desktop and mobile

## Tech Stack

- **React** (with Vite)
- **Framer Motion** — Page and component animations
- **TalkingHead.js** (`@met4citizen/talkinghead`) — 3D WebGL avatar with lip-sync
- **Lucide React** — Professional SVG icon library (replaces emoji icons)
- **Vanilla CSS + CSS Variables** — Custom design system, no CSS framework

## Quick Start

### Prerequisites

- Node.js 18+
- npm
- ConversAI Backend running locally (`uvicorn src.main:app --reload` on port 8000)

### Installation

```bash
# Navigate to frontend directory
cd conversai-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173/`

### Environment Variables

Create a `.env.local` file (optional — defaults to localhost:8000):

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/
│   ├── LandingPage/        # Hero page with pipeline diagram, stats, CTAs
│   ├── InputSection/       # Text input + voice mic + preferences
│   ├── LoadingView/        # Pipeline step progress (with Lucide icons + timer)
│   ├── PlaybackView/       # Main playback layout
│   ├── VisualDisplay/      # AI image display (Pollinations.ai, 16:9, retry logic)
│   ├── DigitalHuman/       # TalkingHead.js 3D avatar with lip-sync
│   ├── Avatar/             # Legacy CSS avatar (kept for fallback)
│   ├── Controls/           # Play/pause, seek, time display
│   ├── Navbar/             # Navigation bar
│   ├── Header/             # App header
│   ├── ThemeToggle/        # Light/dark mode toggle
│   ├── HistoryView/        # Session history
│   └── ErrorView/          # Error handling UI
├── hooks/
│   ├── useAudio.js         # HTML5 Audio API wrapper
│   ├── useSegmentSync.js   # Maps currentTime → active segment/visual
│   ├── useAvatarSync.js    # Derives avatar state from timeline
│   ├── usePlayback.js      # Combined playback orchestrator
│   └── useSpeechRecognition.js  # Web Speech API mic input
├── context/
│   └── ThemeContext.jsx    # Light/dark theme with localStorage
├── services/
│   └── api.js              # Backend API client (explain + followup)
├── styles/
│   ├── variables.css       # Design tokens (colors, spacing, typography)
│   ├── typography.css      # Font styles (Outfit + Inter from Google Fonts)
│   └── animations.css      # CSS keyframe definitions
├── utils/
│   └── history.js          # Session history management
├── vendor/
│   └── talkinghead/        # TalkingHead.js modules (served as ES modules)
│       ├── talkinghead.mjs
│       ├── lipsync-en.mjs
│       ├── dynamicbones.mjs
│       └── retargeter.mjs
├── App.jsx                 # Main app + state machine (LANDING→INPUT→LOADING→PLAYBACK)
└── main.jsx                # Entry point
```

## Component Overview

### LandingPage
Premium hero page with:
- Animated headline + floating visual cards
- Stats row (segments, voice, images per explanation)
- Pipeline diagram (Lucide icons: Brain → Image → Mic → Activity)
- Features grid (6 features with Lucide icons, no emoji)
- Framer Motion entrance animations

### LoadingView
Step-by-step pipeline progress:
- 6 named steps with Lucide icons (BookOpen, PenLine, Image, Mic, Layers, Sparkles)
- Each step shows: pending (muted) → active (highlighted, animated dots) → done (green CheckCircle2)
- Elapsed timer: `"42s elapsed • Usually takes 30-60 seconds"`

### VisualDisplay
AI image display with:
- Shimmer loading state (animated gradient) while Pollinations generates
- 3 retries with cache-busting on failure (delays: 3s, 6s, 9s)
- Headline overlay (gradient at bottom of image)
- Ken Burns zoom effect on loaded images
- Rich error fallback (gradient + headline + prompt excerpt)
- Pre-loads next segment's image in background

### DigitalHuman
TalkingHead.js 3D avatar:
- Loads TalkingHead from `src/vendor/talkinghead/` via Vite alias `@talkinghead`
- Ready Player Me GLB model with ARKit + Oculus Viseme morph targets
- Loading progress bar (0-100%) while GLB downloads
- Drives lip-sync: `head.speakAudio(audioArrayBuffer, options, onEnd)`
- De-duplication guard: won't re-trigger same audio twice
- Error state with hint text if initialization fails

### Controls
Media-style controls:
- Play/Pause toggle
- Replay button
- Seekable progress bar with segment markers
- Time display (`currentTime / duration`)

## Hooks

### useAudio
HTML5 Audio API wrapper:
```javascript
const { isPlaying, currentTime, duration, toggle, seek, replay } = useAudio(audioSrc);
```

### useSegmentSync
Maps currentTime to active segment and visual:
```javascript
const { currentSegment, currentVisual, segmentProgress } = useSegmentSync(segments, currentTime);
```

### useAvatarSync
Derives avatar animation state from avatar metadata:
```javascript
const { shouldAnimate, animationSpeed, scaleFactor, intensity } = useAvatarSync(avatarData, currentTime, isPlaying);
```

### useSpeechRecognition
Web Speech API mic input:
```javascript
const { transcript, isListening, startListening, stopListening } = useSpeechRecognition();
```

## API Integration

The frontend expects the backend to return:

```typescript
{
  narration: string;
  segments: Array<{
    id: string;
    text: string;
    startTime: number;
    endTime: number;
    visual: {
      url: string;          // Pollinations.ai CDN URL
      headline: string;     // Short overlay text
      imagePrompt: string;  // Full Gemini-generated prompt
      type: string;
      startTime: number;
      endTime: number;
      metadata: { segmentId: string; generationMethod: string };
    } | null;
  }>;
  audio: string;            // Raw base64 MP3 (no data: URI prefix)
  audioDuration: number;
  avatar: {
    states: Array<{ startTime: number; endTime: number; state: string; intensity: string }>;
    cues: Array<{ timestamp: number; cueType: string; metadata: object }>;
  } | null;
  metadata: { duration: number; segmentCount: number; hasAvatar: boolean };
}
```

## Vite Configuration

`vite.config.js` includes:

```javascript
resolve: {
  alias: {
    // Points to src/vendor/talkinghead/ — needed because TalkingHead.js
    // uses dynamic internal imports that Vite can't statically bundle
    '@talkinghead': path.resolve(__dirname, 'src/vendor/talkinghead'),
  }
}
```

The TalkingHead modules are copied to `src/vendor/talkinghead/` (not node_modules) and served as raw ES modules via Vite. The `@vite-ignore` comment on the dynamic import prevents Vite's import-analysis plugin from blocking it.

## Design System

### Colors
- Primary: `hsl(265, 80%, 60%)` (Violet)
- Background: `#0a0a0f` (Deep dark)
- Surface: `rgba(255,255,255,0.04)` (Glassmorphism card)
- Text: `#f5f5f7` (Off-white)
- Muted: `#8b8b9a`

### Typography
- Display: Outfit (Google Fonts)
- Body: Inter (Google Fonts)

### Animations
- Framer Motion for page transitions and component entry
- CSS keyframes for shimmer, spinner, Ken Burns zoom
- Lucide React icons (strokeWidth=1.5, consistent sizing)

## Development

```bash
# Start dev server (frontend only)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

> [!IMPORTANT]
> The backend must also be running: `uvicorn src.main:app --reload` (from `conversai-backend/`)

## License

MIT
