# Checkmark - AI Chess Benchmarking Platform

An AI-powered chess benchmarking platform where AI agents play chess against each other to evaluate and compare different AI models.

## Overview

Checkmark provides a unified interface for:
- Registering AI chess models
- Setting up matches between models
- Viewing games and move history
- Analyzing performance metrics across multiple models

## Tech Stack

### Frontend
- **Next.js** (React) - App Router with TypeScript
- **chess.js** - Board rendering and move validation
- **react-chessboard** - Interactive chessboard component
- **zustand** - Board state management

### Backend
- **FastAPI** (Python) - API server with Pydantic v2
- **python-chess** - Chess game logic and validation
- **MongoDB** - Persistent storage
- **LiteLLM + OpenRouter** - AI model integration

## Project Structure

```
project/
├── backend/                 # FastAPI backend
│   ├── main.py            # Application entry point
│   ├── schemas.py         # Pydantic models
│   ├── services/          # Business logic
│   │   ├── chess_engine.py     # Chess logic implementation
│   │   ├── match_service.py    # Match orchestration
│   │   └── ai_model_service.py # AI model integration
│   ├── tools/             # Agentic tools
│   │   └── chess_tools.py    # Tools for AI agents
│   └── utils/             # Utilities
│       └── mongo_db.py      # MongoDB connection
├── frontend/              # Next.js frontend
│   ├── app/              # Next.js App Router
│   │   ├── api/          # API routes
│   │   ├── dashboard/    # Dashboard page
│   │   ├── matches/      # Match viewer page
│   │   └── models/       # Model management page
│   ├── components/       # React components
│   └── package.json
└── .agents_tmp/          # Temporary files
```

## Quick Start

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENROUTER_API_KEY="your_api_key_here"
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DATABASE="checkmark"
```

3. Run the server:
```bash
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

### Phase 1: Project Setup and Dependencies
- ✅ Next.js frontend project initialized
- ✅ FastAPI backend project created
- ✅ MongoDB connection setup
- ✅ Python chess dependencies installed
- ✅ JS dependencies configured

### Phase 2: Database Schema Design
- Collections designed for matches, moves, models, and benchmarks
- MongoDB schemas defined in backend/schemas.py

### Phase 3: Backend Chess Engine
- ChessEngine class with move validation
- FEN serialization/deserialization
- Game status detection (check/checkmate/stalemate)

### Phase 4: Agentic Tools
- GetBoardStateTool - View current board state
- GetLegalMovesTool - Get available legal moves
- MakeMoveTool - Execute moves with validation
- UndoMoveTool - Revert last move
- GetGameStatusTool - Check game status

### Phase 5: AI Model Integration
- LiteLLM/OpenRouter wrapper
- Move suggestion generation
- Position evaluation
- Prompt templates for chess reasoning

### Phase 6: Matchmaking
- Match creation between models
- Game loop orchestration
- Turn management
- Database persistence

### Phase 7: Frontend
- Dashboard with match listings
- Match viewer with interactive chessboard
- Model management page
- Settings page

### Phase 8: Validation and Error Handling
- Move validation middleware
- Retry logic for AI calls
- Edge case handling

### Phase 9: Benchmarking
- Win/loss/draw tracking
- Move accuracy calculation
- Elo rating estimation

### Phase 10: Testing
- Unit tests for chess engine
- Integration tests for tools
- Mock tests for AI service

## API Endpoints

### Matches
- `POST /api/matches` - Create a new match
- `GET /api/matches/{match_id}` - Get match details
- `GET /api/matches/{match_id}/status` - Get game status
- `POST /api/matches/{match_id}/moves` - Make a move

### Models
- `POST /api/models` - Register a new model
- `GET /api/models/{model_id}` - Get model details

### Benchmarks
- `POST /api/benchmarks` - Record benchmark results
- `GET /api/benchmarks/{model_id}` - Get model stats
- `GET /api/benchmarks/rankings` - Get overall rankings

## License

MIT
