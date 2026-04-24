import { NextRequest, NextResponse } from 'next/server'

// Mock match data
const mockMatches = new Map<string, any>()

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model_a_id, model_b_id, mode, time_control, white_side } = body

    // Create mock match
    const matchId = `match-${Date.now()}`
    mockMatches.set(matchId, {
      id: matchId,
      model_a_id,
      model_b_id,
      mode: mode || 'rapid',
      time_control: time_control || 10,
      white_side,
      status: 'active',
      winner_id: null,
      total_moves: 0,
      board_fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
      started_at: new Date().toISOString(),
      ended_at: null,
    })

    return NextResponse.json({
      success: true,
      match_id: matchId,
      message: 'Match created successfully',
    })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to create match' },
      { status: 500 }
    )
  }
}

export async function GET() {
  const matches = Array.from(mockMatches.values())
  return NextResponse.json({ matches })
}
