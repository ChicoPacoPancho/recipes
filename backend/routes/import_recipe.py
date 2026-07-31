"""AI recipe import routes."""

import asyncio
import os
import uuid
import httpx
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify
from backend.database import get_db, IMAGES_DIR
from backend.services.ai_service import (
    fetch_url_content, extract_recipe_html, extract_recipe_with_ai, extract_from_text
)

bp = Blueprint('import_recipe', __name__)


def _get_settings():
    """Get AI-related settings from the database."""
    with get_db() as db:
        rows = db.execute("SELECT key, value FROM settings").fetchall()
        return {row['key']: row['value'] for row in rows}


def _run_async(coro):
    """Run an async function from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@bp.route('/api/import/url', methods=['POST'])
def import_from_url():
    """Import a recipe from a URL using AI extraction."""
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({"error": "URL is required"}), 400

    url = data['url']
    settings = _get_settings()

    try:
        # Fetch URL content
        html = _run_async(fetch_url_content(url))

        # Extract relevant content
        content = extract_recipe_html(html)

        # Send to AI for extraction
        recipe_data = _run_async(extract_recipe_with_ai(content, settings))

        # Add source URL and site
        recipe_data['source_url'] = url
        recipe_data['source_site'] = urlparse(url).netloc.replace('www.', '')

        # Use image from AI response or from page scraping
        image_url = recipe_data.get('image_url') or content.get('image_url')
        if image_url:
            recipe_data['image_url'] = image_url

        # Store original data
        recipe_data['original_data'] = recipe_data.copy()

        return jsonify(recipe_data)

    except httpx.HTTPError as e:
        return jsonify({"error": f"Could not fetch URL: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Could not parse recipe: {str(e)}"}), 422
    except Exception as e:
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@bp.route('/api/import/text', methods=['POST'])
def import_from_text():
    """Import a recipe from raw text using AI extraction."""
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "Text is required"}), 400

    settings = _get_settings()

    try:
        recipe_data = _run_async(extract_from_text(data['text'], settings))
        recipe_data['original_data'] = recipe_data.copy()
        return jsonify(recipe_data)
    except ValueError as e:
        return jsonify({"error": f"Could not parse recipe: {str(e)}"}), 422
    except Exception as e:
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@bp.route('/api/import/image', methods=['POST'])
def download_image():
    """Download an image from a URL and save it locally."""
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({"error": "URL is required"}), 400

    try:
        response = _run_async(_fetch_image(data['url']))
        if not response:
            return jsonify({"error": "Could not download image"}), 400

        # Determine file extension
        content_type = response.headers.get('content-type', '')
        ext = 'jpg'
        if 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'

        # Save with unique filename
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(IMAGES_DIR, filename)
        os.makedirs(IMAGES_DIR, exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return jsonify({"filename": filename})

    except Exception as e:
        return jsonify({"error": f"Image download failed: {str(e)}"}), 500


async def _fetch_image(url):
    """Fetch an image from a URL."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; FamilyCookbook/1.0)'
        })
        response.raise_for_status()
        return response


@bp.route('/api/upload/image', methods=['POST'])
def upload_image():
    """Upload an image file."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    allowed = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({"error": f"File type not allowed. Use: {', '.join(allowed)}"}), 400

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(IMAGES_DIR, filename)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    file.save(filepath)

    return jsonify({"filename": filename})
