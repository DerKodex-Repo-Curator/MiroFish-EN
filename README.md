<div align="center">

<img src="./static/image/mirofish-offline-banner.png" alt="MiroFish Offline" width="100%"/>

# MiroFish-Offline

**English fork of [MiroFish](https://github.com/666ghj/MiroFish) — run fully local or with cloud APIs.**

*A multi-agent swarm intelligence engine that simulates public opinion, market sentiment, and social dynamics.*

[![GitHub Stars](https://img.shields.io/github/stars/nikmcfly/MiroFish-Offline?style=flat-square&color=DAA520)](https://github.com/nikmcfly/MiroFish-Offline/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/nikmcfly/MiroFish-Offline?style=flat-square)](https://github.com/nikmcfly/MiroFish-Offline/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](./LICENSE)

</div>

## What is this?

MiroFish is a multi-agent simulation engine: upload any document (press release, policy draft, financial report), and it generates hundreds of AI agents with unique personalities that simulate the public reaction on social media. Posts, arguments, opinion shifts — hour by hour.

The [original MiroFish](https://github.com/666ghj/MiroFish) was built for the Chinese market (Chinese UI, Zep Cloud for knowledge graphs, DashScope API). This fork makes it **fully English** and supports **both local and cloud** infrastructure:

| Original MiroFish | MiroFish-Offline |
|---|---|
| Chinese UI | **English UI** (1,000+ strings translated) |
| Zep Cloud (graph memory) | **Neo4j** (local CE 5.15 or Aura cloud) |
| DashScope / OpenAI API (LLM) | **Any OpenAI-compatible API** (Ollama, OpenAI, etc.) |
| Zep Cloud embeddings | **Ollama** (nomic-embed-text) or **OpenAI** (text-embedding-3-small) |

## Workflow

1. **Graph Build** — Extracts entities (people, companies, events) and relationships from your document. Builds a knowledge graph with individual and group memory via Neo4j.
2. **Env Setup** — Generates hundreds of agent personas, each with unique personality, opinion bias, reaction speed, influence level, and memory of past events.
3. **Simulation** — Agents interact on simulated social platforms: posting, replying, arguing, shifting opinions. The system tracks sentiment evolution, topic propagation, and influence dynamics in real time.
4. **Report** — A ReportAgent analyzes the post-simulation environment, interviews a focus group of agents, searches the knowledge graph for evidence, and generates a structured analysis.
5. **Interaction** — Chat with any agent from the simulated world. Ask them why they posted what they posted. Full memory and personality persists.

## Screenshot

<div align="center">
<img src="./static/image/mirofish-offline-screenshot.jpg" alt="MiroFish Offline — English UI" width="100%"/>
</div>

## Quick Start

Choose your path: **local** (everything on your hardware) or **cloud** (OpenAI + Neo4j Aura).

### Option A: Fully Local with Docker (easiest)

**Prerequisites:** Docker & Docker Compose, a GPU with 10+ GB VRAM (or CPU-only, slower).

```bash
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
cp .env.example .env

# Start all services (Neo4j, Ollama, MiroFish)
docker compose up -d

# Pull the required models into Ollama
docker exec mirofish-ollama ollama pull qwen2.5:32b
docker exec mirofish-ollama ollama pull nomic-embed-text
```

Open `http://localhost:3000` — that's it.

### Option B: Cloud APIs (no GPU needed)

**Prerequisites:** Python 3.11+, Node.js 18+, an OpenAI API key, a [Neo4j Aura](https://neo4j.com/cloud/aura-free/) instance.

```bash
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
cp .env.example .env
```

Create a `.env.local` file (git-ignored) to override the local defaults with cloud settings:

```bash
# LLM
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# Neo4j Aura
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password

# Embeddings (OpenAI)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_DIMENSIONS=1536

# CAMEL-AI (reads these directly)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE_URL=https://api.openai.com/v1
```

Then run:

```bash
cd backend
pip install -r requirements.txt
python run.py

# In another terminal:
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Option C: Manual Local (no Docker)

**Prerequisites:** Python 3.11+, Node.js 18+, Neo4j 5.15+, Ollama.

**1. Start Neo4j**

```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/mirofish \
  neo4j:5.15-community
```

**2. Start Ollama & pull models**

```bash
ollama serve &
ollama pull qwen2.5:32b      # LLM (or qwen2.5:14b for less VRAM)
ollama pull nomic-embed-text  # Embeddings (768d)
```

**3. Configure & run backend**

```bash
cp .env.example .env
# Edit .env if your Neo4j/Ollama are on non-default ports

cd backend
pip install -r requirements.txt
python run.py
```

**4. Run frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Configuration

Settings are loaded from `.env` (copy from `.env.example`). To override with cloud or custom settings, create a `.env.local` file in the project root — it takes precedence over `.env` and is git-ignored.

| Variable | Default (local) | Cloud example |
|---|---|---|
| `LLM_API_KEY` | `ollama` | `sk-...` |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | `https://api.openai.com/v1` |
| `LLM_MODEL_NAME` | `qwen2.5:32b` | `gpt-4o` |
| `NEO4J_URI` | `bolt://localhost:7687` | `neo4j+s://xxx.databases.neo4j.io` |
| `NEO4J_USER` | `neo4j` | `neo4j` |
| `NEO4J_PASSWORD` | `mirofish` | (from Aura dashboard) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | `text-embedding-3-small` |
| `EMBEDDING_BASE_URL` | `http://localhost:11434` | `https://api.openai.com/v1` |
| `EMBEDDING_DIMENSIONS` | `0` (auto-detect) | `1536` |
| `OPENAI_API_KEY` | `ollama` | `sk-...` |
| `OPENAI_API_BASE_URL` | `http://localhost:11434/v1` | `https://api.openai.com/v1` |

Works with any OpenAI-compatible API — swap Ollama for GPT, Claude, or any other provider by changing the URL and key.

## Architecture

This fork introduces a clean abstraction layer between the application and external services:

```
┌─────────────────────────────────────────┐
│              Flask API                   │
│  graph.py  simulation.py  report.py     │
└──────────────┬──────────────────────────┘
               │ app.extensions['neo4j_storage']
┌──────────────▼──────────────────────────┐
│           Service Layer                  │
│  EntityReader  GraphToolsService         │
│  GraphMemoryUpdater  ReportAgent         │
└──────────────┬──────────────────────────┘
               │ storage: GraphStorage
┌──────────────▼──────────────────────────┐
│         GraphStorage (abstract)          │
│              │                            │
│    ┌─────────▼─────────┐                │
│    │   Neo4jStorage     │                │
│    │  ┌───────────────┐ │                │
│    │  │EmbeddingService│ ← Ollama/OpenAI │
│    │  │ NERExtractor   │ ← LLM          │
│    │  │ SearchService  │ ← Hybrid search │
│    │  └───────────────┘ │                │
│    └───────────────────┘                │
└─────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │   Neo4j     │
        │ Local/Aura  │
        └─────────────┘
```

**Key design decisions:**

- `GraphStorage` is an abstract interface — swap Neo4j for any other graph DB by implementing one class
- Dependency injection via Flask `app.extensions` — no global singletons
- Hybrid search: 0.7 × vector similarity + 0.3 × BM25 keyword search
- Synchronous NER/RE extraction via LLM (replaces Zep's async episodes)
- Embedding service auto-detects Ollama vs OpenAI from the configured URL
- All original dataclasses and LLM tools (InsightForge, Panorama, Agent Interviews) preserved

## Hardware Requirements

### Local (Ollama)

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 32 GB |
| VRAM (GPU) | 10 GB (14b model) | 24 GB (32b model) |
| Disk | 20 GB | 50 GB |
| CPU | 4 cores | 8+ cores |

CPU-only mode works but is significantly slower for LLM inference. For lighter setups, use `qwen2.5:14b` or `qwen2.5:7b`.

### Cloud (OpenAI + Neo4j Aura)

No GPU required. Any machine that can run Python 3.11+ and Node.js 18+. Neo4j Aura has a free tier. Expect OpenAI API costs for LLM and embedding calls during graph building and simulation.

## Use Cases

- **PR crisis testing** — simulate the public reaction to a press release before publishing
- **Trading signal generation** — feed financial news and observe simulated market sentiment
- **Policy impact analysis** — test draft regulations against simulated public response
- **Creative experiments** — someone fed it a classical Chinese novel with a lost ending; the agents wrote a narratively consistent conclusion

## License

AGPL-3.0 — same as the original MiroFish project. See [LICENSE](./LICENSE).

## Credits & Attribution

This is a modified fork of [MiroFish](https://github.com/666ghj/MiroFish) by [666ghj](https://github.com/666ghj), originally supported by [Shanda Group](https://www.shanda.com/). The simulation engine is powered by [OASIS](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

**Modifications in this fork:**
- Backend migrated from Zep Cloud to Neo4j (local CE 5.15 or Aura cloud)
- Added support for cloud LLM and embedding providers (OpenAI, etc.) alongside local Ollama
- Entire frontend translated from Chinese to English (20 files, 1,000+ strings)
- All Zep references replaced with Neo4j across the UI
- `.env.local` override system for easy local/cloud switching
