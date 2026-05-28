# Checkmark Project Plan

## 1. OBJECTIVE

Build **Checkmark** - an AI chess benchmarking platform where AI agents play chess against each other to evaluate and compare different AI models. The platform provides a unified interface for registering AI models, setting up matches, viewing games with interactive boards, and analyzing performance metrics.

## 2. TECH STACK

**Backend (unchanged):**
- FastAPI (Python) - API server with Pydantic v2
- python-chess - Chess game logic and validation
- MongoDB (Motor async driver) - Persistent storage
- LiteLLM + OpenRouter - AI model integration
- Poetry - Dependency management

**Frontend (rebuilt from scratch):**
- Next.js 14+ (App Router, TypeScript)
- shadcn/ui - UI component library (dark theme, preset b0)
- assistant-ui - Agentic UI components for match pages
- chess.js + react-chessboard - Board rendering and move validation
- zustand - State management
- next-auth - Authentication
- Server-Sent Events (SSE) - Live match updates

## 3. ARCHITECTURE

### Single Next.js Application with Two Sections

**Admin Portal (`/admin/*`)** — Protected by NextAuth authentication
- Traditional dashboard with forms, buttons, and components
- Model management, match creation, benchmark analytics
- No chat interface — purely conventional UI

**Public Site (`/*`)** — Open to all users
- Browse matches, view games, explore model rankings
- Interactive chessboard with move-by-move navigation
- Agent chat alongside board showing tool calls, thinking, and inter-agent interactions
- Timelapse replay for finished games

### Shared Components
- `Navbar` — Top navigation with public links and admin (if authenticated)
- `Layout` — Consistent wrapper with navbar, centered content (`max-w-7xl mx-auto`)
- `ChessBoard` — Wrapper around react-chessboard
- `MoveList` — Scrollable move list with SAN notation, timestamps, thinking time
- `PlayerCard` — Model info with name, ELO, win/loss indicators
- `Badge` — Status badges (active, finished, checkmate, stalemate, draw)
- `Card` — shadcn/ui card for information grouping

## 4. IMPLEMENTATION STEPS

### Phase 1: Delete Old Frontend & Initialize New Project ✅

**Goal:** Remove the old frontend and set up a fresh Next.js project with all dependencies.

**Steps:**
1. Delete `frontend/` directory
2. Create new Next.js project (App Router, TypeScript, Tailwind CSS)
3. Initialize shadcn/ui: `npx shadcn@latest init --preset b0 --template next --pointer`
4. Initialize assistant-ui: `npx assistant-ui@latest init --yes`
5. Install NextAuth: `npm install next-auth`
6. Install chess dependencies: `chess.js`, `react-chessboard`, `zustand`
7. Install SSE client: `eventsource-parser`
8. Configure Tailwind dark theme
9. Set up project structure:
   ```
   frontend/
   ├── app/
   │   ├── admin/
   │   │   ├── login/
   │   │   ├── page.tsx
   │   │   ├── models/
   │   │   ├── matches/
   │   │   │   ├── page.tsx
   │   │   │   ├── create/
   │   │   │   └── [matchId]/
   │   │   └── benchmarks/
   │   ├── api/
   │   │   ├── auth/[...nextauth]/
   │   │   └── chat/
   │   ├── matches/
   │   │   ├── page.tsx
   │   │   └── [matchId]/
   │   ├── models/
   │   │   ├── page.tsx
   │   │   └── [modelId]/
   │   ├── dashboard/
   │   ├── layout.tsx
   │   ├── page.tsx
   │   └── globals.css
   ├── components/
   │   ├── ui/ (shadcn components)
   │   ├── chess/ (ChessBoard, MoveList, PlayerCard)
   │   ├── admin/ (Admin-specific components)
   │   └── agent/ (assistant-ui Thread, agent messages)
   ├── lib/
   │   ├── auth.ts (NextAuth config)
   │   ├── api.ts (API client for backend)
   │   └── sse.ts (SSE client for live updates)
   ├── stores/ (Zustand stores)
   └── types/ (TypeScript types)
   ```

**Reference:** `frontend/` (to be rebuilt)

---

### Phase 2: Backend API Integration Layer

