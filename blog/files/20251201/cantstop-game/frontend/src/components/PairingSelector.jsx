import React, { useState } from 'react'
import { motion } from 'framer-motion'
import './PairingSelector.css'

function PairingSelector({
  availablePairings,
  validPairings,
  pairingPlayability,
  selectedPairing,
  onSelectPairing,
  onSelectSum = () => {},
  activeRunners,
  allCompleted,
  isBust = false,
  onHoverPairing = () => {},
  hoveredPairing = null,
  onHoverSum = () => {},
  hoveredSum = null,
  sumColorMap = {},
  lastChosenPairingIndex = null
}) {
  const [tooltip, setTooltip] = useState({ show: false, text: '', x: 0, y: 0 })

  const isPairingValid = (pairing) => {
    return validPairings.some(vp => vp[0] === pairing[0] && vp[1] === pairing[1])
  }

  const getPairingIndex = (pairing) => {
    return validPairings.findIndex(vp => vp[0] === pairing[0] && vp[1] === pairing[1])
  }

  const isColumnCompleted = (col) => {
    return allCompleted.includes(col)
  }

  const isColumnActive = (col) => {
    return activeRunners.includes(col)
  }

  const getPairingPlayability = (pairing, pairingIdx) => {
    // Use backend-provided playability if available
    if (pairingPlayability && pairingIdx >= 0 && pairingPlayability[pairingIdx]) {
      const backendData = pairingPlayability[pairingIdx]
      return {
        sum1Playable: backendData.sum1_playable,
        sum2Playable: backendData.sum2_playable,
        anyPlayable: backendData.sum1_playable || backendData.sum2_playable,
        bothPlayable: backendData.both_can_apply,
        needs_choice: backendData.needs_choice
      }
    }

    return {
      sum1Playable: false,
      sum2Playable: false,
      anyPlayable: false,
      bothPlayable: false,
      needs_choice: false
    }
  }

  const handleMouseMove = (e, needsChoice) => {
    if (needsChoice) {
      setTooltip({
        show: true,
        text: 'Choose One',
        x: e.clientX,
        y: e.clientY
      })
    }
  }

  const handleSumHover = (e, sum, needsChoice) => {
    if (needsChoice) {
      e.stopPropagation()
      setTooltip({
        show: true,
        text: `Choose ${sum}`,
        x: e.clientX,
        y: e.clientY
      })
    }
  }

  const handleMouseLeave = () => {
    setTooltip({ show: false, text: '', x: 0, y: 0 })
  }

  return (
    <div className="pairing-selector">
      <h3 className="pairing-title">{isBust ? 'No Valid Moves!' : 'Choose Your Pairing'}</h3>
      <div className="pairings-grid">
        {availablePairings.map((pairing, index) => {
          const isValid = isPairingValid(pairing)
          const pairingIdx = isValid ? getPairingIndex(pairing) : -1
          const isSelected = selectedPairing === pairingIdx
          const [sum1, sum2] = pairing
          const playability = getPairingPlayability(pairing, pairingIdx)
          const needsChoice = playability.needs_choice
          const wasChosen = lastChosenPairingIndex === pairingIdx
          const isLocked = lastChosenPairingIndex !== null  // Any pairing chosen = all locked

          let disabledReason = null
          if (!isValid) {
            if (!playability.anyPlayable) {
              if (isColumnCompleted(sum1) && isColumnCompleted(sum2)) {
                disabledReason = 'Both completed'
              } else if (activeRunners.length >= 3) {
                disabledReason = 'No room (3 runners)'
              } else {
                disabledReason = 'Cannot play'
              }
            }
          }

          return (
            <motion.div
              key={index}
              className={`pairing-option ${!isValid ? 'disabled' : ''} ${
                isSelected ? 'selected' : ''
              } ${hoveredPairing === index ? 'hovered' : ''} ${needsChoice ? 'needs-choice' : ''} ${
                wasChosen ? 'chosen' : ''
              } ${isLocked ? 'locked' : ''}`}
              onClick={(e) => {
                if (!needsChoice && isValid && !isLocked) {
                  onSelectPairing(pairingIdx, e)
                }
              }}
              onMouseEnter={() => {
                if (!isLocked) {
                  onHoverPairing(index)
                }
              }}
              onMouseMove={(e) => handleMouseMove(e, needsChoice && isValid)}
              onMouseLeave={() => {
                onHoverPairing(null)
                onHoverSum(null)
                handleMouseLeave()
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              style={{ cursor: isLocked ? 'not-allowed' : (needsChoice && isValid ? 'default' : (isValid ? 'pointer' : 'not-allowed')) }}
            >
              <div className="pairing-content">
                <div className="pairing-sums">
                  <div
                    className={`sum-badge ${
                      sumColorMap[sum1]
                        ? (Array.isArray(sumColorMap[sum1]) ? `highlight-${sumColorMap[sum1][0]}` : `highlight-${sumColorMap[sum1]}`)
                        : ''
                    } ${needsChoice && isValid ? 'clickable-sum' : ''} ${hoveredSum === sum1 ? 'sum-hovered' : ''} ${!playability.sum1Playable ? 'sum-unplayable' : ''}`}
                    onClick={(e) => {
                      if (needsChoice && isValid && !isLocked) {
                        e.stopPropagation()
                        onSelectSum(pairingIdx, sum1)
                      }
                    }}
                    onMouseEnter={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        onHoverSum(sum1)
                        handleSumHover(e, sum1, true)
                      }
                    }}
                    onMouseMove={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        setTooltip({ show: true, text: `Choose ${sum1}`, x: e.clientX, y: e.clientY })
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        onHoverSum(null)
                      }
                    }}
                  >
                    {sum1}
                  </div>
                  <span className="pairing-plus">+</span>
                  <div
                    className={`sum-badge ${
                      sumColorMap[sum2]
                        ? (Array.isArray(sumColorMap[sum2]) ? `highlight-${sumColorMap[sum2][1]}` : `highlight-${sumColorMap[sum2]}`)
                        : ''
                    } ${needsChoice && isValid ? 'clickable-sum' : ''} ${hoveredSum === sum2 ? 'sum-hovered' : ''} ${!playability.sum2Playable ? 'sum-unplayable' : ''}`}
                    onClick={(e) => {
                      if (needsChoice && isValid && !isLocked) {
                        e.stopPropagation()
                        onSelectSum(pairingIdx, sum2)
                      }
                    }}
                    onMouseEnter={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        onHoverSum(sum2)
                        handleSumHover(e, sum2, true)
                      }
                    }}
                    onMouseMove={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        setTooltip({ show: true, text: `Choose ${sum2}`, x: e.clientX, y: e.clientY })
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (needsChoice && isValid) {
                        e.stopPropagation()
                        onHoverSum(null)
                      }
                    }}
                  >
                    {sum2}
                  </div>
                </div>
              </div>

              {isSelected && !needsChoice && (
                <motion.div
                  className="selection-indicator"
                  layoutId="selection"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                />
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Tooltip that follows cursor */}
      {tooltip.show && (
        <div
          className="pairing-tooltip"
          style={{
            position: 'fixed',
            left: `${tooltip.x + 15}px`,
            top: `${tooltip.y + 15}px`,
            pointerEvents: 'none',
            zIndex: 10000
          }}
        >
          {tooltip.text}
        </div>
      )}
    </div>
  )
}

export default PairingSelector
