"""Shopping list routes."""

from flask import Blueprint, request, jsonify
from backend.database import get_db, dict_from_row, rows_to_dicts

bp = Blueprint('shopping', __name__)


@bp.route('/api/shopping')
def get_shopping_list():
    """Get the shopping list, grouped by recipe."""
    with get_db() as db:
        items = rows_to_dicts(db.execute("""
            SELECT sl.*, r.title as recipe_title
            FROM shopping_list sl
            LEFT JOIN recipes r ON r.id = sl.recipe_id
            ORDER BY sl.is_checked ASC, r.title ASC, sl.added_at ASC
        """).fetchall())
        return jsonify(items)


@bp.route('/api/shopping/add-recipe/<int:recipe_id>', methods=['POST'])
def add_recipe_to_shopping(recipe_id):
    """Add all ingredients from a recipe to the shopping list."""
    data = request.get_json(silent=True) or {}
    scale = data.get('scale', 1.0)

    with get_db() as db:
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        ingredients = db.execute(
            "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
            (recipe_id,)
        ).fetchall()

        for ing in ingredients:
            quantity = ing['quantity']
            if quantity and scale != 1.0:
                quantity = round(quantity * scale, 3)

            db.execute("""
                INSERT INTO shopping_list
                    (recipe_id, ingredient_id, quantity, unit, name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                recipe_id, ing['id'], quantity, ing['unit'], ing['name']
            ))

        db.commit()
        return jsonify({"success": True, "count": len(ingredients)}), 201


@bp.route('/api/shopping/add-item', methods=['POST'])
def add_custom_item():
    """Add a custom item to the shopping list."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Name is required"}), 400

    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO shopping_list (custom_item, quantity, unit, name)
            VALUES (?, ?, ?, ?)
        """, (data['name'], data.get('quantity'), data.get('unit'), data['name']))
        db.commit()
        return jsonify({"id": cursor.lastrowid}), 201


@bp.route('/api/shopping/<int:item_id>/toggle', methods=['PUT'])
def toggle_item(item_id):
    """Toggle an item's checked state."""
    with get_db() as db:
        db.execute(
            "UPDATE shopping_list SET is_checked = NOT is_checked WHERE id = ?",
            (item_id,)
        )
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/shopping/<int:item_id>', methods=['DELETE'])
def remove_item(item_id):
    """Remove an item from the shopping list."""
    with get_db() as db:
        db.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/shopping/clear-checked', methods=['POST'])
def clear_checked():
    """Remove all checked items from the shopping list."""
    with get_db() as db:
        db.execute("DELETE FROM shopping_list WHERE is_checked = 1")
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/shopping/clear-all', methods=['POST'])
def clear_all():
    """Clear the entire shopping list."""
    with get_db() as db:
        db.execute("DELETE FROM shopping_list")
        db.commit()
        return jsonify({"success": True})
