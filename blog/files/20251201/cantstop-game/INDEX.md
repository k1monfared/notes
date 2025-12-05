# Can't Stop Game - Complete Package Index

## Quick Navigation

### Getting Started (Choose One)
1. **Super Quick Start**: Run `./start.sh` (Unix/Mac) or `start.bat` (Windows)
2. **Manual Setup**: Read [QUICKSTART.md](QUICKSTART.md) (2 minutes)
3. **Full Documentation**: Read [README.md](README.md) (comprehensive)

### Learning the Game
- **How to Play**: [GAMEPLAY.md](GAMEPLAY.md) - Visual walkthrough with examples
- **UI Guide**: [UI_REFERENCE.md](UI_REFERENCE.md) - What everything looks like
- **Project Overview**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Technical details

## File Structure Summary

```
cantstop-game/ (25 files total)
│
├── START HERE
│   ├── INDEX.md              ← You are here
│   ├── QUICKSTART.md         ← 2-minute setup
│   └── start.sh / start.bat  ← One-click launcher
│
├── DOCUMENTATION
│   ├── README.md             ← Full technical docs
│   ├── GAMEPLAY.md           ← How to play guide
│   ├── UI_REFERENCE.md       ← Visual reference
│   └── PROJECT_OVERVIEW.md   ← Architecture overview
│
├── BACKEND (Python/FastAPI)
│   └── backend/
│       ├── main.py           ← Game engine (580 lines)
│       └── requirements.txt  ← Python dependencies
│
└── FRONTEND (React/Vite)
    └── frontend/
        ├── package.json      ← NPM dependencies
        ├── vite.config.js    ← Build config
        ├── index.html        ← Entry point
        └── src/
            ├── main.jsx      ← React bootstrap
            ├── App.jsx       ← Main component (240 lines)
            ├── App.css       ← Main styles
            ├── index.css     ← Global styles
            └── components/
                ├── GameBoard.jsx        ← Board display
                ├── GameBoard.css
                ├── DiceRoller.jsx       ← Dice animation
                ├── DiceRoller.css
                ├── PairingSelector.jsx  ← Pairing UI
                ├── PairingSelector.css
                ├── PlayerInfo.jsx       ← Player stats
                └── PlayerInfo.css
```

## What's Included

