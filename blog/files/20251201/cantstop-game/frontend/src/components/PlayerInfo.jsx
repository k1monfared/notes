import React from 'react'
import { motion } from 'framer-motion'
import './PlayerInfo.css'

function PlayerInfo({
  playerNumber,
  permanent,
  completed,
  isActive,
  columnLengths,
  canRoll = false,
  canStop = false,
  onRoll = () => {},
  onStop = () => {},
  loading = false,
  animatingMove = false
}) {
  const totalProgress = Object.entries(permanent)
    .filter(([col]) => !completed.includes(parseInt(col)))
    .reduce((sum, [_, steps]) => sum + steps, 0)

  const columns = Object.keys(columnLengths).map(Number)

  return (
    <div className={`player-info player-${playerNumber} ${isActive ? 'active' : ''}`}>
      <div className="player-header">
        <h2>Player {playerNumber}</h2>
      </div>

      <div className="player-stats">
        <div className="stat">
          <span className="stat-label">Completed</span>
          <span className="stat-value">{completed.length}/3</span>
        </div>
        <div className="stat">
          <span className="stat-label">Total Steps</span>
          <span className="stat-value">{totalProgress}</span>
        </div>
      </div>

      <div className="completed-columns">
        <h3>Completed Columns</h3>
        {completed.length === 0 ? (
          <p className="no-columns">None yet</p>
        ) : (
          <div className="columns-list">
            {completed.map(col => (
              <motion.div
                key={col}
                className="completed-column-badge"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 200 }}
              >
                {col}
              </motion.div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}

export default PlayerInfo
