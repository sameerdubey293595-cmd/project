import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify, g
from openai import OpenAI
from dotenv import load_dotenv

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dreamlens-secret-key")

# ─────────────────────────────────────────────
# AI Provider — DigitalOcean GenAI (cloud) or Ollama (local)
# ─────────────────────────────────────────────
AI_PROVIDER = os.environ.get("AI_PROVIDER", "digitalocean").lower()

if AI_PROVIDER == "ollama":
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
    ai_client = OpenAI(
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
    )
    AI_MODEL = OLLAMA_MODEL
    print(f"✅ AI Provider: Ollama | Model: {AI_MODEL} | Base URL: {OLLAMA_BASE_URL}")
else:
    # DigitalOcean GenAI Platform (Open-weight Llama 3.3-70B)
    DO_MODEL = os.environ.get("DO_MODEL", "meta-llama/llama-3.3-70b-instruct")
    DO_KEY = os.environ.get("DIGITALOCEAN_API_KEY", "")
    OLLAMA_BASE_URL = None
    ai_client = OpenAI(
        api_key=DO_KEY,
        base_url="https://inference.do-ai.run/v1/",
    )
    AI_MODEL = DO_MODEL
    print(f"✅ AI Provider: DigitalOcean GenAI | Model: {AI_MODEL}")

# ─────────────────────────────────────────────
# Database — PostgreSQL (if DB_HOST provided) or local SQLite
# ─────────────────────────────────────────────
USE_POSTGRES = bool(os.environ.get("DB_HOST")) and PSYCOPG2_AVAILABLE
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "dreams.db")

def get_db():
    if USE_POSTGRES:
        return psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=int(os.environ.get("DB_PORT", 25060)),
            dbname=os.environ.get("DB_NAME", "defaultdb"),
            user=os.environ.get("DB_USER", "doadmin"),
            password=os.environ.get("DB_PASSWORD"),
            sslmode="require",
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    else:
        if "db" not in g:
            g.db = sqlite3.connect(SQLITE_PATH)
            g.db.row_factory = sqlite3.Row
        return g.db

@app.teardown_appcontext
def close_db(e=None):
    if not USE_POSTGRES:
        db = g.pop("db", None)
        if db is not None:
            db.close()

def init_db():
    if USE_POSTGRES:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dreams (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                dream_text TEXT NOT NULL,
                title TEXT,
                emotional_tone TEXT,
                archetype TEXT,
                dream_color TEXT,
                symbols JSONB,
                narrative TEXT,
                insight TEXT
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ DigitalOcean Managed PostgreSQL initialized.")
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dreams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT (datetime('now')),
                dream_text TEXT NOT NULL,
                title TEXT,
                emotional_tone TEXT,
                archetype TEXT,
                dream_color TEXT,
                symbols TEXT,
                narrative TEXT,
                insight TEXT
            );
        """)
        conn.commit()
        conn.close()
        print(f"✅ SQLite initialized at {SQLITE_PATH}")

try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization notice: {e}")

DREAM_ANALYST_SYSTEM_PROMPT = """You are DreamLens, a masterful dream analyst who blends Jungian psychology,
mythological symbolism, and literary sensitivity. When a user shares a dream with you, you produce a deeply
thoughtful, poetic, and psychologically rich analysis.

You MUST respond with ONLY a valid JSON object — no markdown code block, no explanation, just raw JSON.

The JSON must follow this exact schema:
{
  "title": "A short, poetic, evocative title for this dream (5-8 words)",
  "emotional_tone": "A 2-4 word emotional fingerprint of the dream (e.g. 'bittersweet longing', 'anxious wonder')",
  "archetype": "The dominant Jungian archetype present (e.g. 'The Shadow', 'The Hero', 'The Anima', 'The Trickster', 'The Wise Old Man', 'The Child')",
  "symbols": [
    {
      "symbol": "Name of the symbol found in the dream",
      "meaning": "Universal/mythological meaning of this symbol",
      "psychological_note": "What this symbol might be telling the dreamer personally"
    }
  ],
  "narrative": "A 2-paragraph literary rewrite of the dream in elegant third-person prose. Make it feel like a passage from a literary novel. Do not add new plot — only elevate the language and atmosphere of what was described.",
  "insight": "One profound psychological insight or reflection question for the dreamer. Should feel personal, warm, and non-clinical. Start with 'Your dream may be...' or 'Consider why...'",
  "dream_color": "A single hex color that best represents the mood of this dream (e.g. #4a2080 for a mysterious purple dream)"
}

