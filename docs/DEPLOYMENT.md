# ConversAI Deployment Guide

This document outlines the deployment strategy and detailed steps to deploy ConversAI into production.

## 🌍 Infrastructure Overview

ConversAI uses a decoupled deployment architecture:
- **Frontend**: Deployed as a static React app on **Vercel**.
- **Backend**: Deployed as a Dockerized FastAPI service on **Render**.

---

## 🎨 Frontend Deployment (Vercel)

The frontend is a Vite + React application. Vercel provides seamless, zero-config deployments for Vite apps.

### Prerequisites
- A GitHub repository containing the `conversai-frontend` code.
- A Vercel account.

### Deployment Steps
1. **Connect to Vercel**: Log into Vercel and click **Add New > Project**.
2. **Import Repository**: Select the GitHub repository containing ConversAI.
3. **Configure Project**:
   - **Framework Preset**: Vercel should auto-detect **Vite**.
   - **Root Directory**: Select `conversai-frontend`.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. **Environment Variables**:
   - `VITE_API_URL`: Set this to your deployed Render backend URL (e.g., `https://conversai-backend.onrender.com`).
5. **Deploy**: Click **Deploy**. Vercel will automatically build and publish the frontend.

---

## ⚙️ Backend Deployment (Render)

The backend is a FastAPI Python application. It is deployed using a `Dockerfile` to ensure environment consistency.

### Prerequisites
- A Render account.
- The `Dockerfile` located in the `conversai-backend` directory.

### Dockerfile Overview
The provided `Dockerfile` uses a lightweight `python:3.10-slim` image, prevents Python from buffering stdout/writing pyc files, and exposes port `8000`. It strictly respects the Render-provided `$PORT` environment variable via:
```dockerfile
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Deployment Steps
1. **Connect to Render**: Log into Render and click **New > Web Service**.
2. **Import Repository**: Select your GitHub repository.
3. **Configure Web Service**:
   - **Name**: `conversai-backend`
   - **Root Directory**: `conversai-backend`
   - **Environment**: Select **Docker**.
4. **Environment Variables**:
   - Render automatically injects the `PORT` variable.
   - `OBSERVABILITY_ENABLED`: `true` (Enable production telemetry)
   - `OBSERVABILITY_ARTIFACTS`: `false` (IMPORTANT: Disable heavy file/artifact disk writes on Render's ephemeral filesystem)
   - Add any AI/LLM API keys required by your explanation engine (e.g., `GEMINI_API_KEY`).
5. **Deploy**: Render will build the Docker image and deploy the container.

### Storage Considerations (SQLite)
ConversAI's backend uses a local SQLite database (`observability.db`) to record request telemetry. 
- **Ephemeral Storage**: By default, Render's Docker environments are ephemeral. When the server restarts, `observability.db` will be reset.
- **Persistent Storage (Optional)**: If you want to persist the SQLite telemetry database across deployments, you must attach a **Render Disk** to your Web Service and mount it to the `/app` directory, or update `DB_PATH` in `src/observability/database.py` to point to the mount path.

---

## 🔄 CI/CD & Updates

- **Frontend**: Any push to the `main` branch will automatically trigger a new Vercel deployment.
- **Backend**: If "Auto-Deploy" is enabled in Render, pushing to `main` will rebuild the Docker container and deploy the latest backend code. Ensure frontend's `VITE_API_URL` correctly points to the active Render URL.
