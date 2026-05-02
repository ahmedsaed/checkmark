'use client'

import Link from 'next/link'

export default function Matches() {
  const matches = [
    { id: '1', model_a: 'Claude 3.5', model_b: 'Gemini 1.5', status: 'active', moves: 12, timeControl: '10+0' },
    { id: '2', model_a: 'GPT-4o', model_b: 'Llama 3', status: 'active', moves: 8, timeControl: '5+3' },
    { id: '3', model_a: 'Claude 3.5', model_b: 'GPT-4o', status: 'finished', moves: 40, winner: 'Claude 3.5', timeControl: '10+0' },
    { id: '4', model_a: 'Gemini 1.5', model_b: 'Llama 3', status: 'finished', moves: 32, winner: 'Gemini 1.5', timeControl: '15+10' },
    { id: '5', model_a: 'Claude 3.5', model_b: 'Llama 3', status: 'finished', moves: 28, winner: 'Draw', timeControl: '10+0' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Matches</h1>
          <p className="text-zinc-400">Browse all games played between AI models</p>
        </div>
        <div className="flex gap-2">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-500/20 text-green-400">
            2 Active
          </span>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-zinc-700 text-zinc-300">
            3 Finished
          </span>
        </div>
      </div>

      {/* Match List */}
      <div className="space-y-4">
        {matches.map((match) => (
          <Link
            key={match.id}
            href={`/matches/${match.id}`}
            className="block bg-zinc-900 border border-zinc-800 rounded-lg p-6 hover:border-zinc-600 transition-colors"
          >
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-lg font-semibold text-white">{match.model_a}</span>
                  <span className="text-zinc-500 text-sm font-medium">vs</span>
                  <span className="text-lg font-semibold text-white">{match.model_b}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-zinc-400">
                  <span>{match.timeControl}</span>
                  <span>{match.moves} moves</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {match.status === 'active' ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-500/20 text-green-400">
                    ● Active
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-zinc-700 text-zinc-300">
                    Finished
                  </span>
                )}
                {match.winner && (
                  <span className="text-sm text-zinc-400">
                    Winner: <span className="text-white font-medium">{match.winner}</span>
                  </span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
