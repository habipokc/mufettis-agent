# Müfettiş Agent 🕵️‍♂️📜

**AI-Powered Regulatory Assistant for Turkish Banking & Finance**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-purple)
![LangChain](https://img.shields.io/badge/LangChain-Framework-green)
![Docling](https://img.shields.io/badge/Docling-PDF_Parser-orange)

**Müfettiş Agent** is a specialized RAG (Retrieval-Augmented Generation) application designed to assist auditors and banking professionals in navigating the complex landscape of Turkish Banking Laws and Regulations. 

Built with **LangGraph**, **FastAPI**, and **Next.js**, it combines hybrid search retrieval (BM25 + Semantic) with the reasoning capabilities of **Google Gemini 2.0 Flash** to provide accurate, citation-backed answers.

---

## 🚀 Live Demo

Try the agent directly in your browser!
**👉 [https://mufettis-agent.com.tr/](https://mufettis-agent.com.tr/)**

> **Note:** This is a "Bring Your Own Key" (BYOK) application. You will need a Google Gemini API Key to use the live demo. The key is stored locally in your browser and never saved to our servers.

---

## ✨ Features

- **🔍 Hybrid Retrieval System:** Combines **ChromaDB** (Semantic Search) and **BM25** (Keyword Search) for high-precision document retrieval.
- **📄 Smart Document Parsing:** Utilizes **Docling** for high-fidelity PDF parsing, preserving document structure (headers, tables, lists) to create semantically meaningful chunks.
- **🧠 Advanced Reranking:** Uses `Cross-Encoder` models to re-rank search results, ensuring the most relevant legislation is prioritized.
- **🤖 Agentic Workflow:** Powered by **LangGraph**, the system intelligently routes queries between "Chitchat" (Instant response) and "Regulatory Search" (Deep retrieval).
- **⚡ Dynamic Model Support:** Users can plug in their own Gemini API Key to access state-of-the-art models like **Gemini 2.0 Flash**.
- **🇹🇷 Specialized Domain:** Pre-indexed with thousands of pages of Turkish Banking Law (5411), Capital Markets Law, and BDDK regulations.
- **🐳 Dockerized Deployment:** Full stack containerization for easy deployment on AWS, Google Cloud, or on-premise servers.

---

## 🛠️ Tech Stack

### Data Processing & RAG
- **PDF Parsing:** **Docling** (IBM) - Extracts structured text from complex PDFs.
- **Chunking Strategy:** Semantic chunking based on document headers and layout.
- **Vector Database:** ChromaDB (Persistent)
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`

### Backend
- **Framework:** FastAPI (Python)
- **Agent Orchestration:** 
  - **LangChain:** Handles prompt management, model interfacing (`ChatGoogleGenerativeAI`), and RAG components.
  - **LangGraph:** Manages the agent's state (`AgentState`), strictly defines the cyclic workflow, and routes queries between specific nodes (`router`, `chitchat`, `retrieval`).
- **LLM:** Google Gemini 2.0 Flash / 2.5 Flash
- **Dependency Management:** Poetry

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS & Glassmorphism UI
- **State Management:** React Hooks & LocalStorage (for API Keys)

### DevOps
- **Containerization:** Docker & Docker Compose
- **Cloud Provider:** AWS Lightsail (Ubuntu 22.04 LTS)
- **Web Server:** Nginx (Reverse Proxy)

---

## 🏎️ Local Installation

Follow these steps to run Müfettiş Agent on your local machine.

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/mufettis-agent.git
cd mufettis-agent
```

### 2. Setup Environment Variables
Create a `.env` file in the root directory:
```bash
GEMINI_API_KEY=your_backup_api_key_here
```

### 3. Run with Docker Compose
The easiest way to start the full stack:
```bash
docker-compose up --build
```
- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:3000

---

## 🔧 Manual Development Setup

If you prefer running services individually for development:

### Backend (Python)
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

### Frontend (Node.js)
```bash
cd frontend
# Create local env override
echo "BACKEND_URL=http://127.0.0.1:8000" > .env.local
npm install
npm run dev
```

---

## 📂 Project Structure

```
mufettis-agent/
├── backend/
│   ├── app/
│   │   ├── agent/       # LangGraph Agent Logic
│   │   ├── api/         # FastAPI Endpoints
│   │   ├── services/    # RAG & Retrieval Service
│   │   └── core/        # Config & Utils
│   └── poetry.lock
├── frontend/
│   ├── app/             # Next.js Pages
│   └── components/      # UI Components
├── data/                # Vector DB & Raw Data
├── mevzuat/             # Source PDF Documents
├── docker-compose.yml   # Production Orchestration
└── Dockerfile           # Backend Image
```

---

## 🛡️ Privacy & Security

- **API Keys:** User provided keys are stored exclusively in the browser's `localStorage`. They are sent to the backend via secure HTTP headers for a single session and are discarded from server memory immediately after use.
- **Data:** This project uses publicly available legislation data. No sensitive user data is stored.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ for the Turkish Finance Community
</p>
