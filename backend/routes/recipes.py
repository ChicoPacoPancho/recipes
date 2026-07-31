"""Recipe CRUD and search routes."""

import json
from flask import Blueprint, request, jsonify
from backend.database import get_db, dict_from_row, rows_to_dicts
from backend.services.units import convert_to_system, scale_quantity, format_quantity

bp = Blueprint('recipes', __name__)


@bp.route('/api/recipes')
def list_recipes():
    """List recipes with optional search and filtering."""
    q = request.args.get('q', '').strip()
    tag = request.args.get('tag', '').strip()
    ingredient = request.args.get('ingredient', '').strip()
    max_time = request.args.get('max_time', type=int)
    source_site = request.args.get('source_site', '').strip()
    favourites_of = request.args.get('favourites_of', type=int)
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    include_archived = request.args.get('include_archived', 'false') == 'true'

    with get_db() as db:
        conditions = []
        params = []

        if not include_archived:
            conditions.append("r.is_archived = 0")

        # Full-text search on title/description
        if q:
            conditions.append("r.id IN (SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?)")
            # Add wildcards for prefix matching
            params.append(f'{q}*')

        # Filter by tag
        if tag:
            conditions.append("""r.id IN (
                SELECT rt.recipe_id FROM recipe_tags rt
                JOIN tags t ON t.id = rt.tag_id
                WHERE t.name = ?
            )""")
            params.append(tag)

        # Filter by ingredient
        if ingredient:
            conditions.append("""r.id IN (
                SELECT i.recipe_id FROM ingredients i
                JOIN ingredients_fts ON ingredients_fts.rowid = i.id
                WHERE ingredients_fts MATCH ?
            )""")
            params.append(f'{ingredient}*')

        # Filter by max total time
        if max_time is not None:
            conditions.append(
                "(COALESCE(r.prep_time_minutes, 0) + COALESCE(r.cook_time_minutes, 0)) <= ?"
            )
            params.append(max_time)

        # Filter by source site
        if source_site:
            conditions.append("r.source_site = ?")
            params.append(source_site)

        # Filter by favourites (rating >= 4 by a specific member)
        if favourites_of:
            conditions.append("""r.id IN (
                SELECT rat.recipe_id FROM ratings rat
                WHERE rat.member_id = ? AND rat.score >= 4
            )""")
            params.append(favourites_of)

        where = " AND ".join(conditions) if conditions else "1=1"

        # Validate sort column
        allowed_sorts = ['updated_at', 'created_at', 'title', 'prep_time_minutes', 'cook_time_minutes']
        if sort not in allowed_sorts:
            sort = 'updated_at'
        order_dir = 'DESC' if order.lower() == 'desc' else 'ASC'

        query = f"""
            SELECT r.*,
                (SELECT GROUP_CONCAT(t.name, ', ')
                 FROM recipe_tags rt JOIN tags t ON t.id = rt.tag_id
                 WHERE rt.recipe_id = r.id) as tag_list,
                (SELECT ROUND(AVG(rat.score), 1)
                 FROM ratings rat WHERE rat.recipe_id = r.id) as avg_rating,
                (SELECT COUNT(*) FROM ratings rat
                 WHERE rat.recipe_id = r.id) as rating_count
            FROM recipes r
            WHERE {where}
            ORDER BY r.{sort} {order_dir}
        """

        recipes = rows_to_dicts(db.execute(query, params).fetchall())

        # Add computed tags
        settings = dict(db.execute("SELECT key, value FROM settings").fetchall())
        quick_threshold = int(settings.get('quick_recipe_threshold', 30))

        for recipe in recipes:
            computed_tags = []
            total_time = (recipe.get('prep_time_minutes') or 0) + (recipe.get('cook_time_minutes') or 0)
            if 0 < total_time <= quick_threshold:
                computed_tags.append('Quick')
            if recipe.get('avg_rating') and recipe['avg_rating'] >= 4:
                computed_tags.append('Favourite')
            recipe['computed_tags'] = computed_tags

        return jsonify(recipes)


