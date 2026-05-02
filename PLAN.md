# Checkmark Project Plan

## 1. OBJECTIVE

Build **Checkmark** - an AI chess benchmarking platform where AI agents play chess against each other to evaluate and compare different AI models. The platform will provide a unified interface for registering AI models, setting up matches, viewing games, and analyzing performance metrics across multiple models using LiteLLM/OpenRouter integration.

## 2. CONTEXT SUMMARY

**Tech Stack:**
- Frontend: Next.js (React)
- Backend: FastAPI (Python)
- Database: MongoDB
- AI Integration: LiteLLM + OpenRouter API

**Key Components:**
1. Chess game logic and board rendering
2. Agentic tools for move validation and board state
3. AI model management and benchmarking
4. Matchmaking and game orchestration
5. Performance analytics

**Dependencies:**
- python-chess (Python chess library)
- chess.js (JS board rendering)
- LiteLLM wrapper for OpenRouter
- MongoDB for persistent storage

## 3. APPROACH OVERVIEW

**Architecture:** Client-Server with MongoDB backend. Two distinct frontend entry points:
- **Admin Portal** (`/admin/*`) — Locked behind authentication. Used to register models, create matches, and monitor the game loop.
- **Public Site** (`/*`) — Open to anyone. Browse active matches, view finished games with interactive boards, explore model rankings and benchmark data.

**Design System:**
- **Theme:** Dark black theme (`bg-black`, `bg-zinc-950`, `bg-zinc-900`) with zinc/gray palette for surfaces, white text, accent colors (blue for primary actions, green for wins/active, red for losses, yellow for draws).
- **Framework:** Tailwind CSS + shadcn/ui component library for consistent, accessible UI primitives (cards, tables, dialogs, forms, badges, buttons).
- **Layout:** Consistent top navigation bar, centered content container (`max-w-7xl mx-auto`), card-based information grouping, responsive grid layouts.
- **Typography:** Clean hierarchy — large bold headings, readable body text, monospace for FEN strings and move notation.

**Authentication:**
- Admin area protected by simple hardcoded credentials (username + password from environment variables).
- Public pages require no authentication.
- Admin session managed via HTTP-only cookies with Next.js route handlers.

**Chess Libraries:**
- Backend: `python-chess` for move validation, FEN handling, game rules
  - `Board.legal_moves`: Dynamic list of all legal moves
  - `Board.push()` / `Board.pop()`: Make and undo moves via move stack
  - `Board.is_legal()`: Validate move legality
  - `Board.is_checkmate()`, `is_stalemate()`, `is_game_over()`: Game status detection
  - Move format: UCI (e.g., "e2e4") for internal use, convert to SAN for display
  - FEN serialization for board state persistence
- Frontend: `react-chessboard` + `chess.js` for board rendering and move validation
  - `react-chessboard`: Interactive chessboard component (requires `use client` directive)
  - `chess.js`: Backend game logic for frontend validation
  - Move format: SAN notation (e.g., "e4") for agent communication

**Agentic Tool Design:** Tools exposed to AI agents with strict validation feedback loops for invalid moves.
  - Invalid moves return structured error with list of legal alternatives
  - Example: Agent suggests "Qxf7" when queen is on d8 → Returns error + queen's legal moves

**AI Integration:** LiteLLM wrapper to abstract OpenRouter API, supporting multiple model endpoints with configurable parameters.

## 4. IMPLEMENTATION STEPS

### Phase 1: Project Setup and Dependencies ✅ COMPLETED

**Goal:** Initialize project structure and install all necessary dependencies.

**Steps:**
1.1. ✅ Create Next.js frontend project (App Router, TypeScript, Tailwind CSS)
1.2. ✅ Initialize shadcn/ui component library
1.3. ✅ Create FastAPI backend project (Pydantic v2, Uvicorn)
1.4. ✅ Set up MongoDB connection with connection pooling
1.5. ✅ Install Python chess dependencies: `python-chess`, `litellm`, `pydantic-settings`
1.6. ✅ Install JS dependencies: `chess.js`, `react-chessboard`, `zustand` (for board state)
1.7. ✅ Migrate from `requirements.txt` to Poetry for dependency management

**Reference:** `backend/pyproject.toml`, `frontend/package.json`

---

### Phase 2: Database Schema Design ✅ COMPLETED

**Goal:** Design MongoDB collections for matches, moves, models, and benchmarks.

**Collections:**

**models:**
```javascript
{
  name: string,
  provider: string, // e.g., "openrouter"
  model_id: string, // e.g., "anthropic/claude-3.5"
  capabilities: {
    supports_chess: boolean,
    max_context_length: number
  },
  benchmark_stats: {
    wins: number,
    losses: number,
    draws: number,
    total_games: number
  },
  created_at: Date,
  updated_at: Date
}
```

**matches:**
```javascript
{
  id: ObjectId,
  model_a_id: ObjectId,
  model_b_id: ObjectId,
  mode: "best_of" | "rapid" | "blitz" | "bullet",
  time_control: number, // in minutes
  white_side: ObjectId, // Which model plays white
  board_fen: string,
  status: "active" | "finished" | "abandoned",
  winner_id: ObjectId | null,
  total_moves: number,
  started_at: Date,
  ended_at: Date | null
}
```

