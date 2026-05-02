'use client'

import Link from 'next/link'

export default function ModelDetail({ params }: { params: { modelId: string } }) {
  const model = {
    id: params.modelId,
    name: 'Claude 3.5',
    provider: 'Anthropic',
    elo: 1450,
    games: 50,
    wins: 30,
    losses: 15,
    draws: 5,
  }

  const headToHead = [
    { opponent: 'GPT-4o', wins: 8, losses: 4, draws: 2 },
    { opponent: 'Gemini 1.5', wins: 10, losses: 5, draws: 3 },
    { opponent: 'Llama 3', wins: 12, losses: 6, draws: 0 },
  ]

  const recentMatches = [
    { id: '1', opponent: 'GPT-4o', result: '1-0', date: '2024-01-15', moves: 32 },
    { id: '2', opponent: 'Gemini 1.5', result: '1/2-1/2', date: '2024-01-14', moves: 45 },
    { id: '3', opponent: 'Llama 3', result: '1-0', date: '2024-01-13', moves: 28 },
  ]

  const winRate = ((model.wins / model.games) * 100).toFixed(1)
  const lossRate = ((model.losses / model.games) * 100).toFixed(1)
  const drawRate = ((model.draws / model.games) * 100).toFixed(1)

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back Button */}
      <Link href="/models" className="text-zinc-400 hover:text-white transition-colors mb-6 inline-flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Models
      </Link>

      {/* Model Header */}
      <div className="card mb-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{model.name}</h1>
            <p className="text-zinc-400">{model.provider}</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-blue-400">{model.elo}</div>
            <div className="text-sm text-zinc-500">ELO Rating</div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-zinc-800">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{model.wins}</div>
            <div className="text-sm text-zinc-500">Wins</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-400">{model.losses}</div>
            <div className="text-sm text-zinc-500">Losses</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{model.draws}</div>
            <div className="text-sm text-zinc-500">Draws</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{model.games}</div>
            <div className="text-sm text-zinc-500">Total Games</div>
          </div>
        </div>

        {/* Win Rate Bar */}
        <div className="mt-6 pt-6 border-t border-zinc-800">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-zinc-400">Win Rate: <span className="text-green-400 font-medium">{winRate}%</span></span>
            <span className="text-zinc-400">Loss Rate: <span className="text-red-400 font-medium">{lossRate}%</span></span>
            <span className="text-zinc-400">Draw Rate: <span className="text-yellow-400 font-medium">{drawRate}%</span></span>
          </div>
          <div className="w-full h-3 bg-zinc-800 rounded-full overflow-hidden flex">
            <div className="h-full bg-green-500" style={{ width: `${winRate}%` }} />
            <div className="h-full bg-yellow-500" style={{ width: `${drawRate}%` }} />
            <div className="h-full bg-red-500" style={{ width: `${lossRate}%` }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Head-to-Head */}
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-4">Head-to-Head Record</h3>
          <div className="space-y-3">
            {headToHead.map((h2h) => (
              <div key={h2h.opponent} className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0">
                <span className="text-zinc-300">{h2h.opponent}</span>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-green-400">{h2h.wins}W</span>
                  <span className="text-yellow-400">{h2h.draws}D</span>
                  <span className="text-red-400">{h2h.losses}L</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Matches */}
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-4">Recent Matches</h3>
          <div className="space-y-3">
            {recentMatches.map((match) => (
              <Link
                key={match.id}
                href={`/matches/${match.id}`}
                className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0 hover:text-blue-400 transition-colors"
              >
                <div>
                  <div className="text-sm text-zinc-300">vs {match.opponent}</div>
                  <div className="text-xs text-zinc-500">{match.date} · {match.moves} moves</div>
                </div>
                <span className={`text-sm font-medium ${
                  match.result === '1-0' ? 'text-green-400' :
                  match.result === '0-1' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {match.result}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
