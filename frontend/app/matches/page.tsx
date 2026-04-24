'use client'

import { useState, useEffect } from 'react'

// Chess piece SVGs
const Pieces = {
  w: {
    k: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="none" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22.5 11.63V6M20 8h5" stroke="#000" strokeWidth="1.5" />
          <path d="M22.5 25s4.5-7.5 3-13.5c-3-1.5-6 1-6 1s-3-2.5-6-1c-1.5 6 3 13.5 3 13.5" fill="#fff" />
          <path d="M11.5 37c5.5 3.5 15.5 3.5 21 0v-2s9-5.5 6-13.5c-3.5-2-9-2-12-2s-8.5 0-12 2c-3 8 6 13.5 6 13.5v2" fill="#fff" />
          <path d="M11.5 30c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0" stroke="#000" strokeWidth="1.5" />
        </g>
      </svg>
    ),
    q: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#fff" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM24.5 7.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM41 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM10.5 20.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM38.5 20.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0z" />
          <path d="M9 26c8.5-1.5 21-1.5 27 0l2-12-7 11V11l-5.5 14.5-3-15.5-3 15.5-5.5-14.5V25l-7-11 2 12z" />
          <path d="M9 26c0 2 1.5 2 2.5 4 1 2.5 3 4.5 13 4.5s12-2 13-4.5c1-2 2.5-2 2.5-4-8.5-1.5-21-1.5-27 0z" />
          <path d="M11.5 30c3.5-1 18.5-1 22 0M12 33.5c6-1 15-1 21 0" fill="none" />
        </g>
      </svg>
    ),
    r: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#fff" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 39h27v-3H9v3zM12 36v-4h21v4H12zM11 14V9h4v2h5V9h5v2h5V9h4v5" strokeLinecap="round" />
          <path d="M34 14l-3 3H14l-3-3" />
          <path d="M31 17v12.5c0 2.7-2 5-4.5 5h-11C8.5 34.5 6.5 32.2 6.5 29.5V17" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M31 29.5l1.5 2.5h-20l1.5-2.5" />
          <path d="M11 14h23" fill="none" stroke="#000" strokeWidth="1.5" />
        </g>
      </svg>
    ),
    b: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#fff" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <g fill="#fff" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 36c3.39-.97 9.11-1.45 13.5-1.45 4.38 0 10.11.48 13.5 1.45V30c0-2.39-3.15-4.5-7-4.5-3.9 0-7 3.8-7 7 0 3.8-3.15 6.5-7 6.5-3.85 0-7-2.7-7-6.5 0-2.35 1.87-4.5 4.5-5.5V26c0-2.35 1.87-4.5 4.5-5.5V17c-2.63-1-4.5-3.15-4.5-5.5 0-2.63 2.63-4.5 5.5-4.5h17c2.87 0 5.5 1.87 5.5 4.5 0 2.35-1.87 4.5-4.5 5.5v2.5c2.63 1 4.5 3.15 4.5 5.5v2.5c2.63 1 4.5 3.15 4.5 5.5v6z" />
            <path d="M22.5 11.63V6M20 8h5" stroke="#000" strokeWidth="1.5" />
            <path d="M13.5 27c2.5 3 8 3 11 0 3-3 3-8 0-11-3-3-8-3-11 0-3 3-3 8 0 11z" />
          </g>
          <path d="M22.5 34c-2.5 0-4.5-2-4.5-4.5 0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5c0 2.5-2 4.5-4.5 4.5z" fill="#000" />
        </g>
      </svg>
    ),
    n: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#fff" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 10c10.5 1 16.5 8 16 29H15c0-9 10-6.5 8-21" />
          <path d="M24 18c.38 2.32-.46 4.86-2.24 6.64-2.54 2.54-6.62 3.01-9.74.89-2.25 3.76-2.77 8.25-1.29 11.46l-3.74.74c-.4-1.55-.52-3.16-.32-4.77 2-14.77 12.36-21.67 23.78-23.18l3.24.65c-1.04 1.33-1.59 2.92-1.59 4.54 0 3.06-1.98 5.89-5.11 6.7" />
          <path d="M9.5 25.5A4.5 4.5 0 1 1 5 21a4.5 4.5 0 0 1 4.5 4.5z" />
        </g>
      </svg>
    ),
    p: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <path d="M22.5 9c-2.21 0-4 1.79-4 4 0 .89.24 1.71.65 2.45-6.2 1.26-10.85 6.81-11.05 13.27h26.1c-.2-6.46-4.85-12.01-11.05-13.27.41-.74.65-1.56.65-2.45 0-2.21-1.79-4-4-4z" fill="#fff" stroke="#000" strokeWidth="1.5" />
        <path d="M15 30h15v3H15z" fill="#fff" />
        <path d="M22.5 13c-1.5 0-2.5 1-2.5 2.5S21 18 22.5 18s2.5-1 2.5-2.5S24 13 22.5 13z" fill="#000" />
      </svg>
    ),
  },
  b: {
    k: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="none" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22.5 11.63V6M20 8h5" stroke="#000" strokeWidth="1.5" />
          <path d="M22.5 25s4.5-7.5 3-13.5c-3-1.5-6 1-6 1s-3-2.5-6-1c-1.5 6 3 13.5 3 13.5" fill="#000" />
          <path d="M11.5 37c5.5 3.5 15.5 3.5 21 0v-2s9-5.5 6-13.5c-3.5-2-9-2-12-2s-8.5 0-12 2c-3 8 6 13.5 6 13.5v2" fill="#000" />
          <path d="M11.5 30c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0" stroke="#000" strokeWidth="1.5" />
        </g>
      </svg>
    ),
    q: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#000" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM24.5 7.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM41 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM10.5 20.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM38.5 20.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0z" />
          <path d="M9 26c8.5-1.5 21-1.5 27 0l2-12-7 11V11l-5.5 14.5-3-15.5-3 15.5-5.5-14.5V25l-7-11 2 12z" />
          <path d="M9 26c0 2 1.5 2 2.5 4 1 2.5 3 4.5 13 4.5s12-2 13-4.5c1-2 2.5-2 2.5-4-8.5-1.5-21-1.5-27 0z" />
          <path d="M11.5 30c3.5-1 18.5-1 22 0M12 33.5c6-1 15-1 21 0" fill="none" />
        </g>
      </svg>
    ),
    r: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#000" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 39h27v-3H9v3zM12 36v-4h21v4H12zM11 14V9h4v2h5V9h5v2h5V9h4v5" strokeLinecap="round" />
          <path d="M34 14l-3 3H14l-3-3" />
          <path d="M31 17v12.5c0 2.7-2 5-4.5 5h-11C8.5 34.5 6.5 32.2 6.5 29.5V17" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M31 29.5l1.5 2.5h-20l1.5-2.5" />
          <path d="M11 14h23" fill="none" stroke="#000" strokeWidth="1.5" />
        </g>
      </svg>
    ),
    b: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#000" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <g fill="#000" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 36c3.39-.97 9.11-1.45 13.5-1.45 4.38 0 10.11.48 13.5 1.45V30c0-2.39-3.15-4.5-7-4.5-3.9 0-7 3.8-7 7 0 3.8-3.15 6.5-7 6.5-3.85 0-7-2.7-7-6.5 0-2.35 1.87-4.5 4.5-5.5V26c0-2.35 1.87-4.5 4.5-5.5V17c-2.63-1-4.5-3.15-4.5-5.5 0-2.63 2.63-4.5 5.5-4.5h17c2.87 0 5.5 1.87 5.5 4.5 0 2.35-1.87 4.5-4.5 5.5v2.5c2.63 1 4.5 3.15 4.5 5.5v2.5c2.63 1 4.5 3.15 4.5 5.5v6z" />
            <path d="M22.5 11.63V6M20 8h5" stroke="#000" strokeWidth="1.5" />
            <path d="M13.5 27c2.5 3 8 3 11 0 3-3 3-8 0-11-3-3-8-3-11 0-3 3-3 8 0 11z" />
          </g>
          <path d="M22.5 34c-2.5 0-4.5-2-4.5-4.5 0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5c0 2.5-2 4.5-4.5 4.5z" fill="#fff" />
        </g>
      </svg>
    ),
    n: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <g fill="#000" fillRule="evenodd" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 10c10.5 1 16.5 8 16 29H15c0-9 10-6.5 8-21" />
          <path d="M24 18c.38 2.32-.46 4.86-2.24 6.64-2.54 2.54-6.62 3.01-9.74.89-2.25 3.76-2.77 8.25-1.29 11.46l-3.74.74c-.4-1.55-.52-3.16-.32-4.77 2-14.77 12.36-21.67 23.78-23.18l3.24.65c-1.04 1.33-1.59 2.92-1.59 4.54 0 3.06-1.98 5.89-5.11 6.7" />
          <path d="M9.5 25.5A4.5 4.5 0 1 1 5 21a4.5 4.5 0 0 1 4.5 4.5z" />
        </g>
      </svg>
    ),
    p: (
      <svg viewBox="0 0 45 45" className="w-8 h-8">
        <path d="M22.5 9c-2.21 0-4 1.79-4 4 0 .89.24 1.71.65 2.45-6.2 1.26-10.85 6.81-11.05 13.27h26.1c-.2-6.46-4.85-12.01-11.05-13.27.41-.74.65-1.56.65-2.45 0-2.21-1.79-4-4-4z" fill="#000" stroke="#000" strokeWidth="1.5" />
        <path d="M15 30h15v3H15z" fill="#000" />
        <path d="M22.5 13c-1.5 0-2.5 1-2.5 2.5S21 18 22.5 18s2.5-1 2.5-2.5S24 13 22.5 13z" fill="#fff" />
      </svg>
    ),
  },
}

