'use client'

import Link from 'next/link'

export default function Models() {
  const models = [
    { id: '1', name: 'Claude 3.5', provider: 'Anthropic', elo: 1450, games: 50, wins: 30, losses: 15, draws: 5 },
    { id: '2', name: 'GPT-4o', provider: 'OpenAI', elo: 1420, games: 45, wins: 25, losses: 15, draws: 5 },
    { id: '3', name: 'Gemini 1.5', provider: 'Google', elo: 1380, games: 52, wins: 27, losses: 20, draws: 5 },
    { id: '4', name: 'Llama 3', provider: 'Meta', elo: 1350, games: 40, wins: 20, losses: 18, draws: 2 },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">AI Models</h1>
        <p className="text-zinc-400">Registered AI chess models and their performance metrics</p>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {models.map((model) => {
          const winRate = ((model.wins / model.games) * 100).toFixed(1)
          const lossRate = ((model.losses / model.games) * 100).toFixed(1)
          const drawRate = ((model.draws / model.games) * 100).toFixed(1)

          return (
            <Link
              key={model.id}
              href={`/models/${model.id}`}
              className="card card-hover block"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">{model.name}</h3>
                  <p className="text-sm text-zinc-400">{model.provider}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-400">{model.elo}</div>
                  <div className="text-xs text-zinc-500">ELO</div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold text-green-400">{model.wins}</div>
                  <div className="text-xs text-zinc-500">Wins</div>
                </div>
                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold text-red-400">{model.losses}</div>
                  <div className="text-xs text-zinc-500">Losses</div>
                </div>
                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold text-yellow-400">{model.draws}</div>
                  <div className="text-xs text-zinc-500">Draws</div>
                </div>
              </div>

              {/* Win Rate Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Win Rate</span>
                  <span className="text-green-400 font-medium">{winRate}%</span>
                </div>
                <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full"
                    style={{ width: `${winRate}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-zinc-500 pt-1">
                  <span>{model.games} games total</span>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
