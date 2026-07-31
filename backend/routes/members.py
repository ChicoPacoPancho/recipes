"""Household member routes."""

from flask import Blueprint, request, jsonify
from backend.database import get_db, dict_from_row, rows_to_dicts

bp = Blueprint('members', __name__)


@bp.route('/api/members')
def list_members():
    """List all household members."""
    with get_db() as db:
        members = rows_to_dicts(
            db.execute("SELECT * FROM members WHERE is_active = 1 ORDER BY name").fetchall()
        )
        return jsonify(members)


@bp.route('/api/members', methods=['POST'])
def create_member():
    """Create a new household member."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Name is required"}), 400

    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO members (name, avatar) VALUES (?, ?)",
                (data['name'], data.get('avatar', '👤'))
            )
            db.commit()
            return jsonify({"id": cursor.lastrowid}), 201
        except Exception:
            return jsonify({"error": "A member with that name already exists"}), 409


@bp.route('/api/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Update a household member."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    with get_db() as db:
        db.execute(
            "UPDATE members SET name = COALESCE(?, name), avatar = COALESCE(?, avatar) WHERE id = ?",
            (data.get('name'), data.get('avatar'), member_id)
        )
        db.commit()
        return jsonify({"success": True})


@bp.route('/api/members/<int:member_id>', methods=['DELETE'])
def deactivate_member(member_id):
    """Deactivate a household member (soft delete)."""
    with get_db() as db:
        db.execute("UPDATE members SET is_active = 0 WHERE id = ?", (member_id,))
        db.commit()
        return jsonify({"success": True})