**Goal:** Create a proper API client in the frontend that connects to the existing FastAPI backend.

**Steps:**
2.1. Create API client (`lib/api.ts`) with typed methods for all backend endpoints:
   - `getMatches()`, `getMatch(id)`, `createMatch(data)`, `getMatchStatus(id)`
   - `getModels()`, `getModel(id)`, `createModel(data)`
   - `getBenchmarks(modelId)`, `getRankings()`
   - `makeMove(matchId, move)`

2.2. Create TypeScript types matching backend schemas:
   - `Match`, `Move`, `Model`, `Benchmark`, `GameStatus`

2.3. Configure backend URL in environment variables (`NEXT_PUBLIC_API_URL`)

2.4. Set up error handling and loading states

**Reference:** `frontend/lib/api.ts`, `frontend/types/`

---

### Phase 3: Authentication Setup

**Goal:** Implement NextAuth with credentials provider for admin access.

**Steps:**
3.1. Configure NextAuth (`lib/auth.ts`) with credentials provider
3.2. Create admin login page (`/admin/login`)
3.3. Add auth protection for `/admin/*` routes
3.4. Add auth context for conditional navbar links
3.5. Store admin credentials in environment variables

**Reference:** `frontend/lib/auth.ts`, `frontend/app/admin/login/page.tsx`

---

### Phase 4: Admin Portal — Traditional Dashboard

**Goal:** Build the admin dashboard with conventional forms and components.

**Steps:**
4.1. **Admin Dashboard (`/admin`)**
   - Overview stats: total models, active matches, finished matches, total games
   - Quick actions: "Create Match", "Register Model", "View Rankings"
   - Recent activity feed
   - Quick match creation form (select two models, choose time control)

4.2. **Model Management (`/admin/models`)**
   - Table of all registered models (name, provider, model_id, ELO, wins/losses/draws, win rate)
   - Actions: edit, delete, view details
   - "Register New Model" button opens dialog/form
   - Form fields: name, provider, model_id, temperature, max_tokens

4.3. **Match Creation (`/admin/matches/create`)**
   - Multi-step form:
     1. Select Model A (white) and Model B (black) from dropdowns
     2. Choose mode: best_of, rapid, blitz, bullet
     3. Set time control (minutes)
     4. Optional: set custom parameters
   - Submit creates match via API, returns match_id
   - Redirect to match detail page

4.4. **Match Monitoring (`/admin/matches`)**
   - List of all matches with status
   - Filter by status (active, finished, abandoned)
   - Click to view match detail
   - Active matches show live move count (via SSE)
   - "Force End" button for abandoned matches

4.5. **Benchmark Analytics (`/admin/benchmarks`)**
   - Model rankings table (ELO, games played, win rate)
   - Head-to-head comparison view
   - Historical performance charts (ELO over time)
   - Move accuracy metrics
   - Average thinking time per model

**Reference:** `frontend/app/admin/`, `frontend/components/admin/`

---

### Phase 5: Public Site — Core Pages

**Goal:** Build the public-facing pages with real API integration.

**Steps:**
5.1. **Landing Page (`/`)**
   - Hero section with platform tagline
   - Two CTA buttons: "View Dashboard" and "Browse Matches"
   - Dark gradient background
   - Stats section: games played, AI models, active matches
   - Featured matches section

5.2. **Public Dashboard (`/dashboard`)**
   - Active matches grid (model names, status badge, move count)
   - Model rankings table (rank, name, ELO, games played, win rate)
   - Recent finished matches with winner highlighted
   - Color-coded status badges (green = active, gray = finished)
   - Real-time updates via SSE

5.3. **Match List (`/matches`)**
   - Paginated list of all matches (active + finished)
   - Filter by status (active / finished)
   - Filter by model
   - Click into match detail view

5.4. **Models Page (`/models`)**
   - Model cards in responsive grid
   - Each card: name, provider, ELO, wins/losses/draws, win rate bar
   - Click into model detail for head-to-head record and benchmark history

5.5. **Model Detail (`/models/[modelId]`)**
   - Overview stats (ELO, total games, win rate)
   - Head-to-head table vs other models
   - Benchmark history chart (ELO over time)
   - Recent match results

