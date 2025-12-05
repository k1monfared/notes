import React, { useState, useEffect } from 'react'
import axios from 'axios'
import GameBoard from './components/GameBoard'
import DiceRoller from './components/DiceRoller'
import PairingSelector from './components/PairingSelector'
import PlayerInfo from './components/PlayerInfo'
import './App.css'

const API_BASE = '/api'

function App() {
  const [gameId, setGameId] = useState(null)
  const [gameState, setGameState] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedPairing, setSelectedPairing] = useState(null)
  const [animatingMove, setAnimatingMove] = useState(false)
  const [needsNumberChoice, setNeedsNumberChoice] = useState(false)
  const [chosenNumber, setChosenNumber] = useState(null)
  const [modalPosition, setModalPosition] = useState(null)
  const [showCellNumbers, setShowCellNumbers] = useState(false)
  const [lastDice, setLastDice] = useState(null) // Keep track of last rolled dice
  const [darkMode, setDarkMode] = useState(false)
  const [hoveredPairing, setHoveredPairing] = useState(null)
  const [hoveredNumber, setHoveredNumber] = useState(null)
  const [hoveredSum, setHoveredSum] = useState(null) // For hovering individual sums in choose-one

  // Create new game on mount
  useEffect(() => {
    createNewGame()
  }, [])

  // Track last dice whenever game state changes
  useEffect(() => {
    if (gameState?.current_dice) {
      setLastDice(gameState.current_dice)
    }
  }, [gameState?.current_dice])

  // Generate initial random dice on game creation
  useEffect(() => {
    if (gameState && !lastDice) {
      // Generate random initial dice: 4 dice with values 1-6, sorted
      const initialDice = Array.from({ length: 4 }, () => Math.floor(Math.random() * 6) + 1).sort((a, b) => a - b)
      setLastDice(initialDice)
    }
  }, [gameState, lastDice])

  const createNewGame = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/games`)
      setGameId(response.data.game_id)
      setGameState(response.data.state)
      setSelectedPairing(null)
    } catch (error) {
      console.error('Error creating game:', error)
    } finally {
      setLoading(false)
    }
  }

  const rollDice = async () => {
    if (!gameId || animatingMove) return

    setLoading(true)
    setSelectedPairing(null)

    try {
      const response = await axios.post(`${API_BASE}/games/${gameId}/roll`)
      console.log('=== ROLL RESPONSE ===')
      console.log('Full response:', response)
      console.log('response.data:', response.data)
      console.log('response.data.state:', response.data.state)
      console.log('current_dice:', response.data.state?.current_dice)
      console.log('current_dice type:', typeof response.data.state?.current_dice)
      console.log('current_dice is array:', Array.isArray(response.data.state?.current_dice))
      console.log('available_pairings:', response.data.state?.available_pairings)
      console.log('valid_pairings:', response.data.state?.valid_pairings)
      console.log('is_bust:', response.data.state?.is_bust)
      console.log('====================')
      setGameState(response.data.state)
    } catch (error) {
      console.error('Error rolling dice:', error)
    } finally {
      setLoading(false)
    }
  }

  const selectPairing = async (index, event) => {
    if (animatingMove || !gameState?.valid_pairings?.length || gameState.is_bust) return

    // Check if this pairing needs a number choice
    const playability = gameState.pairing_playability?.[index]
    if (playability?.needs_choice) {
      // For choose-one situations, don't do anything on card click
      // User must click on individual sums (handled by selectSum)
      return
    } else {
      // No choice needed - auto-confirm immediately
      setSelectedPairing(index)
      await confirmPairingWithIndex(index, null)
    }
  }

  const selectSum = async (pairingIndex, sum) => {
    if (animatingMove || gameState.is_bust) return
    setSelectedPairing(pairingIndex)
    await confirmPairingWithIndex(pairingIndex, sum)
  }

  const confirmPairingWithIndex = async (pairingIndex, number) => {
    if (animatingMove) return

    setAnimatingMove(true)
    setNeedsNumberChoice(false)

    try {
      const response = await axios.post(`${API_BASE}/games/${gameId}/choose`, {
        pairing_index: pairingIndex,
        chosen_number: number
      })

      // Wait for animation
      await new Promise(resolve => setTimeout(resolve, 800))

      setGameState(response.data.state)
      setSelectedPairing(null)
      setChosenNumber(null)
      setModalPosition(null)
    } catch (error) {
      console.error('Error choosing pairing:', error)
    } finally {
      setAnimatingMove(false)
    }
  }

  const confirmPairing = async () => {
    if (selectedPairing === null || animatingMove) return

    // Check if this pairing needs a number choice
    const playability = gameState.pairing_playability?.[selectedPairing]
    if (playability?.needs_choice && !chosenNumber) {
      // Show number choice UI (should not reach here with auto-confirm)
      setNeedsNumberChoice(true)
      return
    }

    await confirmPairingWithIndex(selectedPairing, chosenNumber)
  }

  const stopTurn = async () => {
    if (!gameId || animatingMove) return

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/games/${gameId}/stop`)
      setGameState(response.data.state)
      setSelectedPairing(null)
    } catch (error) {
      console.error('Error stopping turn:', error)
    } finally {
      setLoading(false)
    }
  }

  const continueAfterBust = async () => {
    if (!gameId) return

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/games/${gameId}/continue`)
      setGameState(response.data.state)
    } catch (error) {
      console.error('Error continuing after bust:', error)
    } finally {
      setLoading(false)
    }
  }

  // Calculate which dice pairs create which sums for highlighting
  const getDicePairsForPairingIndex = (pairingIndex) => {
    // Map pairing index to dice indices with consistent coloring:
    // - pair1 (orange) is always the FIRST sum in the pairing
    // - pair2 (green) is always the SECOND sum in the pairing
    const pairMappings = [
      { pair1: [0, 1], pair2: [2, 3] }, // Pairing 0: (d1+d2, d3+d4)
      { pair1: [0, 2], pair2: [1, 3] }, // Pairing 1: (d1+d3, d2+d4)
      { pair1: [0, 3], pair2: [1, 2] }  // Pairing 2: (d1+d4, d2+d3)
    ]

    if (pairingIndex < 0 || pairingIndex >= pairMappings.length) {
      return { pair1: [], pair2: [] }
    }

    return pairMappings[pairingIndex]
  }

  if (!gameState) {
    return (
      <div className="app-container loading">
        <div className="loading-spinner">Loading game...</div>
      </div>
    )
  }

  const currentPlayer = gameState.current_player
  const hasDice = gameState.current_dice !== null && gameState.current_dice !== undefined
  const hasValidMoves = gameState.valid_pairings?.length > 0
  const isBust = gameState.is_bust

  // Player can roll if it's their turn, no dice showing, game not over, and not animating
  const canRollPlayer1 = currentPlayer === 1 && !hasDice && !gameState.game_over && !animatingMove
  const canRollPlayer2 = currentPlayer === 2 && !hasDice && !gameState.game_over && !animatingMove

  // Player can stop if they have temp progress, no dice showing, not bust, and not animating
  const canStopPlayer1 = currentPlayer === 1 && Object.keys(gameState.temp_progress).length > 0 && !hasDice && !isBust && !animatingMove
  const canStopPlayer2 = currentPlayer === 2 && Object.keys(gameState.temp_progress).length > 0 && !hasDice && !isBust && !animatingMove

  // Calculate highlighted dice based on hover
  let dicePairs = { pair1: [], pair2: [] }
  let previewColumns = []
  let sumColorMap = {} // Maps sum -> 'pair1' or 'pair2' (or array for same sums)

  // Determine which pairing to highlight - either hovered or selected (for modal)
  const activePairingIndex = hoveredPairing !== null ? hoveredPairing :
                             (needsNumberChoice && selectedPairing !== null ? selectedPairing : null)

  if (activePairingIndex !== null) {
    // For modal, use valid_pairings; for hover, use available_pairings
    const pairings = needsNumberChoice && selectedPairing !== null
      ? gameState.valid_pairings
      : gameState.available_pairings

    const pairing = pairings?.[activePairingIndex]
    if (pairing && gameState.current_dice) {
      // Use pairing index directly to determine dice pairs
      // When hovering available_pairings, index matches pairing structure
      // When using valid_pairings, we need to find which available pairing it corresponds to
      let actualPairingIndex = activePairingIndex

      if (needsNumberChoice && selectedPairing !== null) {
        // For valid pairings, find the corresponding available pairing index
        actualPairingIndex = gameState.available_pairings?.findIndex(
          ap => ap[0] === pairing[0] && ap[1] === pairing[1]
        ) ?? -1
      }

      dicePairs = getDicePairsForPairingIndex(actualPairingIndex)

      // Create mapping of sums to their pair colors
      if (pairing[0] === pairing[1]) {
        // Both sums are the same - store as array to indicate both colors
        sumColorMap[pairing[0]] = ['pair1', 'pair2']
      } else {
        sumColorMap[pairing[0]] = 'pair1'
        sumColorMap[pairing[1]] = 'pair2'
      }

      // Check if this is a valid pairing (for available_pairings mode)
      const isValidPairing = gameState.valid_pairings?.some(vp => vp[0] === pairing[0] && vp[1] === pairing[1])
      const validPairingIndex = isValidPairing
        ? gameState.valid_pairings.findIndex(vp => vp[0] === pairing[0] && vp[1] === pairing[1])
        : (needsNumberChoice && selectedPairing !== null ? selectedPairing : -1)

      // Calculate preview positions - which columns would move
      const playability = validPairingIndex >= 0 ? gameState.pairing_playability?.[validPairingIndex] : null

      if (hoveredSum !== null) {
        // User is hovering over a specific sum in a choose-one situation
        // We need to grey out the dice that correspond to the non-hovered sum

        // Determine which sum gets the colored dice and which gets greyed out
        if (pairing[0] === pairing[1]) {
          // Both sums are the same (e.g., 7+7)
          // When hovering, highlight only the first pair of dice, grey out the second
          if (hoveredSum === pairing[0]) {
            // Keep pair1 dice highlighted, clear pair2 dice (they'll show as unhighlighted)
            dicePairs = { pair1: dicePairs.pair1, pair2: [] }
            // Show first position as colored, second as grey
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: true, isSolid: true })
            previewColumns.push({ col: pairing[0], color: 'invalid', offset: 2, isValid: false, isSolid: true })
          }
        } else {
          // Different sums - grey out dice for non-hovered sum
          if (hoveredSum === pairing[0]) {
            // Keep pair1 dice highlighted, clear pair2 dice
            dicePairs = { pair1: dicePairs.pair1, pair2: [] }
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: true, isSolid: true })
            previewColumns.push({ col: pairing[1], color: 'invalid', offset: 1, isValid: false, isSolid: true })
          } else {
            // Keep pair2 dice highlighted, clear pair1 dice
            dicePairs = { pair1: [], pair2: dicePairs.pair2 }
            previewColumns.push({ col: pairing[0], color: 'invalid', offset: 1, isValid: false, isSolid: true })
            previewColumns.push({ col: pairing[1], color: 'pair2', offset: 1, isValid: true, isSolid: true })
          }
        }
      } else {
        // Show preview for the pairing (even if invalid)
        if (playability?.needs_choice) {
          // Choice is needed - show both options with semi-transparent dots
          if (pairing[0] === pairing[1]) {
            // Both sums same - show both as semi-transparent
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: playability.sum1_playable, isSolid: false })
            previewColumns.push({ col: pairing[0], color: 'pair2', offset: 2, isValid: playability.sum2_playable, isSolid: false })
          } else {
            // Different sums - show both as semi-transparent
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: playability.sum1_playable, isSolid: false })
            previewColumns.push({ col: pairing[1], color: 'pair2', offset: 1, isValid: playability.sum2_playable, isSolid: false })
          }
        } else {
          // No choice needed - show preview based on playability
          if (pairing[0] === pairing[1]) {
            // Both sums are the same
            const isPlayable = playability?.sum1_playable || false
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: isPlayable, isSolid: true })
            previewColumns.push({ col: pairing[0], color: 'pair2', offset: 2, isValid: isPlayable, isSolid: true })
          } else {
            // Different sums
            const sum1Playable = playability?.sum1_playable || false
            const sum2Playable = playability?.sum2_playable || false
            previewColumns.push({ col: pairing[0], color: 'pair1', offset: 1, isValid: sum1Playable, isSolid: true })
            previewColumns.push({ col: pairing[1], color: 'pair2', offset: 1, isValid: sum2Playable, isSolid: true })
          }
        }
      }
    }
  }

  // Debug logging for bust state
  if (gameState.is_bust) {
    console.log('BUST STATE - hasDice:', hasDice)
    console.log('BUST STATE - current_dice:', gameState.current_dice)
    console.log('BUST STATE - available_pairings:', gameState.available_pairings)
    console.log('BUST STATE - valid_pairings:', gameState.valid_pairings)
  }

  return (
    <div className={`app-container ${darkMode ? 'dark-mode' : ''}`}>
      <header className="app-header">
        <h1>Can't Stop</h1>
        <div className="header-controls">
          <button
            className="toggle-btn"
            onClick={() => setDarkMode(!darkMode)}
            title="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button
            className="toggle-btn"
            onClick={() => setShowCellNumbers(!showCellNumbers)}
            title="Toggle cell numbers"
          >
            {showCellNumbers ? '🔢' : '123'}
          </button>
          <button className="new-game-btn" onClick={createNewGame} disabled={loading}>
            New Game
          </button>
        </div>
      </header>

      <main className="game-container">
        <div className="game-layout">
          {/* Left sidebar - Player 1 info */}
          <aside className={`player-sidebar player-1-sidebar ${currentPlayer === 1 ? 'active-player' : ''}`}>
            <PlayerInfo
              playerNumber={1}
              permanent={gameState.player1_permanent}
              completed={gameState.player1_completed}
              isActive={currentPlayer === 1}
              columnLengths={gameState.column_lengths}
            />
          </aside>

          {/* Center - Game board and controls */}
          <div className="game-main">
            <GameBoard
              gameState={gameState}
              selectedPairing={selectedPairing}
              animatingMove={animatingMove}
              showCellNumbers={showCellNumbers}
              previewColumns={previewColumns}
              sumColorMap={sumColorMap}
            />

            <div className="game-controls">
              {/* Dice and pairings - always visible */}
              <div className="dice-and-pairings">
                {/* Dice area - always visible, shows empty state when no dice */}
                <DiceRoller
                  dice={lastDice || gameState.current_dice}
                  isBust={gameState.is_bust}
                  dicePairs={dicePairs}
                  onContinue={continueAfterBust}
                  onRoll={rollDice}
                  onStop={stopTurn}
                  canRoll={canRollPlayer1 || canRollPlayer2}
                  canStop={canStopPlayer1 || canStopPlayer2}
                  loading={loading}
                  currentPlayer={currentPlayer}
                />

                {/* Pairing selector - always visible when dice are rolled */}
                {hasDice && (
                  <PairingSelector
                    availablePairings={gameState.available_pairings}
                    validPairings={gameState.valid_pairings}
                    pairingPlayability={gameState.pairing_playability}
                    selectedPairing={selectedPairing}
                    onSelectPairing={selectPairing}
                    onSelectSum={selectSum}
                    activeRunners={gameState.active_runners}
                    allCompleted={[
                      ...gameState.player1_completed,
                      ...gameState.player2_completed
                    ]}
                    isBust={gameState.is_bust}
                    onHoverPairing={setHoveredPairing}
                    hoveredPairing={hoveredPairing}
                    onHoverSum={setHoveredSum}
                    hoveredSum={hoveredSum}
                    sumColorMap={sumColorMap}
                    lastChosenPairingIndex={gameState.last_chosen_pairing_index}
                  />
                )}
              </div>

              {/* Game over message */}
              <div className="action-buttons">
                {gameState.game_over && (
                  <div className="game-over">
                    <h2>Game Over!</h2>
                    <p>Player {gameState.winner} Wins!</p>
                    <button className="primary-btn" onClick={createNewGame}>
                      Play Again
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right sidebar - Player 2 info */}
          <aside className={`player-sidebar player-2-sidebar ${currentPlayer === 2 ? 'active-player' : ''}`}>
            <PlayerInfo
              playerNumber={2}
              permanent={gameState.player2_permanent}
              completed={gameState.player2_completed}
              isActive={currentPlayer === 2}
              columnLengths={gameState.column_lengths}
            />
          </aside>
        </div>
      </main>

    </div>
  )
}

export default App
