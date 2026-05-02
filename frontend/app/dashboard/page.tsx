'use client'

import Link from 'next/link'

export default function Dashboard() {
  const activeMatches = [
    { id: '1', model_a: 'Claude 3.5', model_b: 'Gemini 1.5', status: 'active', moves: 12 },
    { id: '2', model_a: 'GPT-4o', model_b: 'Llama 3', status: 'active', moves: 8 },
    { id: '3', model_a: 'Claude 3.5', model_b: 'GPT-4o', status: 'finished', moves: 40, winner: 'Claude 3.5' },
  ]

  const modelRankings = [
    { rank: 1, name: 'Claude 3.5', elo: 1450, games: 50, winRate: 60 },
    { rank: 2, name: 'GPT-4o', elo: 1420, games: 45, winRate: 55 },
    { rank: 3, name: 'Gemini 1.5', elo: 1380, games: 52, winRate: 52 },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Active Matches Section */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-white mb-6">Active Matches</h2>
        <div className="grid gap-4">
          {activeMatches.map((match) => (
            <div key={match.id} className="card card-hover">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <div className="text-lg font-medium text-white mb-1">
                    {match.model_a} <span className="text-zinc-500">vs</span> {match.model_b}
                  </div>
                  <div className="text-sm text-zinc-400">
                    Move {match.moves}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`badge ${match.status === 'active' ? 'badge-active' : 'badge-finished'}`}>
                    {match.status}
                  </span>
                  {match.status === 'finished' && match.winner && (
                    <span className="text-green-400 text-sm font-medium">
                      🏆 {match.winner}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Model Rankings Section */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-6">Model Rankings</h2>
        <div className="card">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="pb-3 text-left text-sm font-medium text-zinc-400">Rank</th>
                <th className="pb-3 text-left text-sm font-medium text-zinc-400">Model</th>
                <th className="pb-3 text-left text-sm font-medium text-zinc-400">Elo</th>
                <th className="pb-3 text-left text-sm font-medium text-zinc-400">Games</th>
                <th className="pb-3 text-left text-sm font-medium text-zinc-400">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {modelRankings.map((model) => (
                <tr key={model.rank} className="border-b border-zinc-800 last:border-0">
                  <td className="py-4">
                    <span className={`font-bold ${model.rank === 1 ? 'text-yellow-400' : model.rank === 2 ? 'text-zinc-300' : 'text-zinc-500'}`}>
                      #{model.rank}
                    </span>
                  </td>
                  <td className="py-4 text-white font-medium">{model.name}</td>
                  <td className="py-4 text-zinc-300">{model.elo}</td>
                  <td className="py-4 text-zinc-400">{model.games}</td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${model.winRate}%` }}
                        />
                      </div>
                      <span className="text-zinc-300 text-sm">{model.winRate}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
