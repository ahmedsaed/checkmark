'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function MatchDetail({ params }: { params: { matchId: string } }) {
  const [selectedMove, setSelectedMove] = useState<number | null>(null)

  // Mock match data - would come from API in production
  const match = {
    id: params.matchId,
    model_a: 'Claude 3.5',
    model_b: 'Gemini 1.5',
    status: 'active',
    moves: 12,
    timeControl: '10+0',
    fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 7',
  }

  const moves = [
    { number: 1, white: 'e4', black: 'e5', time: '2.3s' },
    { number: 2, white: 'Nf3', black: 'Nc6', time: '1.8s' },
    { number: 3, white: 'Bb5', black: 'a6', time: '3.1s' },
    { number: 4, white: 'Ba4', black: 'Nf6', time: '2.5s' },
    { number: 5, white: 'O-O', black: 'Be7', time: '4.2s' },
    { number: 6, white: 'Re1', black: 'b5', time: '1.9s' },
    { number: 7, white: 'Bb3', black: 'd6', time: '2.7s' },
    { number: 8, white: 'c3', black: 'O-O', time: '3.5s' },
    { number: 9, white: 'h3', black: 'Nb8', time: '5.1s' },
    { number: 10, white: 'd4', black: 'Nbd7', time: '2.2s' },
    { number: 11, white: 'Nbd2', black: 'Bb7', time: '3.8s' },
    { number: 12, white: 'Bc2', black: 'Re8', time: '4.0s' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back Button */}
      <Link href="/matches" className="text-zinc-400 hover:text-white transition-colors mb-6 inline-flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Matches
      </Link>

      {/* Match Header */}
      <div className="card mb-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-sm text-zinc-500 font-mono">#{match.id}</span>
              <span className="text-sm text-zinc-500">{match.timeControl}</span>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              {match.model_a} <span className="text-zinc-500">vs</span> {match.model_b}
            </h1>
            <span className={`badge ${match.status === 'active' ? 'badge-active' : 'badge-finished'}`}>
              {match.status}
            </span>
          </div>
          <div className="text-right">
            <div className="text-sm text-zinc-400">Move {match.moves}</div>
            <div className="text-xs text-zinc-500 font-mono mt-1">{match.fen}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chess Board */}
        <div className="lg:col-span-2">
          <div className="card p-4">
            {/* Board would use react-chessboard here */}
            <div className="aspect-square bg-zinc-800 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">♟</div>
                <p className="text-zinc-400">Chess Board Component</p>
                <p className="text-zinc-500 text-sm mt-2">FEN: {match.fen}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Move List */}
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-4">Moves</h3>
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {moves.map((move) => (
              <button
                key={move.number}
                onClick={() => setSelectedMove(selectedMove === move.number ? null : move.number)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  selectedMove === move.number
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'hover:bg-zinc-800 text-zinc-300'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 font-mono">{move.number}.</span>
                  <span className="flex-1 mx-2">{move.white}</span>
                  <span className="text-zinc-400">{move.black}</span>
                  <span className="text-zinc-600 text-xs ml-2">{move.time}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
