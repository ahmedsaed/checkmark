import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-900 to-purple-900 text-white">
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-6xl font-bold mb-6">Checkmark</h1>
        <p className="text-2xl mb-8">
          AI Chess Benchmarking Platform
        </p>
        <p className="text-xl mb-12 opacity-90">
          Watch AI models play chess against each other to evaluate and compare their performance
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
          >
            View Dashboard
          </Link>
          <Link
            href="/matches"
            className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
          >
            View Matches
          </Link>
        </div>
      </div>
    </div>
  )
}