### Complete Game Implementation ✓
- [x] Full game mechanics (Can't Stop rules)
- [x] 2-player support
- [x] 11 columns (2-12) with correct heights
- [x] 3-runner limit enforcement
- [x] Bust detection and handling
- [x] Win condition (3 completed columns)

### Professional UI ✓
- [x] Animated 4-dice roller with 3D rotation
- [x] Interactive pairing selection (3 options)
- [x] Visual validation (valid/invalid states)
- [x] Animated piece movement
- [x] Player progress tracking
- [x] Responsive design (desktop/tablet/mobile)

### Developer Experience ✓
- [x] Easy setup scripts (Unix & Windows)
- [x] Comprehensive documentation
- [x] Clean code architecture
- [x] RESTful API with auto-docs
- [x] Hot reload for development
- [x] Production build ready

## Quick Command Reference

### First Time Setup
```bash
# Clone or download the cantstop-game folder
# Then:

./start.sh          # Unix/Mac - auto installs & starts
# OR
start.bat           # Windows - auto installs & starts
```

### Manual Control
```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py                    # Runs on :8000

# Frontend
cd frontend
npm install
npm run dev                       # Runs on :3000
```

### Production Build
```bash
cd frontend
npm run build                     # Creates dist/ folder
npm run preview                   # Preview production build
```

## API Quick Reference

Once running, visit: `http://localhost:8000/docs`

**Endpoints:**
- `POST /api/games` - Create new game
- `GET /api/games/{id}` - Get state
- `POST /api/games/{id}/roll` - Roll dice
- `POST /api/games/{id}/choose` - Choose pairing
- `POST /api/games/{id}/stop` - Stop turn

## Component Tree

```
App
├── GameBoard
│   ├── Column (×11)
│   │   └── Cell (×3 to ×13 depending on column)
│   └── ActiveIndicator
│
├── DiceRoller
│   └── Die (×4)
│
├── PairingSelector
│   └── PairingOption (×3)
│
└── PlayerInfo (×2)
    ├── PlayerStats
    ├── CompletedColumns
    └── ProgressBars
```

## Technology Stack

**Backend:**
- Python 3.8+
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic (validation)

**Frontend:**
- React 18 (UI framework)
- Vite (build tool)
- Framer Motion (animations)
- Axios (HTTP client)

**Styling:**
- Pure CSS3 (no preprocessors)
- CSS Grid & Flexbox
- CSS Animations
- Responsive design

## Key Features Breakdown

### Game Mechanics (Backend)
- Dice rolling: 4d6, sorted
- Pairing generation: 3 unique ways to combine
- Validation: Runner limits, completed columns
- State management: Temporary vs permanent progress
- Win detection: First to 3 columns

### Visual Features (Frontend)
- Dice: Realistic 3D rotation with proper dots
- Board: 11 columns with variable heights
- Markers: Blue (P1), Red (P2), Hollow (temp)
- Animations: Smooth, spring-based physics
- Feedback: Clear valid/invalid indicators

### UX Features
- One-click game start
- Visual turn indicator
- Disabled states show reasons
- Confirmation before moves
- Bust notification with loss count
- Win screen with replay option

## Code Statistics

- **Total Files**: 25
- **Total Lines**: ~1,500
- **Backend Code**: ~580 lines (main.py)
- **Frontend Code**: ~900 lines (all components)
- **Documentation**: ~2,000 lines (5 markdown files)

## Customization Points

Want to modify the game? Key locations:

**Game Rules** → `backend/main.py`:
- Line 70-74: Column lengths
- Line 91-119: Pairing validation logic
- Line 134-150: Apply pairing logic

**Visual Design** → `frontend/src/`:
- `App.css`: Main colors and layout
- `GameBoard.css`: Board appearance
- `DiceRoller.css`: Dice styling
- `PairingSelector.css`: Pairing cards

**Animations** → Component files:
- `DiceRoller.jsx`: Dice roll animation
- `GameBoard.jsx`: Piece movement
- `PairingSelector.jsx`: Selection effects

## Common Tasks

### Change Port
**Backend** → Edit `backend/main.py` line 580:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
```

**Frontend** → Edit `frontend/vite.config.js`:
```javascript
server: { port: 3001 }  // Change 3000 to 3001
```

### Add Sound Effects
1. Add audio files to `frontend/public/sounds/`
2. Import in component: `import rollSound from '/sounds/roll.mp3'`
3. Play on action: `new Audio(rollSound).play()`

### Change Colors
Edit `frontend/src/App.css` and component CSS files:
- Player 1: Search for `#3b82f6` (blue)
- Player 2: Search for `#ef4444` (red)
- Active: Search for `#fbbf24` (gold)

### Add AI Opponent
1. Create `backend/strategy.py` with AI logic
2. Import in `backend/main.py`
3. Add `/api/games/{id}/ai-move` endpoint
4. Call from frontend on AI turn

## Support & Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Try `python3` instead of `python`
- Check port 8000 not in use: `lsof -i :8000`

### Frontend won't start
- Check Node version: `node --version` (need 16+)
- Delete `node_modules`, run `npm install` again
- Check port 3000 not in use

### Animations laggy
- Check browser console for errors
- Disable browser extensions
- Try different browser (Chrome recommended)

### Can't connect backend to frontend
- Check both servers running
- Check proxy config in `vite.config.js`
- Check CORS in `backend/main.py`

## Next Steps After Setup

1. **Play a game** - Get familiar with the UI
2. **Read GAMEPLAY.md** - Understand strategies
3. **Read the code** - See how it works
4. **Customize it** - Make it your own
5. **Deploy it** - Share with friends

## Deployment Options

**Easiest:**
- Frontend: Vercel (`vercel deploy`)
- Backend: Railway (connect GitHub)

**Free Tier:**
- Frontend: Netlify, GitHub Pages, Cloudflare Pages
- Backend: Render, Fly.io, Railway

**Scalable:**
- Frontend: AWS S3 + CloudFront, Netlify
- Backend: AWS Elastic Beanstalk, Google Cloud Run

## Contributing Ideas

Want to extend this? Ideas:
- WebSocket multiplayer
- AI opponent with difficulty levels
- Sound effects and music
- Game replay system
- Tournament mode
- Custom rule variants
- Mobile app (React Native)
- Accessibility improvements

## License

MIT License - Free to use, modify, and distribute!

## Credits

- **Game Design**: "Can't Stop" by Sid Sackson
- **Implementation**: This package (original code)
- **Tech Stack**: FastAPI, React, Framer Motion

---

**Ready to play?** Run `./start.sh` and enjoy! 🎲

For questions, check the documentation files listed above.