@bp.route('/api/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    """Get a single recipe with all details."""
    unit_system = request.args.get('units')
    target_servings = request.args.get('servings', type=float)

    with get_db() as db:
        recipe = dict_from_row(
            db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        )
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        # Get default unit system from settings if not specified
        if not unit_system:
            row = db.execute("SELECT value FROM settings WHERE key = 'unit_system'").fetchone()
            unit_system = row['value'] if row else 'imperial'

        # Get ingredients
        ingredients = rows_to_dicts(
            db.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
                (recipe_id,)
            ).fetchall()
        )

        # Apply scaling and unit conversion
        original_servings = recipe.get('servings')
        for ing in ingredients:
            ing['display_quantity'] = ing['quantity']
            ing['display_unit'] = ing['unit']

            # Scale if needed
            if target_servings and original_servings:
                ing['display_quantity'] = scale_quantity(
                    ing['quantity'], original_servings, target_servings
                )

            # Convert units if needed
            if ing['display_quantity'] and ing['display_unit']:
                converted_qty, converted_unit = convert_to_system(
                    ing['display_quantity'], ing['display_unit'], unit_system
                )
                ing['display_quantity'] = converted_qty
                ing['display_unit'] = converted_unit

            ing['formatted_quantity'] = format_quantity(ing['display_quantity'])

        recipe['ingredients'] = ingredients

        # Get steps
        steps = rows_to_dicts(
            db.execute(
                "SELECT * FROM steps WHERE recipe_id = ? ORDER BY step_number",
                (recipe_id,)
            ).fetchall()
        )

        # Get step-ingredient associations
        for step in steps:
            step_ings = rows_to_dicts(
                db.execute("""
                    SELECT i.* FROM step_ingredients si
                    JOIN ingredients i ON i.id = si.ingredient_id
                    WHERE si.step_id = ?
                    ORDER BY i.sort_order
                """, (step['id'],)).fetchall()
            )
            # Apply same scaling/conversion to step ingredients
            for ing in step_ings:
                ing['display_quantity'] = ing['quantity']
                ing['display_unit'] = ing['unit']
                if target_servings and original_servings:
                    ing['display_quantity'] = scale_quantity(
                        ing['quantity'], original_servings, target_servings
                    )
                if ing['display_quantity'] and ing['display_unit']:
                    converted_qty, converted_unit = convert_to_system(
                        ing['display_quantity'], ing['display_unit'], unit_system
                    )
                    ing['display_quantity'] = converted_qty
                    ing['display_unit'] = converted_unit
                ing['formatted_quantity'] = format_quantity(ing['display_quantity'])
            step['ingredients'] = step_ings

        recipe['steps'] = steps

        # Get tags
        tags = rows_to_dicts(
            db.execute("""
                SELECT t.* FROM recipe_tags rt
                JOIN tags t ON t.id = rt.tag_id
                WHERE rt.recipe_id = ?
                ORDER BY t.name
            """, (recipe_id,)).fetchall()
        )
        recipe['tags'] = tags

        # Computed tags
        settings = dict(db.execute("SELECT key, value FROM settings").fetchall())
        quick_threshold = int(settings.get('quick_recipe_threshold', 30))
        computed_tags = []
        total_time = (recipe.get('prep_time_minutes') or 0) + (recipe.get('cook_time_minutes') or 0)
        if 0 < total_time <= quick_threshold:
            computed_tags.append('Quick')
        avg_rating = db.execute(
            "SELECT AVG(score) as avg FROM ratings WHERE recipe_id = ?", (recipe_id,)
        ).fetchone()
        if avg_rating and avg_rating['avg'] and avg_rating['avg'] >= 4:
            computed_tags.append('Favourite')
        recipe['computed_tags'] = computed_tags

        # Get notes
        notes = rows_to_dicts(
            db.execute("""
                SELECT n.*, m.name as member_name, m.avatar as member_avatar
                FROM notes n
                JOIN members m ON m.id = n.member_id
                WHERE n.recipe_id = ?
                ORDER BY n.created_at DESC
            """, (recipe_id,)).fetchall()
        )
        recipe['notes'] = notes

        # Get ratings
        ratings = rows_to_dicts(
            db.execute("""
                SELECT rat.*, m.name as member_name, m.avatar as member_avatar,
                       rb.name as rated_by_name
                FROM ratings rat
                JOIN members m ON m.id = rat.member_id
                LEFT JOIN members rb ON rb.id = rat.rated_by
                WHERE rat.recipe_id = ?
            """, (recipe_id,)).fetchall()
        )
        recipe['ratings'] = ratings

        # Get related recipes
        related = rows_to_dicts(
            db.execute("""
                SELECT rr.relationship_type, r.id, r.title, r.image_filename,
                       r.prep_time_minutes, r.cook_time_minutes
                FROM related_recipes rr
                JOIN recipes r ON r.id = rr.related_recipe_id
                WHERE rr.recipe_id = ? AND r.is_archived = 0
            """, (recipe_id,)).fetchall()
        )
        recipe['related_recipes'] = related

        # Get cooking stats
        stats = db.execute("""
            SELECT
                member_id,
                m.name as member_name,
                COUNT(*) as session_count,
                ROUND(AVG(duration_seconds)) as avg_duration_seconds
            FROM cooking_sessions cs
            JOIN members m ON m.id = cs.member_id
            WHERE cs.recipe_id = ? AND cs.is_complete = 1
            GROUP BY cs.member_id
        """, (recipe_id,)).fetchall()
        recipe['cooking_stats'] = rows_to_dicts(stats)

        household_avg = db.execute("""
            SELECT ROUND(AVG(duration_seconds)) as avg_duration_seconds,
                   COUNT(*) as total_sessions
            FROM cooking_sessions
            WHERE recipe_id = ? AND is_complete = 1
        """, (recipe_id,)).fetchone()
        recipe['household_avg_cook_time'] = dict_from_row(household_avg)

        if target_servings:
            recipe['scaled_servings'] = target_servings

        return jsonify(recipe)