Include 3 to 5 symbols. Do not include symbols not present or strongly implied in the dream text."""

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", ai_provider=AI_PROVIDER, ai_model=AI_MODEL)

@app.route("/api/info")
def api_info():
    return jsonify({
        "provider": AI_PROVIDER,
        "model": AI_MODEL,
        "base_url": OLLAMA_BASE_URL or "https://inference.do-ai.run/v1/",
    })

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    dream_text = (data or {}).get("dream_text", "").strip()

    if not dream_text:
        return jsonify({"error": "Dream text is required."}), 400
    if len(dream_text) < 15:
        return jsonify({"error": "Please describe your dream in a bit more detail (at least 15 characters)."}), 400
    if len(dream_text) > 5000:
        return jsonify({"error": "Dream too long — please keep it under 5000 characters."}), 400

    try:
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": DREAM_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": f"Here is my dream:\n\n{dream_text}"},
            ],
            max_tokens=1500,
            temperature=0.85,
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown code fences if model returned them
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{") and cleaned.endswith("}"):
                    raw = cleaned
                    break

        analysis = json.loads(raw)

        required = ["title", "emotional_tone", "archetype", "symbols", "narrative", "insight"]
        for field in required:
            if field not in analysis:
                raise ValueError(f"Missing field in response: {field}")

        return jsonify({"success": True, "analysis": analysis, "dream_text": dream_text})

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI model response formatting error. Please try again. ({str(e)})"}), 500
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/api/save", methods=["POST"])
def save_dream():
    data = request.get_json()
    dream_text = (data or {}).get("dream_text", "").strip()
    analysis = (data or {}).get("analysis", {})

    if not dream_text or not analysis:
        return jsonify({"error": "Dream text and analysis are required."}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        symbols_payload = json.dumps(analysis.get("symbols", []))

        if USE_POSTGRES:
            cur.execute(
                """
                INSERT INTO dreams
                  (dream_text, title, emotional_tone, archetype, dream_color, symbols, narrative, insight)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    dream_text,
                    analysis.get("title"),
                    analysis.get("emotional_tone"),
                    analysis.get("archetype"),
                    analysis.get("dream_color", "#6b46c1"),
                    symbols_payload,
                    analysis.get("narrative"),
                    analysis.get("insight"),
                ),
            )
            row = cur.fetchone()
            dream_id = row["id"]
            conn.commit()
            cur.close()
            conn.close()
        else:
            cur.execute(
                """
                INSERT INTO dreams
                  (dream_text, title, emotional_tone, archetype, dream_color, symbols, narrative, insight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dream_text,
                    analysis.get("title"),
                    analysis.get("emotional_tone"),
                    analysis.get("archetype"),
                    analysis.get("dream_color", "#6b46c1"),
                    symbols_payload,
                    analysis.get("narrative"),
                    analysis.get("insight"),
                ),
            )
            conn.commit()
            dream_id = cur.lastrowid

        return jsonify({
            "success": True,
            "id": dream_id,
            "message": "Dream saved to your journal! 🌙"
        })

    except Exception as e:
        return jsonify({"error": f"Could not save dream: {str(e)}"}), 500

@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        conn = get_db()
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """
                SELECT id, created_at, title, emotional_tone, archetype, dream_color
                FROM dreams
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
        else:
            cur.execute(
                """
                SELECT id, created_at, title, emotional_tone, archetype, dream_color
                FROM dreams
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
            rows = cur.fetchall()

        dreams = []
        for row in rows:
            created_at_val = row["created_at"]
            if hasattr(created_at_val, "isoformat"):
                created_at_str = created_at_val.isoformat()
            else:
                created_at_str = str(created_at_val)

            dreams.append({
                "id": row["id"],
                "created_at": created_at_str,
                "title": row["title"],
                "emotional_tone": row["emotional_tone"],
                "archetype": row["archetype"],
                "dream_color": row["dream_color"] or "#6b46c1",
            })

        return jsonify({"success": True, "dreams": dreams})

    except Exception as e:
        return jsonify({"error": f"Could not fetch history: {str(e)}"}), 500

@app.route("/api/dream/<int:dream_id>", methods=["GET"])
def get_dream(dream_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("SELECT * FROM dreams WHERE id = %s", (dream_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        else:
            cur.execute("SELECT * FROM dreams WHERE id = ?", (dream_id,))
            row = cur.fetchone()

        if not row:
            return jsonify({"error": "Dream not found."}), 404

        symbols_data = row["symbols"]
        if isinstance(symbols_data, str):
            try:
                symbols_data = json.loads(symbols_data)
            except Exception:
                pass

        created_at_val = row["created_at"]
        if hasattr(created_at_val, "isoformat"):
            created_at_str = created_at_val.isoformat()
        else:
            created_at_str = str(created_at_val)

        return jsonify({
            "success": True,
            "dream": {
                "id": row["id"],
                "created_at": created_at_str,
                "dream_text": row["dream_text"],
                "title": row["title"],
                "emotional_tone": row["emotional_tone"],
                "archetype": row["archetype"],
                "dream_color": row["dream_color"],
                "symbols": symbols_data,
                "narrative": row["narrative"],
                "insight": row["insight"],
            }
        })

    except Exception as e:
        return jsonify({"error": f"Could not fetch dream: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
