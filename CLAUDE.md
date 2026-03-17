# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiroFish-Offline is a multi-agent swarm intelligence engine that simulates public opinion, market sentiment, and social dynamics. It's an English-language fork of the original MiroFish. Supports both local infrastructure (Neo4j CE + Ollama) and cloud providers (OpenAI + Neo4j Aura).

## Commands

```bash
# Full stack (Docker - recommended for local)
docker compose up -d

# Development (concurrent backend + frontend)
npm run dev

# Backend only
cd backend && uv sync && python run.py

# Frontend only
cd frontend && npm install && npm run dev

# Build frontend for production
npm run build

# Tests
cd backend && pip install -e ".[dev]" && pytest
```

**Ports:** Flask backend `:5001`, Vite dev server `:3000`, Neo4j Browser `:7474`, Neo4j Bolt `:7687`, Ollama `:11434`

## Architecture

**5-step pipeline:** Graph Build → Environment Setup (agent personas) → Simulation (multi-round social platform) → Report Generation → Agent Interaction

**Layered backend:**
- `backend/app/api/` — Flask REST endpoints (graph.py, simulation.py, report.py)
- `backend/app/services/` — Business logic (GraphBuilderService, SimulationManager, ReportAgent, OasisProfileGenerator, EntityReader)
- `backend/app/storage/` — Abstract `GraphStorage` interface with `Neo4jStorage` implementation. Includes `EmbeddingService` (auto-detects Ollama vs OpenAI from URL), `NERExtractor`, `SearchService` (hybrid: 0.7 vector + 0.3 BM25)
- `backend/app/models/` — Server-side state: `ProjectContext` (persisted to `backend/uploads/projects/`), `TaskManager` (in-memory, thread-safe)
- `backend/app/utils/` — `llm_client.py` (OpenAI SDK wrapper), `file_parser.py` (PDF/MD/TXT via PyMuPDF)

**Dependency injection:** `Neo4jStorage` is initialized once in the Flask app factory (`app/__init__.py`) and accessed via `app.extensions['neo4j_storage']`.

**Frontend:** Vue 3 SPA with step-based workflow components (`Step1GraphBuild.vue` through `Step5Interaction.vue`), D3.js graph visualization (`GraphPanel.vue`), Axios API clients mirroring backend routes.

## Tech Stack

- **Backend:** Flask 3.0+, Python 3.11 (3.12+ has camel-ai compatibility issues), CAMEL-AI 0.2.78 + camel-oasis 0.2.5
- **Frontend:** Vue 3.5+, Vite 7.2+, D3.js 7.9+
- **Local infra:** Neo4j 5.15 CE, Ollama, Docker Compose
- **Cloud infra:** Neo4j Aura, OpenAI API (or any OpenAI-compatible provider)

## Key Design Decisions

- `GraphStorage` is abstract — Neo4j can be swapped by implementing one class
- LLM access uses OpenAI SDK — works with any OpenAI-compatible API (Ollama, OpenAI, etc.)
- `EmbeddingService` auto-detects backend from URL: Ollama (`/api/embed`) vs OpenAI (`/v1/embeddings`)
- Neo4j vector index dimensions are configured from the embedding model (768 for nomic, 1536 for text-embedding-3-small)
- NER/relation extraction runs synchronously via LLM prompts
- Project state persists server-side to reduce frontend-backend data transfer
- The simulation layer uses CAMEL-AI's OASIS framework for agent-based social simulation
- Simulation scripts run as subprocesses — they load `.env` and `.env.local` independently

## Configuration

Config loads from `.env` (copy from `.env.example`). Create `.env.local` to override with cloud settings — it takes precedence and is git-ignored.

Key variables: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `NEO4J_URI`, `NEO4J_PASSWORD`, `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`, `EMBEDDING_DIMENSIONS`, `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`.
