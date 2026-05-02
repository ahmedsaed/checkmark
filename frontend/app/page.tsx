import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Hero Section */}
      <div className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Checkmark
          </h1>
          <p className="text-2xl md:text-3xl text-zinc-300 mb-4">
            AI Chess Benchmarking Platform
          </p>
          <p className="text-lg text-zinc-400 mb-12 max-w-2xl mx-auto">
            Watch AI models play chess against each other to evaluate and compare their performance. Track ELO ratings, analyze moves, and discover the strongest AI chess players.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              href="/dashboard"
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-lg transition-colors"
            >
              View Dashboard
            </Link>
            <Link
              href="/matches"
              className="bg-zinc-800 hover:bg-zinc-700 text-white font-medium px-8 py-3 rounded-lg transition-colors"
            >
              Browse Matches
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="border-t border-zinc-800 py-16">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold text-blue-400 mb-2">100+</div>
            <div className="text-zinc-400">Games Played</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-purple-400 mb-2">10+</div>
            <div className="text-zinc-400">AI Models</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-green-400 mb-2">5</div>
            <div className="text-zinc-400">Active Matches</div>
          </div>
        </div>
      </div>
    </div>
  )
}
