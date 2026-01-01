"""
TUR Master Server - Matchmaking and Accounts
Deploy on VPS with: uvicorn main:app --host 0.0.0.0 --port 8080
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
import sqlite3
import bcrypt
import secrets
import time
import os
import re
from collections import defaultdict
from blacklist import blocklist
import asyncio
import httpx

# === Helpers (Moved Up) ===
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"



# Lifespan handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start Blocklist Updater
    asyncio.create_task(blocklist.start_updater())
    print("TUR Master Server started!")
    yield
    print("TUR Master Server shutting down")

app = FastAPI(title="TUR Master Server", version="1.0.0", docs_url=None, redoc_url=None, lifespan=lifespan)

# Client validation secret
CLIENT_SECRET = "TUR-G4M3-CL13NT-v1"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# IP Blacklist Middleware
@app.middleware("http")
async def check_ip_blacklist(request: Request, call_next):
    ip = get_client_ip(request)
    if blocklist.check_ip(ip):
        # Log basic info but don't spam
        # print(f"Blocked connection from blacklisted IP: {ip}")
        return JSONResponse(status_code=403, content={"error": "Access Denied (Blacklisted)"})
    return await call_next(request)

# Client validation middleware
@app.middleware("http")
async def validate_client(request: Request, call_next):
    # Public endpoints
    if request.url.path in ["/", "/health"]:
        return await call_next(request)
    
    # Game client header
    if request.headers.get("X-TUR-Client") == CLIENT_SECRET:
        return await call_next(request)
    
    # Website origin
    origin = request.headers.get("Origin", "") or request.headers.get("Referer", "")
    allowed = ["https://tur.wyind.dev", "http://localhost", "http://127.0.0.1"]
    if any(origin.startswith(a) for a in allowed):
        return await call_next(request)
    
    return JSONResponse(status_code=403, content={"error": "Unauthorized"})

DB_PATH = "tur_server.db"
REGISTER_API_KEY = os.environ.get("TUR_REGISTER_KEY", "PBd&%qm!Qt$w#!n@pBtwV3Fz4LuiCPD7I2@2ZC@KF@%4DuVUsk&cx")
ADMIN_API_KEY = os.environ.get("TUR_ADMIN_KEY", "DKkc5k^Eu#V1K8q$wRYxlSJ!aVb84AgL3I96K6ROkZr7EqA9%M%#ojZ!Sl&V$Yfbryg19iSBNGL3")

# Obfuscated tables
TBL_USERS = "u_data"
TBL_SESSIONS = "s_tokens"
TBL_SERVERS = "net_nodes"
TBL_BANS = "b_list"  # Ban list
TBL_STATS = "u_stats" # User stats (score, level)
TBL_NEWS = "n_feed"

# Discord Config
DISCORD_BOT_TOKEN = os.environ.get("TUR_DISCORD_BOT_TOKEN", "")
NEWS_CHANNEL_ID = os.environ.get("TUR_NEWS_CHANNEL_ID", "")

# Rate limiting
rate_limits = defaultdict(list)
RATE_LIMIT_WINDOW = 60
MAX_AUTH_ATTEMPTS = 5
MAX_REGISTER_ATTEMPTS = 3

# === Helpers ===

# get_client_ip moved up


def check_rate_limit(ip: str, limit_type: str, max_attempts: int) -> bool:
    now = time.time()
    key = f"{limit_type}:{ip}"
    rate_limits[key] = [t for t in rate_limits[key] if now - t < RATE_LIMIT_WINDOW]
    if len(rate_limits[key]) >= max_attempts:
        return False
    rate_limits[key].append(now)
    return True

def sanitize_username(username: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '', username)[:20]

def sanitize_text(text: str, max_len: int = 50) -> str:
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)[:max_len]

# === Database ===

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_USERS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uname TEXT UNIQUE NOT NULL,
        pw_h TEXT NOT NULL,
        c_at REAL DEFAULT (strftime('%s', 'now')),
        l_at REAL
    )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_SESSIONS} (
        tk TEXT PRIMARY KEY,
        uid INTEGER NOT NULL,
        c_at REAL DEFAULT (strftime('%s', 'now')),
        exp REAL,
        FOREIGN KEY (uid) REFERENCES {TBL_USERS}(id)
    )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_SERVERS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        n TEXT NOT NULL,
        h_ip TEXT NOT NULL,
        p INTEGER NOT NULL,
        h_n TEXT,
        pw INTEGER DEFAULT 0,
        pc INTEGER DEFAULT 1,
        mp INTEGER DEFAULT 2,
        is_admin INTEGER DEFAULT 0,
        c_at REAL DEFAULT (strftime('%s', 'now')),
        hb REAL DEFAULT (strftime('%s', 'now'))
    )""")
    
    # Migration: Add is_admin if user table exists but column missing
    try:
        c.execute(f"SELECT is_admin FROM {TBL_USERS} LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating DB: Adding is_admin column")
        c.execute(f"ALTER TABLE {TBL_USERS} ADD COLUMN is_admin INTEGER DEFAULT 0")

    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_BANS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER,
        ip TEXT,
        reason TEXT,
        banned_by TEXT,
        c_at REAL DEFAULT (strftime('%s', 'now')),
        exp REAL,
        FOREIGN KEY (uid) REFERENCES {TBL_USERS}(id)
    )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_STATS} (
        uid INTEGER PRIMARY KEY,
        t_score INTEGER DEFAULT 0,
        t_plays INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        lvl INTEGER DEFAULT 1,
        u_at REAL DEFAULT (strftime('%s', 'now')),
        FOREIGN KEY (uid) REFERENCES {TBL_USERS}(id)
    )""")
    # Add indices for leaderboard
    # c.execute(f"CREATE INDEX IF NOT EXISTS idx_xp ON {TBL_STATS}(xp DESC)")
    
    # Detailed Score Logs (New V2)
    c.execute(f"""CREATE TABLE IF NOT EXISTS s_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER,
        song_name TEXT,
        difficulty TEXT,
        score INTEGER,
        max_score INTEGER,
        perfects INTEGER,
        goods INTEGER,
        bads INTEGER,
        misses INTEGER,
        grade TEXT,
        ts REAL DEFAULT (strftime('%s', 'now')),
        FOREIGN KEY (uid) REFERENCES {TBL_USERS}(id)
    )""")
    
    # News Feed Table
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TBL_NEWS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        author TEXT DEFAULT 'SYSTEM',
        ts REAL DEFAULT (strftime('%s', 'now'))
    )""")
    
    conn.commit()
    conn.close()

