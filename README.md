# ConversAI

ConversAI is a multimodal AI platform that transforms text into an **educational experience** featuring AI-generated cinematic visuals, neural voice narration, and a dynamic Lottie-based avatar.

## 🌟 Key Features

- **Lottie Avatar**: Dynamic 2D Lottie animations with distinct states for speaking and idle.
- **Cinematic AI Visuals**: Automatically planned and generated images via `Pollinations.ai` (16:9 aspect ratio).
- **Neural Voice Narration**: High-quality TTS powered by `gTTS` / `edge-tts`.
- **Advanced Observability**: Fully instrumented backend pipeline with SQLite telemetry and hybrid artifact storage.
- **Premium Glassmorphism UI**: Beautiful, fully responsive React frontend with a dark/light mode Theme Toggle.

## 🏗️ Project Structure

The repository is structured as a monorepo containing both the frontend and backend applications:

- [`/conversai-frontend`](./conversai-frontend) — The React/Vite frontend application.
- [`/conversai-backend`](./conversai-backend) — The Python/FastAPI backend application.
- [`/docs`](./docs) — Technical design documents, architecture specs, and deployment guides.

## 🚀 Live Demo

- **Frontend**: Deployed on **Vercel**
- **Backend**: Deployed on **Render** (Dockerized)

*(Add your live URLs here!)*

## 📚 Documentation

For deep-dive documentation on how this system is built and deployed, please refer to our `/docs` folder:

- **[Deployment Guide](./docs/DEPLOYMENT.md)** - Full instructions for deploying to Vercel and Render.
- **[Architecture & Engine Specs](./docs/)** - Design documents for the Explanation, Visual, Voice & Avatar, and Aggregation engines.
- **[Observability Guide](./docs/OBSERVABILITY_GUIDE.md)** - Learn about the fail-safe SQLite telemetry system.

## 🛠️ Local Development

### 1. Start the Backend

```bash
cd conversai-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 2. Start the Frontend

```bash
cd conversai-frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.
