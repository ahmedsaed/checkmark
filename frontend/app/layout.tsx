import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Checkmark - AI Chess Benchmarking Platform',
  description: 'Watch AI models play chess against each other to evaluate and compare their performance',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <nav className="bg-zinc-950 border-b border-zinc-800 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link href="/" className="text-xl font-bold text-white">
                Checkmark
              </Link>
              <div className="flex space-x-6">
                <Link href="/dashboard" className="text-zinc-300 hover:text-white transition-colors">
                  Dashboard
                </Link>
                <Link href="/matches" className="text-zinc-300 hover:text-white transition-colors">
                  Matches
                </Link>
                <Link href="/models" className="text-zinc-300 hover:text-white transition-colors">
                  Models
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="min-h-screen bg-black">
          {children}
        </main>
        <footer className="bg-zinc-950 border-t border-zinc-800 py-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-zinc-500 text-sm">
            <p>Checkmark - AI Chess Benchmarking Platform</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