def db_update_stats(uid: int, score: int):
    conn = get_db()
    c = conn.cursor()
    
    # Simple XP formula: 10% of score
    xp_gain = int(score * 0.1)
    
    # Get current
    c.execute(f"SELECT * FROM {TBL_STATS} WHERE uid = ?", (uid,))
    row = c.fetchone()
    
    if row:
        new_xp = row['xp'] + xp_gain
        new_score = row['t_score'] + score
        new_plays = row['t_plays'] + 1
        # Level formula: sqrt(xp / 1000)
        new_lvl = int((new_xp / 1000) ** 0.5) + 1
        
        c.execute(f"UPDATE {TBL_STATS} SET t_score=?, t_plays=?, xp=?, lvl=?, u_at=? WHERE uid=?",
                  (new_score, new_plays, new_xp, new_lvl, time.time(), uid))
    else:
        new_lvl = int((xp_gain / 1000) ** 0.5) + 1
        c.execute(f"INSERT INTO {TBL_STATS} (uid, t_score, t_plays, xp, lvl) VALUES (?, ?, ?, ?, ?)",
                  (uid, score, 1, xp_gain, new_lvl))
        
    conn.commit()
    conn.close()

def is_user_banned(user_id: int = None, ip: str = None) -> dict:
    """Check if user or IP is banned. Returns ban info or None."""
    conn = get_db()
    c = conn.cursor()
    now = time.time()
    
    # Check by user ID
    if user_id:
        c.execute(f"SELECT reason, exp FROM {TBL_BANS} WHERE uid = ? AND (exp IS NULL OR exp > ?)", (user_id, now))
        row = c.fetchone()
        if row:
            conn.close()
            return {"banned": True, "reason": row["reason"], "expires": row["exp"]}
    
    # Check by IP
    if ip:
        c.execute(f"SELECT reason, exp FROM {TBL_BANS} WHERE ip = ? AND (exp IS NULL OR exp > ?)", (ip, now))
        row = c.fetchone()
        if row:
            conn.close()
            return {"banned": True, "reason": row["reason"], "expires": row["exp"]}
    
    conn.close()
    return None

