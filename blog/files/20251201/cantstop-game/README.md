# Can't Stop - Interactive Dice Game

A fully-featured web implementation of the classic "Can't Stop" dice game with beautiful animations and real-time gameplay.

## Game Overview

Can't Stop is a push-your-luck dice game where players race to complete columns numbered 2-12. On each turn, you roll 4 dice and choose how to pair them, advancing in those columns. The challenge is deciding when to stop and save your progress versus risking it all for more advancement.

### Rules

- Roll 4 dice and choose one of 3 possible pairings
- Advance your markers in the chosen columns
- You can only have 3 active columns (runners) at a time
- Keep rolling or stop to save your progress
- If you roll and can't make any valid moves, you BUST and lose all unsaved progress
- First player to complete 3 columns wins
- Completed columns cannot be used by either player

## Project Structure

```
cantstop-game/
├── backend/              # Python FastAPI server
│   ├── main.py          # Game logic and API endpoints
│   └── requirements.txt # Python dependencies
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # Game UI components
│   │   ├── App.jsx      # Main application
│   │   └── main.jsx     # Entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Features

### Backend (FastAPI)
- RESTful API for game state management
- Pure game mechanics implementation
- Support for multiple simultaneous games
- Clean separation of rules and state

### Frontend (React + Framer Motion)
- Animated dice rolling with realistic 3D rotation
- Visual game board with all 11 columns (2-12)
- Interactive pairing selection with validation
- Smooth animations for piece movement
- Player progress tracking
- Real-time game state updates
- Responsive design for all screen sizes

### Visual Features
- 4 animated dice with proper dot faces (1-6)
- 3 pairing options clearly displayed
- Valid/invalid pairings visually indicated
- Disabled pairings show why they're invalid
- Selected pairing highlights before confirmation
- Animated piece movement on confirmation
- Active columns highlighted
- Completed columns badged
- Temporary vs permanent progress differentiated
- Current player indication
- Bust animation and messaging

## Installation & Setup

### Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start on `http://localhost:3000`

### Build for Production

```bash
# Frontend
cd frontend
npm run build

# This creates a dist/ folder with optimized static files
# Serve with any static file server
npm run preview
```

## API Endpoints

### Create Game
```
POST /api/games
Response: { game_id, state }
```

### Get Game State
```
GET /api/games/{game_id}
Response: { current_player, dice, progress, ... }
```

### Roll Dice
```
POST /api/games/{game_id}/roll
Response: { state }
```

### Choose Pairing
```
POST /api/games/{game_id}/choose
Body: { pairing_index: 0 | 1 | 2 }
Response: { state }
```

### Stop Turn
```
POST /api/games/{game_id}/stop
Response: { state }
```

## Game State Structure

```javascript
{
  game_id: string,
  current_player: 1 | 2,
  player1_permanent: { 2: 0, 3: 0, ..., 12: 0 },
  player2_permanent: { 2: 0, 3: 0, ..., 12: 0 },
  player1_completed: [7, 8],  // Example
  player2_completed: [6],
  current_dice: [2, 2, 5, 6] | null,
  temp_progress: { 4: 2, 11: 1 },  // Unsaved progress
  active_runners: [4, 11],
  available_pairings: [[4, 11], [7, 8], [8, 7]],
  valid_pairings: [[4, 11], [7, 8]],  // Only valid moves
  game_over: false,
  winner: null,
  is_bust: false,
  column_lengths: { 2: 3, 3: 5, ..., 7: 13, ..., 12: 3 }
}
```

## How to Play

1. Click "Roll Dice" to roll 4 dice
2. View all 3 possible pairings
3. Invalid pairings are grayed out with reason shown:
   - "Column completed" - that column is already won
   - "Too many runners" - would exceed 3 active columns
4. Click a valid pairing to select it (highlights in gold)
5. Click "Confirm Move" to apply the move (animated)
6. Click "Roll Dice" again or "Stop & Save Progress"
7. If you bust, all temporary progress is lost
8. First to complete 3 columns wins!

## Strategy Tips

- Outer columns (2, 3, 11, 12) are shorter but harder to roll
- Middle columns (6, 7, 8) are easier to roll but longer
- Balance risk vs reward when deciding to roll again
- Watch your opponent's progress
- Be careful with 3 active runners - one bad roll and you're stuck!

## Technologies Used

- **Backend**: Python 3.x, FastAPI, Pydantic, Uvicorn
- **Frontend**: React 18, Vite, Framer Motion, Axios
- **Styling**: CSS3 with animations and gradients

## Development

### Backend Tests
The game mechanics are pure functions and can be tested independently:

```python
from backend.main import GameMechanics

# Test dice rolling
dice = GameMechanics.roll_dice()
assert len(dice) == 4

# Test pairings
pairings = GameMechanics.get_all_pairings([1, 2, 3, 4])
assert len(pairings) == 3
```

### Adding Features

Ideas for extension:
- WebSocket support for real-time multiplayer
- AI opponent with different strategies
- Game history and replay
- Sound effects
- Leaderboards
- Tutorial mode
- Undo functionality
- Save/load games

## License

MIT License - feel free to use and modify!

## Credits

Based on the classic "Can't Stop" board game by Sid Sackson.