@bp.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Create a new recipe."""
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400

    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO recipes (title, description, source_url, source_site,
                               image_filename, prep_time_minutes, cook_time_minutes,
                               servings, servings_unit, created_by, original_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data.get('description'),
            data.get('source_url'),
            data.get('source_site'),
            data.get('image_filename'),
            data.get('prep_time_minutes'),
            data.get('cook_time_minutes'),
            data.get('servings'),
            data.get('servings_unit', 'servings'),
            data.get('created_by'),
            json.dumps(data.get('original_data')) if data.get('original_data') else None,
        ))
        recipe_id = cursor.lastrowid

        # Insert ingredients
        _save_ingredients(db, recipe_id, data.get('ingredients', []))

        # Insert steps
        _save_steps(db, recipe_id, data.get('steps', []))

        # Insert tags
        _save_tags(db, recipe_id, data.get('tags', []))

        db.commit()
        return jsonify({"id": recipe_id}), 201


@bp.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update a recipe."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    with get_db() as db:
        existing = db.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Recipe not found"}), 404

        db.execute("""
            UPDATE recipes SET
                title = COALESCE(?, title),
                description = ?,
                source_url = ?,
                source_site = ?,
                image_filename = COALESCE(?, image_filename),
                prep_time_minutes = ?,
                cook_time_minutes = ?,
                servings = ?,
                servings_unit = COALESCE(?, servings_unit),
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get('title'),
            data.get('description'),
            data.get('source_url'),
            data.get('source_site'),
            data.get('image_filename'),
            data.get('prep_time_minutes'),
            data.get('cook_time_minutes'),
            data.get('servings'),
            data.get('servings_unit'),
            recipe_id,
        ))

        # Replace ingredients if provided
        if 'ingredients' in data:
            db.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
            _save_ingredients(db, recipe_id, data['ingredients'])

        # Replace steps if provided
        if 'steps' in data:
            db.execute("DELETE FROM steps WHERE recipe_id = ?", (recipe_id,))
            _save_steps(db, recipe_id, data['steps'])

        # Replace tags if provided
        if 'tags' in data:
            db.execute("DELETE FROM recipe_tags WHERE recipe_id = ?", (recipe_id,))
            _save_tags(db, recipe_id, data['tags'])

        db.commit()
        return jsonify({"success": True})


