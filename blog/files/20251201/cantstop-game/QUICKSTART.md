# Quick Start Guide

Get the Can't Stop game running in under 2 minutes!

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ and npm installed

## Step 1: Start the Backend

```bash
# Navigate to backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal open!

## Step 2: Start the Frontend (New Terminal)

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

## Step 3: Play!

Open your browser to `http://localhost:3000`

### First Turn

1. Click **"Roll Dice"** - 4 dice appear with animation
2. See 3 pairing options (some may be grayed out)
3. Click a **valid pairing** (it highlights in gold)
4. Click **"Confirm Move"** - watch the pieces animate
5. Click **"Roll Dice"** again or **"Stop & Save Progress"**

### Game Flow

- **Keep Rolling**: Build up temporary progress (risky!)
- **Stop**: Save your progress (safe!)
- **Bust**: If no valid moves, you lose all temporary progress

### Win Condition

First player to complete **3 columns** wins!

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.8+)
- Try: `python3 main.py` instead of `python main.py`

### Frontend won't start
- Check Node version: `node --version` (needs 16+)
- Delete `node_modules` and run `npm install` again

### Port already in use
Backend on 8000:
```bash
# Change port in backend/main.py, line at bottom:
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use 8001
```

Frontend on 3000:
```bash
# Change port in frontend/vite.config.js:
server: { port: 3001 }
```

### Can't connect to backend
Check frontend/vite.config.js has correct proxy:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // Match backend port
    changeOrigin: true,
  }
}
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check API endpoints at `http://localhost:8000/docs`
- Modify game rules in [backend/main.py](backend/main.py)
- Customize UI in [frontend/src/components/](frontend/src/components/)

Enjoy the game!
