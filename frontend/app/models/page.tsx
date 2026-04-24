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
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Checkmark</h1>
          <div className="space-x-4">
            <Link href="/dashboard" className="text-gray-300 hover:text-white">Dashboard</Link>
            <Link href="/matches" className="text-gray-300 hover:text-white">Matches</Link>
            <Link href="/models" className="text-blue-400 hover:text-white">Models</Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold mb-6">AI Models</h2>

        <div className="grid gap-6">
          {models.map((model) => (
            <div key={model.id} className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-bold">{model.name}</h3>
                  <p className="text-gray-400">Provider: {model.provider}</p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-green-400">Elo: {model.elo}</div>
                  <div className="text-sm text-gray-400">Games: {model.games}</div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="bg-gray-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-green-400">{model.wins}</div>
                  <div className="text-sm text-gray-400">Wins</div>
                </div>
                <div className="bg-gray-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-red-400">{model.losses}</div>
                  <div className="text-sm text-gray-400">Losses</div>
                </div>
                <div className="bg-gray-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-400">{model.draws}</div>
                  <div className="text-sm text-gray-400">Draws</div>
                </div>
              </div>

              <div className="mt-4 bg-gray-700 rounded p-3">
                <div className="flex justify-between text-sm">
                  <span>Win Rate:</span>
                  <span className="font-bold">{((model.wins / model.games) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span>Loss Rate:</span>
                  <span className="font-bold">{((model.losses / model.games) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span>Draw Rate:</span>
                  <span className="font-bold">{((model.draws / model.games) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Add New Model</h3>
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Model Name"
              className="bg-gray-700 rounded px-4 py-2 text-white"
            />
            <input
              type="text"
              placeholder="Provider (e.g., openrouter/anthropic)"
              className="bg-gray-700 rounded px-4 py-2 text-white"
            />
            <input
              type="number"
              placeholder="Expected Elo"
              className="bg-gray-700 rounded px-4 py-2 text-white"
            />
            <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
              Add Model
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