function ChessBoard() {
  const [fen, setFen] = useState('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
  const [boardState, setBoardState] = useState(Array(8).fill(null).map(() => Array(8).fill(null)))
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null)
  const [possibleMoves, setPossibleMoves] = useState<string[]>([])

  useEffect(() => {
    parseFEN(fen)
  }, [fen])

  function parseFEN(fen: string) {
    const [position, , , , , turn] = fen.split(' ')
    const rows = position.split('/')
    const board = Array(8).fill(null).map(() => Array(8).fill(null))

    rows.forEach((row, rowIndex) => {
      let colIndex = 0
      for (const char of row) {
        if (/\d/.test(char)) {
          colIndex += parseInt(char, 10)
        } else {
          const color = char === char.toUpperCase() ? 'w' : 'b'
          board[rowIndex][colIndex] = {
            type: char.toLowerCase(),
            color: color,
          }
          colIndex++
        }
      }
    })

    setBoardState(board)
  }

  function getSquareName(row: number, col: number) {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    return `${files[col]}${8 - row}`
  }

  function handleSquareClick(row: number, col: number) {
    const squareName = getSquareName(row, col)

    if (selectedSquare === squareName) {
      setSelectedSquare(null)
      setPossibleMoves([])
      return
    }

    // Check if this piece can move to this square
    const piece = boardState[row][col]
    if (piece && piece.color === 'w') {
      if (possibleMoves.includes(squareName)) {
        // Valid move
        executeMove(selectedSquare, squareName)
      } else {
        // Select this piece instead
        setSelectedSquare(squareName)
        calculatePossibleMoves(piece, row, col)
      }
      return
    }

    // Select a different piece
    if (piece) {
      setSelectedSquare(squareName)
      calculatePossibleMoves(piece, row, col)
      return
    }

    setSelectedSquare(null)
    setPossibleMoves([])
  }

  function calculatePossibleMoves(piece: any, row: number, col: number) {
    // Simplified move calculation - in production, use chess.js library
    const possibleMoves: string[] = []
    const directions: Record<string, number[][]> = {
      p: [[-1, 0], [-2, 0], [-1, 1], [-1, -1]], // Simplified
      n: [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]],
      b: [[-1, -1], [-1, 1], [1, -1], [1, 1]],
      r: [[-1, 0], [1, 0], [0, -1], [0, 1]],
      q: [[-1, -1], [-1, 1], [1, -1], [1, 1], [-1, 0], [1, 0], [0, -1], [0, 1]],
      k: [[-1, -1], [-1, 1], [1, -1], [1, 1], [-1, 0], [1, 0], [0, -1], [0, 1]],
    }

    const type = piece.type
    const directionsList = directions[type] || directions.p

    directionsList.forEach(([dRow, dCol]) => {
      const newRow = row + dRow
      const newCol = col + dCol

      if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
        const target = boardState[newRow][newCol]
        if (!target) {
          possibleMoves.push(getSquareName(newRow, newCol))
        } else if (target.color === 'b') {
          possibleMoves.push(getSquareName(newRow, newCol))
        }
      }
    })

    setPossibleMoves(possibleMoves)
  }

  function executeMove(from: string, to: string) {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    const fromRow = 8 - parseInt(files[from[0]], 10)
    const fromCol = files.indexOf(from[1])
    const toRow = 8 - parseInt(files[to[0]], 10)
    const toCol = files.indexOf(to[1])

    // Create FEN for the new position
    const newBoard = boardState.map((row) => [...row])
    newBoard[fromRow][fromCol] = null
    newBoard[toRow][toCol] = newBoard[fromRow][fromCol]
    newBoard[fromRow][fromCol] = null

    // Convert to FEN
    const fenStrings = newBoard.map((row) => {
      return row.reduce((acc, piece) => {
        if (!piece) {
          return acc + (acc.length ? '' : 1)
        }
        const type = piece.type
        const color = piece.color === 'w' ? type.toUpperCase() : type
        if (type === 'p' && row.indexOf(piece) === 0) {
          return acc + 1
        }
        return acc + color
      }, '')
    })

    const newFen = fenStrings.join('/') + ' ' + (fen[6] === 'w' ? 'b' : 'w') + ' ' + 'KQkq - 0 1'
    setFen(newFen)
    setSelectedSquare(null)
    setPossibleMoves([])
  }

  function loadInitialBoard() {
    setFEN('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
  }

  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Chess Board</h2>
        <button
          onClick={loadInitialBoard}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
        >
          Refresh Board
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="flex-1">
          <div className="grid grid-cols-8 border-2 border-gray-600">
            {boardState.map((row, rowIndex) =>
              row.map((piece, colIndex) => {
                const squareName = getSquareName(rowIndex, colIndex)
                const isSelected = selectedSquare === squareName
                const isPossibleMove = possibleMoves.includes(squareName)
                const isDark = (rowIndex + colIndex) % 2 === 1

                return (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    onClick={() => handleSquareClick(rowIndex, colIndex)}
                    className={`
                      ${isDark ? 'bg-gray-700' : 'bg-gray-300'}
                      ${isSelected ? 'ring-2 ring-yellow-500' : ''}
                      ${isPossibleMove ? 'ring-2 ring-green-500' : ''}
                      cursor-pointer flex items-center justify-center
                    `}
                    style={{ flex: '1 1 auto' }}
                  >
                    {piece && Pieces[piece.color][piece.type]}
                    {isPossibleMove && (
                      <div className="absolute w-3 h-3 bg-green-500 rounded-full" />
                    )}
                  </div>
                )
              })
            )}
          </div>
          <div className="mt-2 text-sm text-gray-400">
            Click on a piece to select it, then click on a highlighted square to move
          </div>
        </div>

        <div className="lg:w-64">
          <div className="bg-gray-800 rounded-lg p-4 mb-4">
            <h3 className="font-bold mb-2">Board State</h3>
            <div className="text-xs text-gray-400 break-all">
              {fen}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="font-bold mb-2">Possible Moves</h3>
            <div className="flex flex-wrap gap-2">
              {possibleMoves.length > 0 ? (
                possibleMoves.map((move) => (
                  <span
                    key={move}
                    className="bg-blue-500 text-white px-2 py-1 rounded text-sm"
                  >
                    {move}
                  </span>
                ))
              ) : (
                <span className="text-gray-400">No moves</span>
              )}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="font-bold mb-2">Game Status</h3>
            <div className="text-sm text-gray-400">
              <p>Turn: {fen[6] === 'w' ? 'White' : 'Black'}</p>
              <p>Castling: {fen[10]}</p>
              <p>En passant: {fen[14]}</p>
              <p>Move number: {parseInt(fen[18], 10)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Matches() {
  const [currentMatch, setCurrentMatch] = useState({
    id: '1',
    model_a: 'Claude 3.5',
    model_b: 'Gemini 1.5',
    status: 'active',
    moves: 12,
    fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
  })

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Checkmark</h1>
          <div className="space-x-4">
            <Link href="/dashboard" className="text-gray-300 hover:text-white">Dashboard</Link>
            <Link href="/matches" className="text-blue-400 hover:text-white">Matches</Link>
            <Link href="/models" className="text-gray-300 hover:text-white">Models</Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold mb-6">Active Match</h2>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <span className="text-2xl mr-4">
                🤖 {currentMatch.model_a} <span className="text-gray-400">vs</span> 🤖 {currentMatch.model_b}
              </span>
            </div>
            <span className={`px-3 py-1 rounded-full ${currentMatch.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`}>
              {currentMatch.status}
            </span>
          </div>
          <div className="mt-4 text-gray-400">
            Moves: {currentMatch.moves}
          </div>
        </div>

        <ChessBoard />
      </div>
    </div>
  )
}
