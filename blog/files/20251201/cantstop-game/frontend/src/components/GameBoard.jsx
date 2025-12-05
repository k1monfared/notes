import React from 'react'
import { motion } from 'framer-motion'
import './GameBoard.css'

function GameBoard({ gameState, selectedPairing, animatingMove, showCellNumbers = false, previewColumns = [], sumColorMap = {} }) {
  const { column_lengths, player1_permanent, player2_permanent, temp_progress, active_runners } = gameState

  const getColumnHeight = (col) => {
    return column_lengths[col]
  }

  const getPlayer1Progress = (col) => {
    return player1_permanent[col] || 0
  }

  const getPlayer2Progress = (col) => {
    return player2_permanent[col] || 0
  }

  const getTempProgress = (col) => {
    return temp_progress[col] || 0
  }

  const isCompleted = (col) => {
    return gameState.player1_completed.includes(col) || gameState.player2_completed.includes(col)
  }

  const getCompletedBy = (col) => {
    if (gameState.player1_completed.includes(col)) return 1
    if (gameState.player2_completed.includes(col)) return 2
    return null
  }

  const isActive = (col) => {
    return active_runners.includes(col)
  }

  const isInSelectedPairing = (col) => {
    if (selectedPairing === null || !gameState.valid_pairings) return false
    const pairing = gameState.valid_pairings[selectedPairing]
    return pairing && (pairing[0] === col || pairing[1] === col)
  }

  const getPreviewsForColumn = (col) => {
    // Returns array of preview objects for this column: [{ position, color, isValid, isSolid }, ...]
    const currentPlayer = gameState.current_player
    const permanentProg = currentPlayer === 1 ? getPlayer1Progress(col) : getPlayer2Progress(col)
    const tempProg = getTempProgress(col)
    const basePosition = permanentProg + tempProg

    return previewColumns
      .filter(p => p.col === col)
      .map(p => ({
        position: basePosition + p.offset,
        color: p.color,
        isValid: p.isValid !== undefined ? p.isValid : true,
        isSolid: p.isSolid !== undefined ? p.isSolid : true
      }))
  }

  const columns = Object.keys(column_lengths).map(Number)

  return (
    <div className="game-board">
      <div className="columns-container">
        {columns.map(col => {
          const height = getColumnHeight(col)
          const p1Progress = getPlayer1Progress(col)
          const p2Progress = getPlayer2Progress(col)
          const tempProg = getTempProgress(col)
          const currentPlayer = gameState.current_player
          const permanentProg = currentPlayer === 1 ? p1Progress : p2Progress
          const completed = isCompleted(col)
          const completedBy = getCompletedBy(col)
          const active = isActive(col)
          const highlighted = isInSelectedPairing(col)

          return (
            <div key={col} className={`column ${active ? 'column-active' : ''}`}>
              <div className="column-header">
                <span className="column-number">{col}</span>
              </div>

              <div className="column-track">
                {Array.from({ length: height }, (_, i) => {
                  const position = i + 1
                  // Show marker only at the current position (topmost), not all positions below
                  const hasP1 = position === p1Progress && p1Progress > 0
                  const hasP2 = position === p2Progress && p2Progress > 0
                  const hasTemp = position === permanentProg + tempProg && tempProg > 0

                  // Get all preview markers for this column and position
                  const columnPreviews = getPreviewsForColumn(col)
                  const previewsAtPosition = columnPreviews.filter(p => p.position === position)
                  const hasPreviewMarkers = previewsAtPosition.length > 0

                  return (
                    <motion.div
                      key={position}
                      className={`column-cell ${completed ? 'completed' : ''} ${
                        completedBy === 1 ? 'player-1-completed' : ''
                      } ${completedBy === 2 ? 'player-2-completed' : ''} ${
                        highlighted ? 'highlighted' : ''
                      } ${active ? 'cell-active' : ''} ${
                        hasPreviewMarkers ? 'preview-cell' : ''
                      }`}
                      initial={false}
                      animate={highlighted ? { scale: [1, 1.05, 1] } : {}}
                      transition={{ duration: 0.3, repeat: highlighted ? Infinity : 0, repeatDelay: 0.5 }}
                    >
                      {/* Show markers - position side-by-side when multiple on same position */}
                      {(() => {
                        // Determine which markers are present
                        const markers = []
                        if (hasP1) markers.push({ type: 'p1' })
                        if (hasP2) markers.push({ type: 'p2' })
                        if (hasTemp) markers.push({ type: 'temp' })
                        // Add all preview markers
                        previewsAtPosition.forEach(p => markers.push({ type: 'preview', color: p.color, isValid: p.isValid, isSolid: p.isSolid }))

                        // Calculate positions based on how many markers
                        const getPosition = (index, total) => {
                          if (total === 1) return '50%'
                          if (total === 2) return index === 0 ? '33%' : '67%'
                          if (total === 3) return ['25%', '50%', '75%'][index]
                          if (total === 4) return ['20%', '40%', '60%', '80%'][index]
                          return '50%'
                        }

                        return (
                          <>
                            {markers.map((marker, idx) => {
                              const markerPos = getPosition(idx, markers.length)

                              if (marker.type === 'p1') {
                                return (
                                  <motion.div
                                    key={`p1-${idx}`}
                                    className="cell-marker player-1-marker"
                                    style={{ left: markerPos }}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: 'spring', stiffness: 300 }}
                                  />
                                )
                              }

                              if (marker.type === 'p2') {
                                return (
                                  <motion.div
                                    key={`p2-${idx}`}
                                    className="cell-marker player-2-marker"
                                    style={{ left: markerPos }}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: 'spring', stiffness: 300 }}
                                  />
                                )
                              }

                              if (marker.type === 'temp') {
                                return (
                                  <motion.div
                                    key={`temp-${idx}`}
                                    className={`cell-marker temp-marker player-${currentPlayer}-temp`}
                                    style={{ left: markerPos }}
                                    initial={{ scale: 0, opacity: 0 }}
                                    animate={{
                                      scale: animatingMove ? [0, 1.2, 1] : 1,
                                      opacity: 1
                                    }}
                                    transition={{ type: 'spring', stiffness: 200, damping: 10 }}
                                  />
                                )
                              }

                              if (marker.type === 'preview') {
                                const isSolid = marker.isSolid !== undefined ? marker.isSolid : true
                                return (
                                  <motion.div
                                    key={`preview-${idx}-${marker.color}`}
                                    className={`cell-marker preview-marker ${marker.isValid ? `preview-${marker.color}` : 'preview-invalid'} ${!isSolid ? 'preview-semi' : ''}`}
                                    style={{ left: markerPos }}
                                    initial={{ scale: 0, opacity: 0 }}
                                    animate={{
                                      scale: [0.8, 1, 0.8],
                                      opacity: isSolid ? [0.6, 1, 0.6] : [0.3, 0.5, 0.3]
                                    }}
                                    transition={{
                                      duration: 1.5,
                                      repeat: Infinity,
                                      ease: 'easeInOut'
                                    }}
                                  />
                                )
                              }

                              return null
                            })}
                          </>
                        )
                      })()}
                      {showCellNumbers && <span className="position-number">{position}</span>}
                    </motion.div>
                  )
                })}
              </div>

              {completed && (
                <div className={`completed-badge player-${completedBy}-badge`}>
                  P{completedBy}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default GameBoard
