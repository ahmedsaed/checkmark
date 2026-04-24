import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model_id, elo_estimate, move_accuracy, thinking_time_avg } = body

    return NextResponse.json({
      success: true,
      benchmark_id: `benchmark-${Date.now()}`,
      message: 'Benchmark recorded successfully',
    })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to record benchmark' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json({
      success: true,
      benchmarks: [
        {
          model_id: 'model-1',
          elo_estimate: 1450,
          move_accuracy: 0.85,
          total_games: 50,
        },
      ],
    })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to fetch benchmarks' },
      { status: 500 }
    )
  }
}

export async function GET_MODEL(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const model_id = searchParams.get('model_id')

    if (!model_id) {
      return NextResponse.json(
        { success: false, error: 'model_id required' },
        { status: 400 }
      )
    }

    return NextResponse.json({
      success: true,
      model_id,
      elo_estimate: 1450,
      move_accuracy: 0.85,
      total_games: 50,
      wins: 30,
      losses: 15,
      draws: 5,
    })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to fetch model benchmarks' },
      { status: 500 }
    )
  }
}
