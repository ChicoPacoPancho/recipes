"""Cooking session routes."""

from flask import Blueprint, request, jsonify
from backend.database import get_db, dict_from_row, rows_to_dicts

bp = Blueprint('cooking', __name__)


@bp.route('/api/cooking/start', methods=['POST'])
def start_session():
    """Start a cooking session."""
    data = request.get_json()
    if not data or not data.get('recipe_id') or not data.get('member_id'):
        return jsonify({"error": "recipe_id and member_id are required"}), 400

    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO cooking_sessions (recipe_id, member_id, started_at)
            VALUES (?, ?, datetime('now'))
        """, (data['recipe_id'], data['member_id']))
        db.commit()
        return jsonify({"id": cursor.lastrowid}), 201


@bp.route('/api/cooking/<int:session_id>/stop', methods=['PUT'])
def stop_session(session_id):
    """Stop a cooking session and record duration."""
    data = request.get_json() or {}

    with get_db() as db:
        session = dict_from_row(
            db.execute("SELECT * FROM cooking_sessions WHERE id = ?", (session_id,)).fetchone()
        )
        if not session:
            return jsonify({"error": "Session not found"}), 404

        duration = data.get('duration_seconds')
        is_complete = data.get('is_complete', 1)

        db.execute("""
            UPDATE cooking_sessions
            SET ended_at = datetime('now'),
                duration_seconds = ?,
                is_complete = ?
            WHERE id = ?
        """, (duration, is_complete, session_id))
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/cooking/<int:session_id>/discard', methods=['DELETE'])
def discard_session(session_id):
    """Discard a cooking session (don't count it)."""
    with get_db() as db:
        db.execute("DELETE FROM cooking_sessions WHERE id = ?", (session_id,))
        db.commit()
        return jsonify({"success": True})