@bp.route('/api/recipes/<int:recipe_id>/archive', methods=['POST'])
def archive_recipe(recipe_id):
    """Archive a recipe and remove its shopping list items."""
    with get_db() as db:
        db.execute(
            "UPDATE recipes SET is_archived = 1, updated_at = datetime('now') WHERE id = ?",
            (recipe_id,)
        )
        db.execute("DELETE FROM shopping_list WHERE recipe_id = ?", (recipe_id,))
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/recipes/<int:recipe_id>/unarchive', methods=['POST'])
def unarchive_recipe(recipe_id):
    """Unarchive a recipe."""
    with get_db() as db:
        db.execute(
            "UPDATE recipes SET is_archived = 0, updated_at = datetime('now') WHERE id = ?",
            (recipe_id,)
        )
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/recipes/<int:recipe_id>/clone', methods=['POST'])
def clone_recipe(recipe_id):
    """Clone a recipe to create a new one based on it."""
    with get_db() as db:
        original = dict_from_row(
            db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        )
        if not original:
            return jsonify({"error": "Recipe not found"}), 404

        data = request.get_json() or {}
        new_title = data.get('title', f"{original['title']} (Copy)")

        cursor = db.execute("""
            INSERT INTO recipes (title, description, source_url, source_site,
                               image_filename, prep_time_minutes, cook_time_minutes,
                               servings, servings_unit, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_title,
            original['description'],
            original['source_url'],
            original['source_site'],
            original['image_filename'],
            original['prep_time_minutes'],
            original['cook_time_minutes'],
            original['servings'],
            original['servings_unit'],
            data.get('created_by', original['created_by']),
        ))
        new_id = cursor.lastrowid

        # Clone ingredients
        ingredients = rows_to_dicts(
            db.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
                (recipe_id,)
            ).fetchall()
        )
        _save_ingredients(db, new_id, ingredients)

        # Clone steps
        steps = rows_to_dicts(
            db.execute(
                "SELECT * FROM steps WHERE recipe_id = ? ORDER BY step_number",
                (recipe_id,)
            ).fetchall()
        )
        _save_steps(db, new_id, steps)

        # Clone tags
        tags = rows_to_dicts(
            db.execute("""
                SELECT t.name FROM recipe_tags rt
                JOIN tags t ON t.id = rt.tag_id
                WHERE rt.recipe_id = ?
            """, (recipe_id,)).fetchall()
        )
        _save_tags(db, new_id, [t['name'] for t in tags])

        # Add as related recipe (alternative)
        db.execute(
            "INSERT OR IGNORE INTO related_recipes VALUES (?, ?, 'alternative')",
            (new_id, recipe_id)
        )
        db.execute(
            "INSERT OR IGNORE INTO related_recipes VALUES (?, ?, 'alternative')",
            (recipe_id, new_id)
        )

        db.commit()
        return jsonify({"id": new_id}), 201


# --- Notes ---

@bp.route('/api/recipes/<int:recipe_id>/notes')
def get_notes(recipe_id):
    """Get notes for a recipe."""
    member_id = request.args.get('member_id', type=int)
    with get_db() as db:
        if member_id:
            notes = rows_to_dicts(db.execute("""
                SELECT n.*, m.name as member_name, m.avatar as member_avatar
                FROM notes n JOIN members m ON m.id = n.member_id
                WHERE n.recipe_id = ? AND (n.is_private = 0 OR n.member_id = ?)
                ORDER BY n.created_at DESC
            """, (recipe_id, member_id)).fetchall())
        else:
            notes = rows_to_dicts(db.execute("""
                SELECT n.*, m.name as member_name, m.avatar as member_avatar
                FROM notes n JOIN members m ON m.id = n.member_id
                WHERE n.recipe_id = ? AND n.is_private = 0
                ORDER BY n.created_at DESC
            """, (recipe_id,)).fetchall())
        return jsonify(notes)


@bp.route('/api/recipes/<int:recipe_id>/notes', methods=['POST'])
def create_note(recipe_id):
    """Add a note to a recipe."""
    data = request.get_json()
    if not data or not data.get('content') or not data.get('member_id'):
        return jsonify({"error": "content and member_id are required"}), 400

    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO notes (recipe_id, member_id, content, is_private)
            VALUES (?, ?, ?, ?)
        """, (recipe_id, data['member_id'], data['content'], data.get('is_private', 0)))
        db.commit()
        return jsonify({"id": cursor.lastrowid}), 201


@bp.route('/api/recipes/<int:recipe_id>/notes/<int:note_id>', methods=['PUT'])
def update_note(recipe_id, note_id):
    """Update a note."""
    data = request.get_json()
    with get_db() as db:
        db.execute("""
            UPDATE notes SET content = ?, is_private = ?, updated_at = datetime('now')
            WHERE id = ? AND recipe_id = ?
        """, (data.get('content'), data.get('is_private', 0), note_id, recipe_id))
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/recipes/<int:recipe_id>/notes/<int:note_id>', methods=['DELETE'])
def delete_note(recipe_id, note_id):
    """Delete a note."""
    with get_db() as db:
        db.execute("DELETE FROM notes WHERE id = ? AND recipe_id = ?", (note_id, recipe_id))
        db.commit()
        return jsonify({"success": True})


# --- Ratings ---

@bp.route('/api/recipes/<int:recipe_id>/ratings', methods=['POST'])
def upsert_rating(recipe_id):
    """Add or update a rating for a recipe."""
    data = request.get_json()
    if not data or not data.get('member_id'):
        return jsonify({"error": "member_id is required"}), 400

    with get_db() as db:
        db.execute("""
            INSERT INTO ratings (recipe_id, member_id, score, sticker, comment, rated_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(recipe_id, member_id)
            DO UPDATE SET score = ?, sticker = ?, comment = ?, rated_by = ?,
                         updated_at = datetime('now')
        """, (
            recipe_id, data['member_id'], data.get('score'), data.get('sticker'),
            data.get('comment'), data.get('rated_by'),
            data.get('score'), data.get('sticker'), data.get('comment'), data.get('rated_by'),
        ))
        db.commit()
        return jsonify({"success": True})