def get_user_from_token(token: str):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT uid, exp FROM {TBL_SESSIONS} WHERE tk = ?", (token,))
    row = c.fetchone()
    if not row or row['exp'] < time.time():
        conn.close()
        return None
    
    uid = row['uid']
    c.execute(f"SELECT id, username, is_admin FROM {TBL_USERS} WHERE id = ?", (uid,))
    user = c.fetchone()
    conn.close()
    return user

def is_admin_request(req_key: str = None, token: str = None) -> bool:
    """Validate if request comes from admin via Key OR Token"""
    # 1. Check Key
    if req_key and secrets.compare_digest(req_key, ADMIN_API_KEY):
        return True
    
    # 2. Check Token
    if token:
        user = get_user_from_token(token)
        if user and user['is_admin'] == 1:
            return True
            
    return False

# === Admin Promote ===
class PromoteRequest(BaseModel):
    admin_key: Optional[str] = None
    username: str

@app.post("/api/v2/admin/promote")
async def promote_user(req: PromoteRequest, request: Request):
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip, "admin_action", 5):
         raise HTTPException(429, "Rate limit")
         
    # Check Auth (Key OR Token)
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    
    if not is_admin_request(req.admin_key, token):
        raise HTTPException(403, "Invalid Admin Key or Token")
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE {TBL_USERS} SET is_admin = 1 WHERE username = ?", (req.username,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(404, "User not found")
    conn.commit()
    conn.close()
    return {"success": True, "message": f"User {req.username} is now an ADMIN"}

# === Models (Pydantic V2) ===

class RegisterRequest(BaseModel):
    username: str
    password: str
    api_key: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username must be 3-20 alphanumeric characters')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 64:
            raise ValueError('Password must be 6-64 characters')
        return v

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    username: Optional[str] = None
    message: Optional[str] = None

class ServerListResponse(BaseModel):
    servers: List[dict]

class RegisterServerRequest(BaseModel):
    name: str
    port: int
    host_name: Optional[str] = "Player"
    password_protected: bool = False
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return sanitize_text(v, 30)
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v < 1024 or v > 65535:
            raise ValueError('Invalid port')
        return v

# === Auth ===

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = time.time() + (7 * 24 * 3600)
    conn = get_db()
    c = conn.cursor()
    c.execute(f"DELETE FROM {TBL_SESSIONS} WHERE uid = ? AND exp < ?", (user_id, time.time()))
    c.execute(f"INSERT INTO {TBL_SESSIONS} (tk, uid, exp) VALUES (?, ?, ?)", (token, user_id, expires))
    conn.commit()
    conn.close()
    return token

# === Routes ===

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/register")
async def register(req: RegisterRequest, request: Request):
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip, "register", MAX_REGISTER_ATTEMPTS):
        raise HTTPException(429, "Too many attempts")
    if not secrets.compare_digest(req.api_key, REGISTER_API_KEY):
        raise HTTPException(403, "Unauthorized")
    
    username = sanitize_username(req.username)
    if len(username) < 3:
        raise HTTPException(400, "Invalid username")
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT id FROM {TBL_USERS} WHERE uname = ?", (username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(400, "Username taken")
    
    pw_hash = hash_password(req.password)
    c.execute(f"INSERT INTO {TBL_USERS} (uname, pw_h) VALUES (?, ?)", (username, pw_hash))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return LoginResponse(success=True, token=create_session(user_id), username=username)

@app.post("/login")
async def login(req: LoginRequest, request: Request):
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip, "login", MAX_AUTH_ATTEMPTS):
        return LoginResponse(success=False, message="Too many attempts")
    
    # Check IP ban first
    ip_ban = is_user_banned(ip=client_ip)
    if ip_ban:
        return LoginResponse(success=False, message=f"Banned: {ip_ban.get('reason', 'No reason')}")
    
    username = sanitize_username(req.username)
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT id, uname, pw_h FROM {TBL_USERS} WHERE uname = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row or not verify_password(req.password, row["pw_h"]):
        return LoginResponse(success=False, message="Invalid credentials")
    
    # Check user ban
    user_ban = is_user_banned(user_id=row["id"])
    if user_ban:
        return LoginResponse(success=False, message=f"Banned: {user_ban.get('reason', 'No reason')}")
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE {TBL_USERS} SET l_at = ? WHERE id = ?", (time.time(), row["id"]))
    conn.commit()
    conn.close()
    
    return LoginResponse(success=True, token=create_session(row["id"]), username=row["uname"])

