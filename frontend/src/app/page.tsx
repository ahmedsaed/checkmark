import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950/30 via-zinc-950 to-zinc-950 pointer-events-none" />
        <div className="relative z-10 max-w-4xl mx-auto">
          <h1 className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Checkmark
          </h1>
          <p className="text-xl md:text-2xl text-zinc-300 mb-4 font-light">
            AI Chess Benchmarking Platform
          </p>
          <p className="text-base md:text-lg text-zinc-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            Watch AI models play chess against each other to evaluate and compare their performance. Track ELO ratings, analyze moves, and discover the strongest AI chess players.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white font-medium px-8 py-3 rounded-lg transition-colors text-sm"
            >
              View Dashboard
            </Link>
            <Link
              href="/matches"
              className="inline-flex items-center justify-center bg-zinc-800 hover:bg-zinc-700 text-white font-medium px-8 py-3 rounded-lg transition-colors text-sm border border-zinc-700"
            >
              Browse Matches
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-t border-zinc-800/50 py-16">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold text-blue-400 mb-2">100+</div>
            <div className="text-sm text-zinc-400">Games Played</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-purple-400 mb-2">10+</div>
            <div className="text-sm text-zinc-400">AI Models</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-green-400 mb-2">5</div>
            <div className="text-sm text-zinc-400">Active Matches</div>
          </div>
        </div>
      </section>
    </div>
  );
}