# --- Related Recipes ---

@bp.route('/api/recipes/<int:recipe_id>/related')
def get_related(recipe_id):
    """Get related recipes."""
    with get_db() as db:
        related = rows_to_dicts(db.execute("""
            SELECT rr.relationship_type, r.id, r.title, r.image_filename,
                   r.prep_time_minutes, r.cook_time_minutes
            FROM related_recipes rr
            JOIN recipes r ON r.id = rr.related_recipe_id
            WHERE rr.recipe_id = ? AND r.is_archived = 0
        """, (recipe_id,)).fetchall())
        return jsonify(related)


@bp.route('/api/recipes/<int:recipe_id>/related', methods=['POST'])
def add_related(recipe_id):
    """Add a related recipe."""
    data = request.get_json()
    if not data or not data.get('related_recipe_id'):
        return jsonify({"error": "related_recipe_id is required"}), 400

    rel_type = data.get('relationship_type', 'related')
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO related_recipes VALUES (?, ?, ?)",
            (recipe_id, data['related_recipe_id'], rel_type)
        )
        # Add reverse relationship
        reverse_type = rel_type
        if rel_type == 'prerequisite':
            reverse_type = 'goes_with'
        db.execute(
            "INSERT OR IGNORE INTO related_recipes VALUES (?, ?, ?)",
            (data['related_recipe_id'], recipe_id, reverse_type)
        )
        db.commit()
        return jsonify({"success": True}), 201


@bp.route('/api/recipes/<int:recipe_id>/related/<int:related_id>', methods=['DELETE'])
def remove_related(recipe_id, related_id):
    """Remove a related recipe link."""
    with get_db() as db:
        db.execute(
            "DELETE FROM related_recipes WHERE recipe_id = ? AND related_recipe_id = ?",
            (recipe_id, related_id)
        )
        db.execute(
            "DELETE FROM related_recipes WHERE recipe_id = ? AND related_recipe_id = ?",
            (related_id, recipe_id)
        )
        db.commit()
        return jsonify({"success": True})


# --- Helper functions ---

def _save_ingredients(db, recipe_id, ingredients):
    """Save ingredients for a recipe."""
    for i, ing in enumerate(ingredients):
        db.execute("""
            INSERT INTO ingredients
                (recipe_id, name, quantity, unit, original_text, group_name,
                 sort_order, is_optional, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_id,
            ing.get('name', ''),
            ing.get('quantity'),
            ing.get('unit'),
            ing.get('original_text'),
            ing.get('group_name'),
            ing.get('sort_order', i),
            ing.get('is_optional', 0),
            ing.get('notes'),
        ))


def _save_steps(db, recipe_id, steps):
    """Save steps for a recipe. Also links step-ingredient associations."""
    with get_db() as lookup_db:
        # Get all ingredients for this recipe to match by name
        recipe_ingredients = rows_to_dicts(
            lookup_db.execute(
                "SELECT id, name FROM ingredients WHERE recipe_id = ?", (recipe_id,)
            ).fetchall()
        )

    for i, step in enumerate(steps):
        cursor = db.execute("""
            INSERT INTO steps
                (recipe_id, step_number, instruction, original_text,
                 duration_minutes, group_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            recipe_id,
            step.get('step_number', i + 1),
            step.get('instruction', ''),
            step.get('original_text'),
            step.get('duration_minutes'),
            step.get('group_name'),
        ))
        step_id = cursor.lastrowid

        # Link ingredients to this step
        ingredient_names = step.get('ingredient_names', [])
        if ingredient_names:
            for ing_name in ingredient_names:
                for ing in recipe_ingredients:
                    if ing['name'].lower() in ing_name.lower() or ing_name.lower() in ing['name'].lower():
                        db.execute(
                            "INSERT OR IGNORE INTO step_ingredients VALUES (?, ?)",
                            (step_id, ing['id'])
                        )
                        break


def _save_tags(db, recipe_id, tags):
    """Save tags for a recipe. Creates new tags as needed."""
    for tag_name in tags:
        if isinstance(tag_name, dict):
            tag_name = tag_name.get('name', '')
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        # Get or create tag
        existing = db.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
        if existing:
            tag_id = existing['id']
        else:
            cursor = db.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = cursor.lastrowid

        db.execute(
            "INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)",
            (recipe_id, tag_id)
        )
