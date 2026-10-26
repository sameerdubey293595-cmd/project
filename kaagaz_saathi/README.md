# 🌙 DreamLens — AI-Powered Dream Journal & Interpreter

> **Decode what your sleeping mind is trying to tell you.**  
> Powered by open-weight **Llama 3.3-70B** on **DigitalOcean GenAI Platform** — your dreams never leave DigitalOcean's servers.

---

## What is DreamLens?

DreamLens is a web app that takes your dream description and transforms it into:

- 📖 **A poetic auto-generated title** for your dream  
- 🎭 **Emotional tone** fingerprint  
- ♆ **Jungian archetype** detected (The Shadow, The Hero, The Trickster…)  
- ◈ **Symbol analysis** — 3–5 key dream symbols with psychological meanings  
- ✍️ **Literary rewrite** — your dream retold as elegant literary prose  
- 💡 **Personal insight** — a reflection question or psychological observation  

All results are saved to your **DigitalOcean Managed PostgreSQL** dream journal and accessible anytime.

---

## Why Open-Weight AI?

DreamLens uses **Llama 3.3-70B** — a fully open-weight model — served through **DigitalOcean GenAI Platform**. This matters because:

- **Privacy**: Your dreams (arguably the most private thing you have) are analyzed by a model running on infrastructure *you control*, not sent to a closed corporate AI.
- **Cost**: Open-weight models via DigitalOcean serverless inference cost a fraction of GPT-4 — making this sustainable to run at scale.
- **Flexibility**: You can swap to any other open model (Mistral, DeepSeek, Qwen) without changing your code — just change the model string.

---

## Tech Stack (100% DigitalOcean)

| Layer | Technology |
|---|---|
| **AI Inference** | DigitalOcean GenAI Platform (Llama 3.3-70B) |
| **Database** | DigitalOcean Managed PostgreSQL |
| **Hosting** | DigitalOcean App Platform |
| **Backend** | Python + Flask + Gunicorn |
| **Frontend** | Pure HTML/CSS/JS (no framework) |

---

## Setup & Deployment

### Step 1 — Get a DigitalOcean Account
Sign up at [digitalocean.com](https://digitalocean.com). You'll need:
1. A **Personal Access Token** (API → Tokens → Generate New Token)
2. A **Managed PostgreSQL** cluster (Database → Create → PostgreSQL)
3. **App Platform** for deployment

### Step 2 — Clone & Configure
```bash
git clone https://github.com/YOUR_USERNAME/dreamlens.git
cd dreamlens
cp .env.example .env
# Edit .env with your real values
```

### Step 3 — DigitalOcean GenAI Setup
1. Go to [cloud.digitalocean.com/gen-ai](https://cloud.digitalocean.com/gen-ai)
2. Under **Inference**, find the model catalog
3. Find `meta-llama/llama-3.3-70b-instruct` (Serverless Inference)
4. Use your DO Personal Access Token as the API key
5. Base URL: `https://inference.do-ai.run/v1/`

### Step 4 — Database Setup
The app auto-creates the `dreams` table on first startup. Just provide your Managed PostgreSQL connection details in `.env`.

### Step 5 — Deploy to DigitalOcean App Platform
```bash
# Push to GitHub, then connect repo in DigitalOcean App Platform
# OR use the spec file:
doctl apps create --spec .do/app.yaml
```

### Step 6 — Local Development
```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main UI |
| `POST` | `/api/analyze` | Analyze a dream with Llama 3.3 |
| `POST` | `/api/save` | Save dream + analysis to PostgreSQL |
| `GET` | `/api/history` | Last 10 saved dreams |
| `GET` | `/api/dream/<id>` | Full dream record by ID |

---

## Project Structure

```
dreamlens/
├── app.py              ← Flask backend + DigitalOcean AI integration
├── templates/
│   └── index.html      ← Full frontend (animated starfield UI)
├── requirements.txt    ← Python dependencies
├── Procfile            ← For DigitalOcean App Platform
├── .do/
│   └── app.yaml        ← App Platform deployment spec
├── .env.example        ← Environment variable template
└── README.md
```

---

## Built For

🎃 [Hacktoberfest Open-Source AI Challenge — Week 4](https://dev.to/challenges/hf26)  
**Category entered**: Best Use of DigitalOcean
# project
# project
# project