**moves:**
```javascript
{
  id: ObjectId,
  match_id: ObjectId,
  move_number: number,
  san: string, // e.g., "e4" or "Nf3"
  uci: string, // e.g., "e2e4"
  from_square: string,
  to_square: string,
  promotion: string | null,
  is_check: boolean,
  is_checkmate: boolean,
  is_castling: boolean,
  is_en_passant: boolean,
  thinking_time_ms: number | null,
  timestamp: Date
}
```

**benchmarks:**
```javascript
{
  model_id: ObjectId,
  match_id: ObjectId,
  elo_estimate: number,
  move_accuracy: number,
  average_depth: number,
  thinking_time_avg: number,
  timestamp: Date
}
```

**Reference:** `backend/models.py` (Pydantic models), `backend/schemas.py` (MongoDB schemas)

---

### Phase 3: Backend Chess Engine Implementation

**Goal:** Implement core chess logic using python-chess library.

**Steps:**
3.1. Create `ChessEngine` class with methods:
   - `initialize_board()` - Create new game
   - `get_legal_moves(board)` - Return all legal moves
   - `make_move(board, move)` - Execute move, validate, return new board
   - `undo_move(board)` - Revert last move
   - `get_board_fen(board)` - Get FEN string representation
   - `get_game_status(board)` - Check/checkmate/stalemate detection
   - `validate_move(original_board, proposed_move)` - Validate move legality

3.2. Implement FEN serialization/deserialization for board state transfer

3.3. Create board state middleware for validating moves received from agents

**Reference:** `backend/services/chess_engine.py`

---

### Phase 4: Agentic Tool Implementation

**Goal:** Create tools that AI agents can call to interact with chess games.

**Tools:**

**4.1 `GetBoardStateTool`:**
- Input: `match_id: str`, `side: "white" | "black"` (optional)
- Output: FEN string, piece positions dict, whose turn, castling rights, en passant target
- Usage: Agent calls to view current board before making move

**4.2 `GetLegalMovesTool`:**
- Input: `match_id: str`
- Output: List of all legal moves in SAN notation (e.g., ["e4", "Nf3", "d5"])
- Usage: Agent calls to see available moves

**4.3 `MakeMoveTool`:**
- Input: `match_id: str`, `move_san: str` (e.g., "e4")
- Output: `{"success": true, "message": "Move executed", "board_fen": "...", "is_check": false}` OR `{"success": false, "message": "Invalid move: e4 is not legal", "legal_moves": [...]}`
- Behavior: Validates move against current board state, returns error with legal alternatives if invalid

**4.4 `UndoMoveTool`:**
- Input: `match_id: str`
- Output: Previous board state FEN, whether undo was successful

**4.5 `GetGameStatusTool`:**
- Input: `match_id: str`
- Output: `{"status": "active", "winner": null, "is_checkmate": false, "is_stalemate": false, "move_count": 12}`

**Reference:** `backend/tools/chess_tools.py`

---

### Phase 5: AI Model Integration (LiteLLM + OpenRouter)

**Goal:** Create unified AI model interface for chess reasoning.

**Steps:**
5.1. Create `AIModelService` class:
   - `get_model_config(model_name)` - Get configuration for specific model
   - `generate_move_suggestion(board_fen, match_id)` - Get AI's move recommendation
   - `evaluate_position(board_fen, model_name)` - Get AI's position evaluation
   - `batch_generate_moves(moves_list)` - Generate moves for multiple models

5.2. Implement LiteLLM/OpenRouter wrapper:
   - Abstract OpenRouter API calls
   - Handle different model capabilities
   - Implement retry logic with exponential backoff
   - Add rate limiting support

5.3. Create prompt templates for chess reasoning:
   - Move suggestion prompt (includes FEN, position description)
   - Position evaluation prompt
   - Game strategy prompt

**Reference:** `backend/services/ai_model_service.py`

---

### Phase 6: Matchmaking and Game Orchestration

**Goal:** Implement automated match setup and game loop.

**Steps:**
6.1. Create `MatchService`:
   - `create_match(model_a, model_b, mode)` - Initialize new match
   - `get_current_move_maker(match_id)` - Determine whose turn based on move count
   - `advance_turn(match_id)` - Switch turn, persist board state
   - `complete_match(match_id)` - Mark match finished, calculate winner

6.2. Implement game loop:
   - Fetch current board state
   - Get move suggestion from appropriate AI model
   - Call MakeMoveTool with suggested move
   - Handle validation errors (retry with different model or prompt)
   - Save move to database
   - Advance turn
   - Repeat until game ends

6.3. Add async support for concurrent matches

**Reference:** `backend/services/match_service.py`

---

### Phase 7: Frontend — Public Site (Open Access)

**Goal:** Build a polished dark-themed public interface for browsing matches, viewing games, and exploring model rankings.

**Design:** Dark black theme (`bg-black` / `bg-zinc-950`), shadcn/ui components, consistent layout with top nav bar, centered content (`max-w-7xl mx-auto`), card-based grouping.

