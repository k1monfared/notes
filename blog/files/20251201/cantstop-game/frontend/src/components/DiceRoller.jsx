import React from 'react'
import { motion } from 'framer-motion'
import './DiceRoller.css'

const diceFaces = {
  1: [{ top: '50%', left: '50%' }],
  2: [
    { top: '25%', left: '25%' },
    { top: '75%', left: '75%' }
  ],
  3: [
    { top: '25%', left: '25%' },
    { top: '50%', left: '50%' },
    { top: '75%', left: '75%' }
  ],
  4: [
    { top: '25%', left: '25%' },
    { top: '25%', left: '75%' },
    { top: '75%', left: '25%' },
    { top: '75%', left: '75%' }
  ],
  5: [
    { top: '25%', left: '25%' },
    { top: '25%', left: '75%' },
    { top: '50%', left: '50%' },
    { top: '75%', left: '25%' },
    { top: '75%', left: '75%' }
  ],
  6: [
    { top: '25%', left: '25%' },
    { top: '25%', left: '75%' },
    { top: '50%', left: '25%' },
    { top: '50%', left: '75%' },
    { top: '75%', left: '25%' },
    { top: '75%', left: '75%' }
  ]
}

function Die({ value, index, highlightType }) {
  return (
    <motion.div
      className={`die ${highlightType ? `highlighted-${highlightType}` : ''}`}
      initial={{ rotateX: 0, rotateY: 0, scale: 0 }}
      animate={{
        rotateX: [0, 360, 720],
        rotateY: [0, 360, 720],
        scale: [0, 1.2, 1]
      }}
      transition={{
        duration: 0.6,
        delay: index * 0.1,
        ease: 'easeOut'
      }}
    >
      {diceFaces[value].map((pos, i) => (
        <div
          key={i}
          className="die-dot"
          style={{
            top: pos.top,
            left: pos.left,
            transform: 'translate(-50%, -50%)'
          }}
        />
      ))}
    </motion.div>
  )
}

function DiceRoller({
  dice,
  isBust,
  dicePairs = { pair1: [], pair2: [] },
  onContinue = () => {},
  onRoll = () => {},
  onStop = () => {},
  canRoll = false,
  canStop = false,
  loading = false,
  currentPlayer = 1
}) {
  // Determine highlight type for each die
  const getHighlightType = (index) => {
    if (dicePairs.pair1.includes(index)) return 'pair1'
    if (dicePairs.pair2.includes(index)) return 'pair2'
    return null
  }

  return (
    <div className={`dice-roller ${isBust ? 'bust' : ''}`}>
      {/* Action buttons area - always at top */}
      <div className="dice-actions">
        <motion.button
          className={`roll-btn roll-btn-player-${currentPlayer}`}
          onClick={onRoll}
          disabled={!canRoll || loading}
          whileHover={canRoll && !loading ? { scale: 1.1, rotateZ: 360 } : {}}
          whileTap={canRoll && !loading ? { scale: 0.95 } : {}}
          transition={{ duration: 0.6 }}
        >
          <div className="dice-dot"></div>
          <div className="dice-dot"></div>
          <div className="dice-dot"></div>
          <div className="dice-dot"></div>
          <div className="dice-dot"></div>
          <div className="dice-dot"></div>
        </motion.button>

        <motion.button
          className="stop-btn"
          onClick={onStop}
          disabled={!canStop || loading}
          whileHover={canStop && !loading ? { scale: 1.05 } : {}}
          whileTap={canStop && !loading ? { scale: 0.95 } : {}}
        >
          <div className="stop-icon">STOP</div>
        </motion.button>
      </div>

      {/* Dice display area - always visible */}
      {dice && dice.length > 0 && (
        <div className="dice-container">
          {dice.map((value, index) => (
            <Die
              key={index}
              value={value}
              index={index}
              highlightType={getHighlightType(index)}
            />
          ))}
        </div>
      )}

      {/* Bust message */}
      {isBust && (
        <div className="bust-controls">
          <motion.div
            className="bust-label"
            initial={{ scale: 0 }}
            animate={{ scale: [0, 1.2, 1] }}
            transition={{ duration: 0.5 }}
          >
            BUST!
          </motion.div>
          <button
            className="next-player-btn"
            onClick={onContinue}
            disabled={loading}
          >
            Next Player
          </button>
        </div>
      )}
    </div>
  )
}

export default DiceRoller
