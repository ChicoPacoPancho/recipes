import sqlite3
import os
from contextlib import contextmanager

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
DATABASE_PATH = os.path.join(DATA_DIR, 'recipes.db')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')


@contextmanager
def get_db():
    """Get a database connection with WAL mode and foreign keys enabled."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


def init_db():
    """Initialize the database schema."""
    with get_db() as db:
        db.executescript(SCHEMA)
        db.commit()
        # Insert default settings if not present
        defaults = [
            ('unit_system', 'imperial'),
            ('quick_recipe_threshold', '30'),
            ('ai_provider', 'ollama'),
            ('ai_base_url', 'http://localhost:11434'),
            ('ai_model', 'llama3.2'),
            ('ai_api_key', ''),
            ('household_name', 'Our Family'),
        ]
        for key, value in defaults:
            db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        db.commit()


SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    avatar TEXT DEFAULT '👤',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    source_url TEXT,
    source_site TEXT,
    image_filename TEXT,
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    servings REAL,
    servings_unit TEXT DEFAULT 'servings',
    created_by INTEGER REFERENCES members(id),
    is_archived INTEGER DEFAULT 0,
    original_data TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts USING fts5(
    title, description, content='recipes', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS recipes_fts_insert AFTER INSERT ON recipes BEGIN
    INSERT INTO recipes_fts(rowid, title, description)
    VALUES (new.id, new.title, new.description);
END;

CREATE TRIGGER IF NOT EXISTS recipes_fts_delete AFTER DELETE ON recipes BEGIN
    INSERT INTO recipes_fts(recipes_fts, rowid, title, description)
    VALUES ('delete', old.id, old.title, old.description);
END;

CREATE TRIGGER IF NOT EXISTS recipes_fts_update AFTER UPDATE ON recipes BEGIN
    INSERT INTO recipes_fts(recipes_fts, rowid, title, description)
    VALUES ('delete', old.id, old.title, old.description);
    INSERT INTO recipes_fts(rowid, title, description)
    VALUES (new.id, new.title, new.description);
END;

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    original_text TEXT,
    group_name TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_optional INTEGER DEFAULT 0,
    notes TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS ingredients_fts USING fts5(
    name, content='ingredients', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS ingredients_fts_insert AFTER INSERT ON ingredients BEGIN
    INSERT INTO ingredients_fts(rowid, name) VALUES (new.id, new.name);
END;

CREATE TRIGGER IF NOT EXISTS ingredients_fts_delete AFTER DELETE ON ingredients BEGIN
    INSERT INTO ingredients_fts(ingredients_fts, rowid, name)
    VALUES ('delete', old.id, old.name);
END;

CREATE TRIGGER IF NOT EXISTS ingredients_fts_update AFTER UPDATE ON ingredients BEGIN
    INSERT INTO ingredients_fts(ingredients_fts, rowid, name)
    VALUES ('delete', old.id, old.name);
    INSERT INTO ingredients_fts(rowid, name) VALUES (new.id, new.name);
END;

CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    original_text TEXT,
    duration_minutes INTEGER,
    group_name TEXT
);

CREATE TABLE IF NOT EXISTS step_ingredients (
    step_id INTEGER NOT NULL REFERENCES steps(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    PRIMARY KEY (step_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    is_ai_suggested INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recipe_tags (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, tag_id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    content TEXT NOT NULL,
    is_private INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    score INTEGER CHECK(score BETWEEN 1 AND 5),
    sticker TEXT,
    comment TEXT,
    rated_by INTEGER REFERENCES members(id),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(recipe_id, member_id)
);

CREATE TABLE IF NOT EXISTS related_recipes (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    related_recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'related'
        CHECK(relationship_type IN ('related', 'prerequisite', 'alternative', 'goes_with')),
    PRIMARY KEY (recipe_id, related_recipe_id)
);

CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
    ingredient_id INTEGER REFERENCES ingredients(id) ON DELETE SET NULL,
    custom_item TEXT,
    quantity REAL,
    unit TEXT,
    name TEXT NOT NULL,
    is_checked INTEGER DEFAULT 0,
    added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cooking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    started_at TEXT,
    ended_at TEXT,
    duration_seconds INTEGER,
    is_complete INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""
