"""Tag management routes."""

from flask import Blueprint, request, jsonify
from backend.database import get_db, rows_to_dicts

bp = Blueprint('tags', __name__)


@bp.route('/api/tags')
def list_tags():
    """List all tags with recipe counts."""
    with get_db() as db:
        tags = rows_to_dicts(db.execute("""
            SELECT t.*,
                   (SELECT COUNT(*) FROM recipe_tags rt WHERE rt.tag_id = t.id) as recipe_count
            FROM tags t
            ORDER BY t.name
        """).fetchall())
        return jsonify(tags)


@bp.route('/api/tags', methods=['POST'])
def create_tag():
    """Create a new tag."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Name is required"}), 400

    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO tags (name) VALUES (?)", (data['name'].strip(),)
            )
            db.commit()
            return jsonify({"id": cursor.lastrowid}), 201
        except Exception:
            # Tag already exists
            tag = db.execute(
                "SELECT id FROM tags WHERE name = ?", (data['name'].strip(),)
            ).fetchone()
            return jsonify({"id": tag['id']}), 200


@bp.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a tag."""
    with get_db() as db:
        db.execute("DELETE FROM recipe_tags WHERE tag_id = ?", (tag_id,))
        db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/source-sites')
def list_source_sites():
    """List all unique source sites."""
    with get_db() as db:
        sites = db.execute("""
            SELECT DISTINCT source_site, COUNT(*) as recipe_count
            FROM recipes
            WHERE source_site IS NOT NULL AND source_site != ''
            AND is_archived = 0
            GROUP BY source_site
            ORDER BY recipe_count DESC
        """).fetchall()
        return jsonify(rows_to_dicts(sites))