**Reference:** `frontend/app/page.tsx`, `frontend/app/dashboard/`, `frontend/app/matches/`, `frontend/app/models/`

---

### Phase 6: Match Detail — Interactive Chessboard + Agent Chat

**Goal:** Build the match detail page with interactive chessboard and assistant-ui agent chat.

**Steps:**
6.1. **Split Layout**
   - Left side: Interactive chessboard using `react-chessboard`
   - Right side: Agent chat using assistant-ui Thread component

6.2. **Chessboard Features**
   - Move-by-move navigation (play/pause, jump to move)
   - Controls: play/pause, speed slider, jump to move
   - FEN string displayed in monospace
   - "Replay" button to play through moves as timelapse
   - Game status header (active / checkmate / stalemate / draw)

6.3. **Agent Chat (assistant-ui Thread)**
   - Shows tool calls from each agent (GetBoardState, GetLegalMoves, MakeMove)
   - Shows agent thinking/reasoning messages
   - Shows inter-agent interactions (congratulations, trash talk)
   - Color-coded by agent (white vs black)
   - Streaming updates for active matches via SSE
   - Historical messages for finished games loaded from API

6.4. **Player Cards**
   - Both models with win/loss indicators
   - ELO ratings, move count, thinking time

6.5. **Move List**
   - Scrollable list of moves with SAN notation, timestamps, thinking time
   - Click to jump to that move on the board

**Reference:** `frontend/app/matches/[matchId]/page.tsx`, `frontend/components/chess/`, `frontend/components/agent/`

---

### Phase 7: Real-Time Updates with SSE

**Goal:** Implement Server-Sent Events for live match updates.

**Steps:**
7.1. Create SSE client (`lib/sse.ts`)
7.2. Subscribe to match updates for active matches
7.3. Update UI in real-time:
   - Move count increments
   - New moves appear in move list
   - Chessboard updates position
   - Agent chat streams new messages
7.4. Handle connection errors and reconnection
7.5. Clean up SSE connections on unmount

**Reference:** `frontend/lib/sse.ts`

---

### Phase 8: Testing & Polish

**Goal:** Ensure code quality and polish the UI.

**Steps:**
8.1. Test all pages with real backend data
8.2. Test authentication flow
8.3. Test SSE live updates
8.4. Test chessboard interactions
8.5. Test agent chat rendering
8.6. Responsive design testing
8.7. Error states and loading skeletons
8.8. Accessibility checks

**Reference:** Manual testing across all pages

## 5. TESTING AND VALIDATION

**Success Criteria:**

1. **Authentication:**
   - Admin login works with credentials
   - `/admin/*` routes redirect to login if not authenticated
   - Navbar shows admin link only when authenticated

2. **Admin Dashboard:**
   - Model management CRUD operations work
   - Match creation form validates inputs
   - Match monitoring shows live updates via SSE
   - Benchmark analytics display correctly

3. **Public Site:**
   - All pages load with real data from backend
   - Match detail shows interactive chessboard
   - Agent chat displays tool calls and messages
   - Timelapse replay works for finished games

4. **Real-Time Updates:**
   - Active matches update in real-time via SSE
   - Chessboard position updates on new moves
   - Agent chat streams new messages
   - Connection reconnection works on network issues

5. **UI/UX:**
   - Dark theme consistent across all pages
   - Responsive design works on mobile/tablet/desktop
   - Loading states and error states handled gracefully
   - Smooth animations and transitions

## 6. DEPLOYMENT

**Requirements:**
- Self-hostable or Vercel-deployable
- Environment variables for:
  - `NEXTAUTH_SECRET` — NextAuth secret key
  - `NEXTAUTH_URL` — Application URL
  - `NEXT_PUBLIC_API_URL` — Backend API URL
  - `ADMIN_USERNAME` / `ADMIN_PASSWORD` — Admin credentials
  - `MONGODB_URI` / `MONGODB_DATABASE` — Backend MongoDB (backend only)
  - `OPENROUTER_API_KEY` — Backend AI integration (backend only)

**Deployment Steps:**
1. Deploy backend to separate service (Railway, Render, etc.)
2. Deploy frontend to Vercel or same platform
3. Configure environment variables
4. Set up custom domain if needed
5. Configure CORS for backend if self-hosted
