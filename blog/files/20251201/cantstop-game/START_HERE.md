# Start the Can't Stop Game

Python 3.12 is detected and working! ✓

## Option 1: Separate Terminals (Recommended)

Open **2 terminal windows** in this directory:

### Terminal 1 - Backend
```bash
cd /home/k1/public/notes/blog/files/20251201/cantstop-game
./run_backend.sh
```

### Terminal 2 - Frontend
```bash
cd /home/k1/public/notes/blog/files/20251201/cantstop-game
./run_frontend.sh
```

Then open your browser to: **http://localhost:3000**

## Option 2: Manual Start

### Terminal 1 - Backend
```bash
cd /home/k1/public/notes/blog/files/20251201/cantstop-game/backend
python3 -m pip install -r requirements.txt
python3 main.py
```

### Terminal 2 - Frontend
```bash
cd /home/k1/public/notes/blog/files/20251201/cantstop-game/frontend
npm install
npm run dev
```

## Troubleshooting

### Backend starts but shows error about dependencies
```bash
# Make sure you're in the backend directory
cd /home/k1/public/notes/blog/files/20251201/cantstop-game/backend
python3 -m pip install --user -r requirements.txt
python3 main.py
```

### Frontend needs Node.js
Check if Node is installed:
```bash
node --version  # Should show v16 or higher
npm --version   # Should show a version
```

If not installed, install Node.js:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm

# Or use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
```

## What You Should See

**Backend (Terminal 1):**
```
Installing backend dependencies...
Starting backend on http://localhost:8000
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend (Terminal 2):**
```
Starting frontend on http://localhost:3000

  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**Browser:**
- Open http://localhost:3000
- You should see the purple-themed Can't Stop game
- Click "Roll Dice" to start playing!

## Quick Test

To verify Python works:
```bash
python3 --version
# Should show: Python 3.12.7
```

To verify the backend file exists:
```bash
ls -lh /home/k1/public/notes/blog/files/20251201/cantstop-game/backend/main.py
# Should show the file
```

Need help? Check [QUICKSTART.md](QUICKSTART.md) or [README.md](README.md)
