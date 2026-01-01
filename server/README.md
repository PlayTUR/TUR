# TUR Master Server

Simple matchmaking server for TUR multiplayer.

## Quick Start

```bash
cd server
pip install -r requirements.txt
python main.py
```

Server runs on port 8080 by default.

## Deployment (VPS)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn (production)
uvicorn main:app --host 0.0.0.0 --port 8080

# Or run directly
python main.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/register` | POST | Create account |
| `/login` | POST | Login, get token |
| `/servers` | GET | List active servers |
| `/servers/register` | POST | Register new server |
| `/servers/{id}/heartbeat` | POST | Keep server alive |
| `/servers/{id}` | DELETE | Remove server |

## Configuration

Edit `main.py` to change:
- `DB_PATH` - Database file location
- Port - Change in `uvicorn.run()` call
