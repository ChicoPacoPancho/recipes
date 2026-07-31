"""Family Cookbook - Flask application entry point."""

import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from backend.database import init_db, get_db, IMAGES_DIR, rows_to_dicts

# Import route blueprints
from backend.routes.recipes import bp as recipes_bp
from backend.routes.members import bp as members_bp
from backend.routes.shopping import bp as shopping_bp
from backend.routes.cooking import bp as cooking_bp
from backend.routes.tags import bp as tags_bp
from backend.routes.import_recipe import bp as import_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__,
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'),
                static_url_path='')

    # Enable CORS for development
    CORS(app)

    # Max upload size: 10MB
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

    # Initialize database
    init_db()

    # Register blueprints
    app.register_blueprint(recipes_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(cooking_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(import_bp)

    # --- Settings routes ---

    @app.route('/api/settings')
    def get_settings():
        with get_db() as db:
            settings = db.execute("SELECT key, value FROM settings").fetchall()
            return jsonify({row['key']: row['value'] for row in settings})

    @app.route('/api/settings', methods=['PUT'])
    def update_settings():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        with get_db() as db:
            for key, value in data.items():
                db.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(value))
                )
            db.commit()
        return jsonify({"success": True})

    # --- Image serving ---

    @app.route('/api/images/<path:filename>')
    def serve_image(filename):
        return send_from_directory(IMAGES_DIR, filename)

    # --- Unit conversion endpoint ---

    @app.route('/api/convert')
    def convert_units():
        from backend.services.units import convert_unit, convert_temperature
        value = request.args.get('value', type=float)
        from_unit = request.args.get('from', '')
        to_unit = request.args.get('to', '')

        if value is None or not from_unit or not to_unit:
            return jsonify({"error": "value, from, and to are required"}), 400

        # Check if temperature
        temp_units = {'f', '°f', 'fahrenheit', 'c', '°c', 'celsius'}
        if from_unit.lower() in temp_units:
            result = convert_temperature(value, from_unit, to_unit)
            return jsonify({"value": result, "unit": to_unit})

        result_value, result_unit = convert_unit(value, from_unit, to_unit)
        if result_value is None:
            return jsonify({"error": "Cannot convert between these units"}), 400
        return jsonify({"value": result_value, "unit": result_unit})

    # --- Stats endpoint ---

    @app.route('/api/stats')
    def get_stats():
        with get_db() as db:
            recipe_count = db.execute(
                "SELECT COUNT(*) as count FROM recipes WHERE is_archived = 0"
            ).fetchone()['count']
            archived_count = db.execute(
                "SELECT COUNT(*) as count FROM recipes WHERE is_archived = 1"
            ).fetchone()['count']
            member_count = db.execute(
                "SELECT COUNT(*) as count FROM members WHERE is_active = 1"
            ).fetchone()['count']
            tag_count = db.execute(
                "SELECT COUNT(*) as count FROM tags"
            ).fetchone()['count']
            shopping_count = db.execute(
                "SELECT COUNT(*) as count FROM shopping_list WHERE is_checked = 0"
            ).fetchone()['count']
            return jsonify({
                "recipes": recipe_count,
                "archived_recipes": archived_count,
                "members": member_count,
                "tags": tag_count,
                "shopping_items": shopping_count,
            })

    # --- SPA fallback ---
    # Serve the frontend for any non-API route

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        # If it's an API route, return JSON 404
        if request.path.startswith('/api/'):
            return jsonify({"error": "Not found"}), 404
        # Otherwise serve the SPA
        return send_from_directory(app.static_folder, 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