**Pages & Components:**

**7.1 Landing Page (`/`):**
- Hero section with platform tagline
- Two CTA buttons: "View Dashboard" and "Browse Matches"
- Dark gradient background

**7.2 Public Dashboard (`/dashboard`):**
- Active matches grid (model names, status badge, move count)
- Model rankings table (rank, name, ELO, games played, win rate)
- Recent finished matches with winner highlighted
- Color-coded status badges (green = active, gray = finished)

**7.3 Match List (`/matches`):**
- Paginated list of all matches (active + finished)
- Filter by status (active / finished)
- Filter by model
- Click into match detail view

**7.4 Match Detail (`/matches/[matchId]`):**
- Interactive chessboard using `react-chessboard`
- Move list with SAN notation, timestamps, and thinking time
- Game status header (active / checkmate / stalemate / draw)
- Player cards showing both models with win/loss indicators
- FEN string displayed in monospace
- "Load Position" button to replay from any move

**7.5 Models Page (`/models`):**
- Model cards in responsive grid
- Each card: name, provider, ELO, wins/losses/draws, win rate bar
- Click into model detail for head-to-head record and benchmark history

**7.6 Model Detail (`/models/[modelId]`):**
- Overview stats (ELO, total games, win rate)
- Head-to-head table vs other models
- Benchmark history chart (ELO over time)
- Recent match results

**Reference:** `frontend/app/`, `frontend/components/ui/` (shadcn), `frontend/components/chess/`

---

### Phase 8: Validation and Error Handling

**Goal:** Ensure robust handling of invalid moves and edge cases.

**Steps:**
8.1. Implement move validation middleware:
   - Catch all move attempts from agents
   - Validate against current legal moves
   - Return structured error with legal alternatives

8.2. Add retry logic for AI model calls:
   - Retry failed move suggestions (3 attempts)
   - Fall back to different model if all fail

8.3. Handle edge cases:
   - Engine crashes during game
   - Network timeouts
   - Invalid match IDs

**Reference:** `backend/middleware/`, `backend/services/ai_model_service.py`

---

### Phase 9: Benchmarking and Analytics

**Goal:** Collect and analyze performance metrics.

**Steps:**
9.1. Implement metrics collection:
   - Win/loss/draw rates per model
   - Move accuracy (percentage of legal moves)
   - Average thinking time
   - Position evaluation scores

9.2. Create benchmark reports:
   - Historical performance trends
   - Head-to-head comparisons
   - Elo rating calculations

9.3. Add analytics API endpoints:
   - GET `/api/benchmarks/{model_id}` - Get model stats
   - GET `/api/benchmarks/rankings` - Get overall rankings
   - GET `/api/benchmarks/history` - Get historical data

**Reference:** `backend/routers/benchmarks.py`, `backend/services/analytics.py`

---

### Phase 10: Testing and Documentation

**Goal:** Ensure code quality and provide usage documentation.

**Steps:**
10.1. Backend tests:
   - Unit tests for ChessEngine
   - Integration tests for tools
   - Mock tests for AI model service

10.2. Frontend tests:
   - Component tests for board rendering
   - API integration tests

10.3. Documentation:
   - API documentation (OpenAPI/Swagger)
   - README with setup instructions
   - Architecture diagrams

**Reference:** `backend/tests/`, `docs/`

## 5. TESTING AND VALIDATION

**Success Criteria:**

1. **Chess Engine Tests:**
   - All standard chess rules validated (castling, en passant, promotion)
   - Check/checkmate detection accurate
   - FEN serialization round-trip verified
   - `Board.legal_moves` generates correct move count for all positions
   - UCI to SAN conversion verified for move display

2. **Tool Validation Tests:**
   - `MakeMoveTool` rejects invalid moves and provides legal alternatives
   - Invalid move example: Agent suggests "Qxf7" when queen is on d8 → Returns error + list of queen's legal moves
   - Move format conversion: SAN from agents → UCI internally → SAN for display
   - Board state persistence via FEN verified across API calls

3. **AI Integration Tests:**
   - LiteLLM/OpenRouter connection verified
   - Multiple model endpoints tested (e.g., GPT-4, Claude, Llama variants)
   - Rate limiting handled correctly with exponential backoff
   - Prompt injection protection verified

4. **Match Orchestration Tests:**
   - Game loop completes full games
   - Turn switching works correctly (white/black alternation)
   - Match completion detection accurate (checkmate, stalemate, draw conditions)
   - Database persistence of moves verified

5. **Frontend Tests:**
   - Chessboard renders correctly with all piece types
   - Move history displays properly with timestamps
   - Dashboard shows match status in real-time
   - `use client` directive properly implemented for interactive components

6. **End-to-End Validation:**
   - Two AI models can play a full game autonomously
   - Invalid moves are caught and handled gracefully
   - Benchmark metrics are recorded accurately
   - Concurrent matches don't interfere with each other

**Validation Methods:**
- Pytest for backend unit/integration tests
- React Testing Library for frontend tests
- Manual testing with diverse AI model pairs
- Load testing for concurrent matches
