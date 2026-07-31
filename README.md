# 🍳 Family Cookbook

A private recipe app designed for a single household. Not a social platform — a shared family cookbook that becomes more useful over time.

## Features

- **Recipe Management** — Create, edit, clone, and archive recipes with discrete ingredients and steps
- **AI Import** — Extract recipes from URLs or raw text using a local AI (Ollama) or OpenAI-compatible API
- **Cooking Mode** — Distraction-free step-by-step view with relevant ingredients inline and a manual timer
- **Shopping List** — Add recipe ingredients to a single shared list, grouped by recipe, check off items as you shop
- **Search & Filter** — Full-text search by title, description, ingredient, tags, cooking time, and source site
- **Recipe Scaling** — Adjust servings and all ingredient quantities scale automatically
- **Unit Conversion** — Toggle between metric and imperial measurements
- **Ratings & Stickers** — Household members rate recipes with stars, emoji stickers, and short comments (fun for kids!)
- **Notes** — Leave public or private notes on recipes for yourself or the whole household
- **Related Recipes** — Link recipes that go together, are prerequisites, or are alternatives
- **Cooking Time Tracking** — Track actual cooking time per household member with averages
- **Tags** — Free-form tags plus two computed tags: "Quick" (configurable threshold) and "Favourite" (high avg rating)
- **PWA** — Installable on Android/iOS home screen, works offline for viewing cached recipes
- **Mobile-First** — Designed for phone use in the kitchen

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python / Flask |
| Database | SQLite (single file, FTS5 full-text search) |
| Frontend | Svelte 4 + Vite + Tailwind CSS |
| AI | Ollama (local, free) or OpenAI-compatible API |
| Deployment | Docker / Docker Compose |

## Quick Start

### With Docker (recommended)

```bash
docker compose up --build
```

Open http://localhost:5000 in your browser.

### For Development

Prerequisites: Python 3.10+, Node.js 18+

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start both servers
./start.sh
```

- Frontend dev server: http://localhost:5173 (with hot reload)
- Backend API: http://localhost:5000

### Production (without Docker)

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 "backend.app:create_app()"
```

## AI Recipe Import Setup

The app can extract recipes from website URLs using AI. Configure in **Settings → AI Recipe Import**.

### Option 1: Ollama (Free, Local, Recommended)

1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull llama3.2`
3. In Settings, set:
   - Provider: `Ollama (Local)`
   - Base URL: `http://localhost:11434`
   - Model: `llama3.2`

### Option 2: OpenAI-Compatible API

1. Get an API key from OpenAI, Anthropic, or any compatible provider
2. In Settings, set:
   - Provider: `OpenAI Compatible`
   - Base URL: `https://api.openai.com` (or your provider's URL)
   - Model: `gpt-4o-mini` (or your preferred model)
   - API Key: your key

## Backup

The entire database is a single file. Back it up:

```bash
# If using Docker
docker compose exec cookbook cp /app/data/recipes.db /app/data/recipes.db.bak

# If running directly
cp data/recipes.db data/recipes.db.bak
```

For automated backups, add a cron job:
```bash
0 3 * * * cp /path/to/data/recipes.db /path/to/backups/recipes-$(date +\%Y\%m\%d).db
```

## Project Structure

```
├── backend/
│   ├── app.py              # Flask application entry point
│   ├── database.py          # SQLite schema and connection management
│   ├── routes/
│   │   ├── recipes.py       # Recipe CRUD, search, notes, ratings, related
│   │   ├── members.py       # Household member management
│   │   ├── shopping.py      # Shopping list operations
│   │   ├── cooking.py       # Cooking session tracking
│   │   ├── tags.py          # Tag management
│   │   └── import_recipe.py # AI recipe import
│   └── services/
│       ├── ai_service.py    # AI provider abstraction
│       └── units.py         # Unit conversion and scaling
├── frontend/
│   ├── src/
│   │   ├── App.svelte       # Root component with routing
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable UI components
│   │   └── lib/             # API client, stores, utilities
│   └── public/              # PWA manifest, service worker, icons
├── docker-compose.yml
├── Dockerfile
└── start.sh                 # Development startup script
```

## Design Decisions

- **SQLite** — Zero maintenance, one-file backup, handles hundreds of recipes easily, FTS5 for instant search
- **No ORM** — Direct SQL queries for simplicity and transparency
- **PWA over native app** — Cross-platform via browser, no app store overhead, single codebase
- **Honor system auth** — Simple member selection, no passwords; a parent can record a child's rating
- **Single shopping list** — No multi-list management complexity; clear and add as needed
- **Original data preserved** — Imported recipe data stored as JSON; user edits never destroy the original
- **Svelte** — Compiles to small, fast vanilla JS; minimal runtime overhead