@app.get("/servers", response_model=ServerListResponse)
async def list_servers():
    conn = get_db()
    c = conn.cursor()
    c.execute(f"DELETE FROM {TBL_SERVERS} WHERE hb < ?", (time.time() - 90,))
    conn.commit()
    c.execute(f"SELECT id, n, h_ip, p, h_n, pw, pc, mp FROM {TBL_SERVERS} ORDER BY c_at DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    
    return ServerListResponse(servers=[{
        "id": r["id"], "name": r["n"], "host_ip": r["h_ip"], "port": r["p"],
        "host_name": r["h_n"] or "Player", "password_protected": bool(r["pw"]),
        "player_count": min(r["pc"], 10), "max_players": min(r["mp"], 10)
    } for r in rows])

class RegisterServerRequest(BaseModel):
    name: str
    port: int
    host_name: Optional[str] = "Player"
    password_protected: bool = False
    max_players: int = 2
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return sanitize_text(v, 30)
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v < 1024 or v > 65535:
            raise ValueError('Invalid port')
        return v
        
    @field_validator('max_players')
    @classmethod
    def validate_max_players(cls, v: int) -> int:
        if v < 2 or v > 16:
            raise ValueError('Max players must be 2-16')
        return v

@app.post("/servers/register")
async def register_server(req: RegisterServerRequest, request: Request):
    client_ip = get_client_ip(request)
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {TBL_SERVERS} WHERE h_ip = ?", (client_ip,))
    if c.fetchone()[0] >= 3:
        conn.close()
        raise HTTPException(400, "Too many servers")
    
    c.execute(f"INSERT INTO {TBL_SERVERS} (n, h_ip, p, h_n, pw, mp) VALUES (?, ?, ?, ?, ?, ?)",
              (req.name, client_ip, req.port, req.host_name, int(req.password_protected), req.max_players))
    server_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "server_id": server_id}

@app.post("/servers/{server_id}/heartbeat")
async def server_heartbeat(server_id: int, player_count: int = 1, request: Request = None):
    client_ip = get_client_ip(request) if request else "0.0.0.0"
    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE {TBL_SERVERS} SET hb = ?, pc = ? WHERE id = ? AND h_ip = ?",
              (time.time(), min(player_count, 10), server_id, client_ip))
    conn.commit()
    conn.close()
    return {"success": True}

@app.delete("/servers/{server_id}")
async def remove_server(server_id: int, request: Request):
    client_ip = get_client_ip(request)
    conn = get_db()
    c = conn.cursor()
    c.execute(f"DELETE FROM {TBL_SERVERS} WHERE id = ? AND h_ip = ?", (server_id, client_ip))
    conn.commit()
    conn.close()
    return {"success": True}

# === Internal Management Endpoints ===

class BanRequest(BaseModel):
    admin_key: Optional[str] = None # Optional now that tokens work
    username: Optional[str] = None
    user_id: Optional[int] = None
    ip: Optional[str] = None
    reason: str = "No reason provided"
    duration_days: Optional[int] = None  # None = permanent

class UnbanRequest(BaseModel):
    admin_key: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[int] = None
    ip: Optional[str] = None

@app.post("/api/v2/internal/mod/r")
async def admin_ban(req: BanRequest, request: Request):
    # Check Auth (Key OR Token)
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    
    if not is_admin_request(req.admin_key, token):
        raise HTTPException(403, "Unauthorized")
    
    conn = get_db()
    c = conn.cursor()
    
    # Resolve username to user_id if provided
    uid = req.user_id
    if req.username and not uid:
        c.execute(f"SELECT id FROM {TBL_USERS} WHERE uname = ?", (req.username,))
        row = c.fetchone()
        if row:
            uid = row["id"]
    
    if not uid and not req.ip:
        conn.close()
        raise HTTPException(400, "Must provide username, user_id, or ip")
    
    # Calculate expiration
    exp = None
    if req.duration_days:
        exp = time.time() + (req.duration_days * 24 * 3600)
    
    # Insert ban
    c.execute(f"INSERT INTO {TBL_BANS} (uid, ip, reason, banned_by, exp) VALUES (?, ?, ?, ?, ?)",
              (uid, req.ip, req.reason, "admin", exp))
    
    # Invalidate existing sessions for this user
    if uid:
        c.execute(f"DELETE FROM {TBL_SESSIONS} WHERE uid = ?", (uid,))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Banned user_id={uid} ip={req.ip}"}

