import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const matchSchema = z.object({
  model_a_id: z.string(),
  model_b_id: z.string(),
  mode: z.enum(['best_of', 'rapid', 'blitz', 'bullet']),
  time_control: z.number().int().positive(),
  white_side: z.string().optional(),
})

const moveSchema = z.object({
  move_san: z.string(),
  is_white_move: z.boolean(),
})

export async function GET(request: NextRequest, { params }: { params: { matchId: string } }) {
  try {
    const mockMatch = {
      id: params.matchId,
      model_a_id: 'model-a',
      model_b_id: 'model-b',
      mode: 'rapid',
      time_control: 10,
      white_side: 'model-a',
      status: 'active',
      winner_id: null,
      total_moves: 12,
      board_fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 7',
      started_at: new Date().toISOString(),
      ended_at: null,
    }
    return NextResponse.json(mockMatch)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to fetch match' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest, { params }: { params: { matchId: string } }) {
  try {
    const body = await request.json()
    const validatedData = matchSchema.parse(body)
    return NextResponse.json({ success: true, message: 'Match updated successfully' })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ success: false, error: 'Invalid request body' }, { status: 400 })
    }
    return NextResponse.json({ success: false, error: 'Failed to update match' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest, { params }: { params: { matchId: string } }) {
  try {
    const body = await request.json()
    const validatedData = matchSchema.parse(body)
    return NextResponse.json({ success: true, message: 'Match updated successfully' })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ success: false, error: 'Invalid request body' }, { status: 400 })
    }
    return NextResponse.json({ success: false, error: 'Failed to update match' }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest, { params }: { params: { matchId: string } }) {
  try {
    const body = await request.json()
    const validatedData = moveSchema.parse(body)
    return NextResponse.json({
      success: true,
      move_number: validatedData.is_white_move ? 7 : 8,
      move_from: 'e2',
      move_to: 'e4',
      is_check: false,
      board_fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 7',
    })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ success: false, error: 'Invalid request body' }, { status: 400 })
    }
    return NextResponse.json({ success: false, error: 'Failed to make move' }, { status: 500 })
  }
}

export async function GET_STATUS(request: NextRequest, { params }: { params: { matchId: string } }) {
  try {
    return NextResponse.json({
      status: 'active',
      is_checkmate: false,
      is_stalemate: false,
      is_insufficient_material: false,
      winner: null,
      move_count: 12,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Failed to get game status' }, { status: 500 })
  }
}
