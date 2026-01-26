# 📘 ConversAI
### A Multimodal AI Platform for Story-Driven Understanding of Text

---

## 🚨 Problem Statement

Students and learners frequently encounter long, text-heavy content such as articles, blogs, PDFs, documentation, and AI-generated responses.  
Although these sources contain valuable information, users often skim or disengage due to cognitive overload, resulting in poor understanding.

Most existing AI tools still respond primarily with dense text, which does not effectively solve this problem.

---

## 💡 Solution

**ConversAI** addresses this gap by transforming complex text into:

- 🎙️ **Narrated explanations** (human-like voice)
- 📖 **Story-driven structure** (clear, logical flow)
- 🖼️ **Supporting visuals** (to reinforce understanding)
- 🧍 **Optional digital narrator (avatar)** for enhanced engagement

The goal is not to explain *everything*, but to help users **quickly grasp the core ideas** in a natural and engaging way.

---

## 🎯 V1 Scope (MVP)

ConversAI V1 focuses on solving **one problem extremely well**.

### ✅ What V1 Supports
- Paste text-heavy content for explanation
- Optional user instruction (e.g. *"Explain like I’m a beginner"*)
- Select explanation duration (short / medium)
- Select narration style
- AI-generated voice narration
- AI-generated supporting visuals
- Optional lightweight digital narrator (avatar)
- Follow-up questions after explanation

### ❌ What V1 Intentionally Does NOT Include
- PDF or document uploads
- User authentication or accounts
- Browser extensions
- Real-time interactive video calls

These features are planned for future versions once the core explanation engine is mature.

---

## 🧠 System Design Overview

ConversAI follows a **layered, backend-orchestrated architecture**:

- **Web UI** – User interaction and explanation playback
- **Backend API** – Central orchestration layer
- **Explanation Engine** – Analyzes and restructures text into narrated explanations
- **Visual Planning & Generation Engine** – Generates visuals aligned with narration segments
- **Voice & Avatar Engine** – Produces audio narration and optional avatar
- **Aggregation Engine** – Composes all outputs into a unified multimodal experience

The backend controls the entire flow, enabling clean separation of concerns and future scalability.

---

## 🏗️ Architecture Principles

- Modular monolith (not microservices)
- Backend-orchestrated AI pipeline
- Parallel generation of audio and visuals
- Open-source & free technologies only
- Designed for scalability without premature overengineering

---

## 🛠️ Tech Stack (V1)

- **Frontend:** React  
- **Backend:** Python + FastAPI  
- **LLM:** Gemini Pro (Free Tier)  
- **Image Generation:** Open-source image models  
- **Text-to-Speech:** Open-source TTS  

### 🚀 Deployment
- **Frontend:** Vercel  
- **Backend:** Render  
- **Repository:** GitHub (Monorepo)

---

## 🤝 Collaboration & Development

This project is collaboratively built by:
- **Ishaan Gujaran**
- **Shivani Singh**

Development follows:
- Shared ownership
- Rotating implementation & review roles
- Clean, meaningful Git commits
- Industry-style Git workflow (`main`, `dev`, feature branches)

---

## 📌 Vision

ConversAI aims to evolve into a general-purpose **explanation layer for the web**, where any text-heavy content can be transformed into an interactive, human-like explanation experience.

---

## 📄 License

This project solely belongs to Shivani & Ishaan and is intended for learning, experimentation, and demonstration of real-world GenAI system design.