@app.post("/api/v2/internal/mod/u")
async def admin_unban(req: UnbanRequest, request: Request):
    # Check Auth (Key OR Token)
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    
    if not is_admin_request(req.admin_key, token):
        raise HTTPException(403, "Unauthorized")
    
    conn = get_db()
    c = conn.cursor()
    
    # Resolve username to user_id if provided
    uid = req.user_id
    if req.username and not uid:
        c.execute(f"SELECT id FROM {TBL_USERS} WHERE uname = ?", (req.username,))
        row = c.fetchone()
        if row:
            uid = row["id"]
    
    # Remove bans
    if uid:
        c.execute(f"DELETE FROM {TBL_BANS} WHERE uid = ?", (uid,))
    if req.ip:
        c.execute(f"DELETE FROM {TBL_BANS} WHERE ip = ?", (req.ip,))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Unbanned"}

@app.get("/api/v2/internal/mod/l")
async def admin_list_bans(request: Request, admin_key: Optional[str] = None):
    # Check Auth (Key OR Token)
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
    
    if not is_admin_request(admin_key, token):
        raise HTTPException(403, "Unauthorized")
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"""
        SELECT b.id, b.uid, u.uname, b.ip, b.reason, b.c_at, b.exp
        FROM {TBL_BANS} b
        LEFT JOIN {TBL_USERS} u ON b.uid = u.id
        ORDER BY b.c_at DESC
        LIMIT 100
    """)
    rows = c.fetchall()
    conn.close()
    
    return {"bans": [{"id": r["id"], "user_id": r["uid"], "username": r["uname"],
                      "ip": r["ip"], "reason": r["reason"],
                      "created": r["c_at"], "expires": r["exp"]} for r in rows]}

# === Leaderboard / Stats ===

# === Leaderboard / Stats ===

class ScoreSubmitRequest(BaseModel):
    score: int
    max_score: int = 0
    song_hash: Optional[str] = None # Legacy
    song_name: Optional[str] = "Unknown"
    difficulty: Optional[str] = "MEDIUM"
    perfects: int = 0
    goods: int = 0
    bads: int = 0
    misses: int = 0

