# Setup Guide — MacBook Air M2 (Apple Silicon)

Step-by-step instructions to run NetGuard locally on a MacBook Air M2 (also works on any macOS
Apple Silicon or Intel Mac with minor path differences).

## 1. Install prerequisites

```bash
# Xcode command line tools (if not already installed)
xcode-select --install

# Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Nmap — required for real network scans
brew install nmap

# Python 3.12
brew install python@3.12

# Node.js (18+)
brew install node
```

Verify installs:
```bash
nmap --version
python3 --version
node --version
npm --version
```

## 2. Backend setup

```bash
cd netscan/backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## 3. Run the backend

Real scans use Nmap features (OS detection, SYN scans) that need elevated privileges on macOS:

```bash
sudo $(which uvicorn) app.main:app --reload --port 8000
```

If you only want to explore the app with the bundled **sample data** (no real scanning), you don't
need `sudo`:

```bash
uvicorn app.main:app --reload --port 8000
```

Leave this terminal running. Confirm it's up:
```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

## 4. Frontend setup (new terminal tab)

```bash
cd netscan/frontend
npm install
npm run dev
```

Open the printed URL — typically `http://localhost:5173`.

## 5. Log in

- Username: `admin`
- Password: `admin123`

## 6. Run your first scan

Go to **Network Scan** and try your own local subnet. Find it with:

```bash
ipconfig getifaddr en0
```

If that returns e.g. `192.168.1.42`, scan `192.168.1.0/24`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `nmap: command not found` | Re-run `brew install nmap`, restart terminal |
| Scans return 0 hosts | Ensure you're on the same Wi-Fi/LAN as your targets; check macOS firewall settings |
| OS detection shows "Unknown" often | Re-run backend with `sudo` — OS fingerprinting needs raw socket access |
| CORS errors in browser console | Confirm backend is running on port 8000 and frontend on 5173 (see `frontend/src/api/client.ts`) |
| `pip install` fails on a native package (compiler errors) | Run `xcode-select --install` first, then retry |
| Port 8000 or 5173 already in use | `lsof -i :8000` (or `:5173`) to find the process, then `kill <pid>` |

## Full command summary (copy/paste)

```bash
# One-time setup
brew install nmap python@3.12 node
cd netscan/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install

# Every time you want to run the app (2 terminals)
# Terminal 1
cd netscan/backend && source venv/bin/activate && sudo $(which uvicorn) app.main:app --reload --port 8000

# Terminal 2
cd netscan/frontend && npm run dev
```

## Alternative: Docker

If you have Docker Desktop for Mac installed:

```bash
cd netscan
docker compose up --build
```

Open `http://localhost:5173`. Note: Docker Desktop on macOS doesn't expose the host LAN to
containers the same way Linux does, so real scans of your local network work best when the backend
runs natively (as above) rather than in Docker on a Mac.
