'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Dashboard() {
  const [activeMatches, setActiveMatches] = useState([
    { id: '1', model_a: 'Claude 3.5', model_b: 'Gemini 1.5', status: 'active', moves: 12 },
    { id: '2', model_a: 'GPT-4o', model_b: 'Llama 3', status: 'active', moves: 8 },
    { id: '3', model_a: 'Claude 3.5', model_b: 'GPT-4o', status: 'finished', moves: 40, winner: 'Claude 3.5' },
  ])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Checkmark</h1>
          <div className="space-x-4">
            <Link href="/dashboard" className="text-blue-400 hover:text-blue-300">Dashboard</Link>
            <Link href="/matches" className="text-gray-300 hover:text-white">Matches</Link>
            <Link href="/models" className="text-gray-300 hover:text-white">Models</Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold mb-6">Active Matches</h2>
        <div className="grid gap-4">
          {activeMatches.map((match) => (
            <div key={match.id} className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-2xl mr-4">
                    🤖 {match.model_a} <span className="text-gray-400">vs</span> 🤖 {match.model_b}
                  </span>
                </div>
                <span className={`px-3 py-1 rounded-full ${match.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`}>
                  {match.status}
                </span>
              </div>
              <div className="mt-4 text-gray-400">
                Moves: {match.moves}
              </div>
              {match.status === 'finished' && (
                <div className="mt-2 text-green-400 font-bold">Winner: {match.winner}</div>
              )}
            </div>
          ))}
        </div>

        <h2 className="text-3xl font-bold mt-12 mb-6">Model Rankings</h2>
        <div className="bg-gray-800 rounded-lg p-6">
          <table className="w-full">
            <thead>
              <tr className="text-left">
                <th className="pb-2">Rank</th>
                <th className="pb-2">Model</th>
                <th className="pb-2">Elo</th>
                <th className="pb-2">Games</th>
                <th className="pb-2">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-gray-700">
                <td className="py-3">1</td>
                <td className="py-3">Claude 3.5</td>
                <td className="py-3">1450</td>
                <td className="py-3">50</td>
                <td className="py-3">60%</td>
              </tr>
              <tr className="border-t border-gray-700">
                <td className="py-3">2</td>
                <td className="py-3">GPT-4o</td>
                <td className="py-3">1420</td>
                <td className="py-3">45</td>
                <td className="py-3">55%</td>
              </tr>
              <tr className="border-t border-gray-700">
                <td className="py-3">3</td>
                <td className="py-3">Gemini 1.5</td>
                <td className="py-3">1380</td>
                <td className="py-3">52</td>
                <td className="py-3">52%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