@app.post("/api/v2/stats/submit")
async def submit_score(req: ScoreSubmitRequest, request: Request):
    # Auth Check
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth_header.split(" ")[1]
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT uid FROM {TBL_SESSIONS} WHERE tk = ?", (token,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(401, "Invalid token")
    
    uid = row['uid']
    
    # Anticheat Validation
    if req.max_score > 0 and req.score > (req.max_score + 5000): # Loose tolerance
        print(f"ANTICHEAT: User {uid} submitted {req.score} but max is {req.max_score}")
        conn.close()
        raise HTTPException(400, "Score validation failed")
    
    # Calculate Grade
    acc = 0
    total = req.perfects + req.goods + req.bads + req.misses
    if total > 0:
        weighted = (req.perfects * 100 + req.goods * 75 + req.bads * 50)
        acc = (weighted / (total * 100)) * 100
        
    grade = "F"
    if acc >= 99: grade = "S"
    elif acc >= 95: grade = "A"
    elif acc >= 85: grade = "B"
    elif acc >= 75: grade = "C"
    elif acc >= 60: grade = "D"
    
    # Update Stats (Aggregate)
    db_update_stats(uid, req.score)
    
    # Log Score (Individual)
    c.execute("INSERT INTO s_logs (uid, song_name, difficulty, score, max_score, perfects, goods, bads, misses, grade) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (uid, req.song_name, req.difficulty, req.score, req.max_score, req.perfects, req.goods, req.bads, req.misses, grade))
    
    conn.commit()
    conn.close()
    
    return {"success": True}

@app.get("/api/v2/leaderboard")
async def get_leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute(f"""
        SELECT s.xp, s.lvl, s.t_score, u.uname 
        FROM {TBL_STATS} s
        JOIN {TBL_USERS} u ON s.uid = u.id
        ORDER BY s.xp DESC
        LIMIT 50
    """)
    rows = c.fetchall()
    conn.close()
    
    return {"leaderboard": [{"username": r["uname"], "xp": r["xp"], "level": r["lvl"], "score": r["t_score"]} for r in rows]}

@app.get("/api/v2/users/me")
async def get_my_stats(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"error": "No token"}
    token = auth_header.split(" ")[1]
    
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT uid FROM {TBL_SESSIONS} WHERE tk = ?", (token,))
    sess = c.fetchone()
    
    if not sess:
         conn.close()
         return {"error": "Invalid token"}
         
    uid = sess['uid']
    c.execute(f"SELECT * FROM {TBL_STATS} WHERE uid = ?", (uid,))
    stats = c.fetchone()
    
    # Get user info including admin status
    c.execute(f"SELECT uname, is_admin FROM {TBL_USERS} WHERE id = ?", (uid,))
    u_row = c.fetchone()
    
    # Advanced Stats
    # 1. Best Score
    c.execute("SELECT MAX(score) FROM s_logs WHERE uid = ?", (uid,))
    best_score = c.fetchone()[0] or 0
    
    # 2. Most Played Difficulty
    c.execute("SELECT difficulty, COUNT(*) as cnt FROM s_logs WHERE uid = ? GROUP BY difficulty ORDER BY cnt DESC LIMIT 1", (uid,))
    fav_diff_row = c.fetchone()
    fav_diff = fav_diff_row[0] if fav_diff_row else "NONE"
    
    # 3. Global Rank (by XP)
    # Count how many users have more XP than me
    my_xp = stats['xp'] if stats else 0
    c.execute(f"SELECT COUNT(*) FROM {TBL_STATS} WHERE xp > ?", (my_xp,))
    rank = c.fetchone()[0] + 1
    
    conn.close()
    
    res = {
        "username": u_row['uname'],
        "id": uid,
        "is_admin": bool(u_row['is_admin']),
        "stats": {
            "score": stats['t_score'] if stats else 0,
            "plays": stats['t_plays'] if stats else 0,
            "level": stats['lvl'] if stats else 1,
            "xp": stats['xp'] if stats else 0,
            "rank": rank,
            "best_score": best_score,
            "fav_difficulty": fav_diff
        }
    }
    return res

@app.post("/api/v2/news/webhook")
async def post_news_webhook(request: Request):
    # This endpoint accepts data pushing from an external source (like a Discord Bot or manual script)
    # Auth: Verify Secret or Admin Key
    auth_header = request.headers.get("Authorization") or request.headers.get("X-News-Secret")
    
    # Allow authentication via Admin Key for simplicity
    if not auth_header or not secrets.compare_digest(auth_header, ADMIN_API_KEY):
        raise HTTPException(403, "Unauthorized Webhook")
        
    try:
        data = await request.json()
        content = data.get("content")
        author = data.get("author", "SYSTEM")
        
        if not content:
            raise HTTPException(400, "Missing content")
            
        conn = get_db()
        c = conn.cursor()
        c.execute(f"INSERT INTO {TBL_NEWS} (content, author) VALUES (?, ?)", (content, author))
        conn.commit()
        conn.close()
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(400, f"Error processing webhook: {str(e)}")

@app.get("/api/v2/news")
async def get_news():
    # If using DB (cache)
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT content, author, ts FROM {TBL_NEWS} ORDER BY ts DESC LIMIT 10")
    rows = c.fetchall()
    
    # Poll Discord if cache is stale or empty (and token exists)
    should_poll = False
    if len(rows) == 0:
        should_poll = True
    elif rows and (time.time() - rows[0]['ts'] > 900): # 15 min stale
        should_poll = True
        
    if should_poll and DISCORD_BOT_TOKEN and NEWS_CHANNEL_ID:
        try:
            # print("Polling Discord...")
            url = f"https://discord.com/api/v10/channels/{NEWS_CHANNEL_ID}/messages?limit=5"
            headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
            
            if resp.status_code == 200:
                msgs = resp.json()
                # Clear old cache? Or just append? Let's generic replace for now to sync
                c.execute(f"DELETE FROM {TBL_NEWS}") 
                for m in msgs:
                     # Parse TS: 2025-12-31T22:00:00+00:00
                     # Simple workaround: use current time for sort, or parse if caring about precision
                     # For now, just insert
                     c.execute(f"INSERT INTO {TBL_NEWS} (content, author, ts) VALUES (?, ?, ?)", 
                               (m["content"], m["author"]["username"], time.time()))
                conn.commit()
                # Re-fetch
                c.execute(f"SELECT content, author, ts FROM {TBL_NEWS} ORDER BY ts DESC LIMIT 10")
                rows = c.fetchall()
        except Exception as e:
            print(f"Discord Poll Failed: {e}")
            
    conn.close()
    
    return {"news": [{
        "content": r["content"],
        "author": r["author"],
        "timestamp": r["ts"] * 1000 
    } for r in rows]}

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Server error"})

# Serve Static Website (Must be last to avoid overriding API routes)
from fastapi.staticfiles import StaticFiles
import os
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
