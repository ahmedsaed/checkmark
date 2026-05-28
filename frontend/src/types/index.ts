// ---------------------------------------------------------------------------
// Backend schema types (mirrors backend/schemas.py)
// ---------------------------------------------------------------------------

export type MatchMode = "best_of" | "rapid" | "blitz" | "bullet";
export type MatchStatus = "active" | "finished" | "abandoned";

export interface Match {
  id: string;
  model_a_id: string;
  model_b_id: string;
  mode: MatchMode;
  time_control: number;
  white_side: string | null;
  status: MatchStatus;
  winner_id: string | null;
  total_moves: number;
  board_fen: string | null;
  started_at: string;
  ended_at: string | null;
}

export interface Move {
  id: string;
  match_id: string;
  move_number: number;
  san: string;
  uci: string;
  from_square: string;
  to_square: string;
  promotion: string | null;
  is_check: boolean;
  is_checkmate: boolean;
  is_castling: boolean;
  is_en_passant: boolean;
  thinking_time_ms: number | null;
  timestamp: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  capabilities: {
    supports_chess: boolean;
    max_context_length: number;
  };
  benchmark_stats: {
    wins: number;
    losses: number;
    draws: number;
    total_games: number;
  };
  created_at: string;
  updated_at: string;
}

export interface Benchmark {
  model_id: string;
  match_id: string;
  elo_estimate: number;
  move_accuracy: number;
  average_depth: number;
  thinking_time_avg: number;
  timestamp: string;
}

export interface GameStatus {
  status: MatchStatus;
  winner: string | null;
  is_checkmate: boolean;
  is_stalemate: boolean;
  is_draw: boolean;
  move_count: number;
  current_fen: string;
}

// ---------------------------------------------------------------------------
// API response wrappers
// ---------------------------------------------------------------------------

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface MatchListResponse {
  matches: Match[];
  total: number;
}

export interface ModelListResponse {
  models: Model[];
  total: number;
}

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface MatchCreateRequest {
  model_a_id: string;
  model_b_id: string;
  mode: MatchMode;
  time_control: number;
  white_side?: string;
}

export interface ModelCreateRequest {
  name: string;
  provider: string;
  model_id: string;
  temperature?: number;
  max_tokens?: number;
}

// ---------------------------------------------------------------------------
// Agent chat types (for assistant-ui Thread)
// ---------------------------------------------------------------------------

export type AgentRole = "white" | "black" | "system";

export interface AgentMessage {
  id: string;
  role: AgentRole;
  type: "tool_call" | "tool_result" | "reasoning" | "interaction" | "system";
  content: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// SSE event types
// ---------------------------------------------------------------------------

export type SSEEventType =
  | "move"
  | "status_change"
  | "agent_message"
  | "match_created"
  | "match_finished";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}
