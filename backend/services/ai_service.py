"""AI service for recipe extraction from URLs and text."""

import json
import httpx
import re
from bs4 import BeautifulSoup


# System prompt for recipe extraction
EXTRACT_PROMPT = """You are a recipe extraction assistant. Extract recipe data from the provided content and return it as JSON.

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{
    "title": "Recipe title",
    "description": "Brief description of the dish",
    "prep_time_minutes": null or integer,
    "cook_time_minutes": null or integer,
    "servings": null or number,
    "servings_unit": "servings" or other unit,
    "image_url": null or "URL of the main recipe image",
    "tags": ["tag1", "tag2"],
    "ingredients": [
        {
            "name": "ingredient name",
            "quantity": null or number,
            "unit": null or "unit string",
            "group_name": null or "group name like 'For the sauce'",
            "is_optional": false,
            "notes": null or "any notes about this ingredient",
            "original_text": "original text as written"
        }
    ],
    "steps": [
        {
            "step_number": 1,
            "instruction": "Step instruction text",
            "duration_minutes": null or integer,
            "group_name": null or "group name",
            "original_text": "original text as written",
            "ingredient_names": ["ingredient names referenced in this step"]
        }
    ]
}

Important rules:
- Parse quantities as numbers (1.5 not "1 1/2")
- Separate the ingredient name from its quantity and unit
- Keep original_text as written in the source
- Identify which ingredients are referenced in each step
- Extract reasonable tags (cuisine type, meal type, dietary info, cooking method)
- If information is missing, use null
- Return ONLY JSON, no other text"""


async def fetch_url_content(url):
    """Fetch and clean content from a URL."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FamilyCookbook/1.0)'
        }
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def extract_recipe_html(html_content):
    """Extract relevant recipe content from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Try to find JSON-LD structured data first
    json_ld = None
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'Recipe':
                        json_ld = item
                        break
            elif isinstance(data, dict):
                if data.get('@type') == 'Recipe':
                    json_ld = data
                elif '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Recipe':
                            json_ld = item
                            break
        except (json.JSONDecodeError, TypeError):
            continue

    # Remove script, style, nav, footer elements
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Get text content (limited to avoid token explosion)
    text = soup.get_text(separator='\n', strip=True)
    # Limit to first 8000 chars
    text = text[:8000]

    # Find the main image
    image_url = None
    # Try og:image first
    og_image = soup.find('meta', property='og:image')
    if og_image:
        image_url = og_image.get('content')
    # Try the largest image
    if not image_url:
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'ad']):
                image_url = src
                break

    result = {
        'text': text,
        'image_url': image_url,
    }

    if json_ld:
        result['structured_data'] = json.dumps(json_ld, indent=2)

    return result


async def extract_recipe_with_ai(content, settings):
    """Send content to AI for recipe extraction."""
    provider = settings.get('ai_provider', 'ollama')
    base_url = settings.get('ai_base_url', 'http://localhost:11434')
    model = settings.get('ai_model', 'llama3.2')
    api_key = settings.get('ai_api_key', '')

    # Build the user message
    user_message = "Extract the recipe from this content:\n\n"
    if content.get('structured_data'):
        user_message += f"Structured data found:\n{content['structured_data']}\n\n"
    user_message += f"Page text:\n{content['text']}"

    if provider == 'ollama':
        return await _call_ollama(base_url, model, user_message)
    elif provider == 'openai':
        return await _call_openai_compatible(base_url, model, api_key, user_message)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")


async def _call_ollama(base_url, model, user_message):
    """Call Ollama API."""
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data.get('message', {}).get('content', '')
        return _parse_ai_response(content)


async def _call_openai_compatible(base_url, model, api_key, user_message):
    """Call OpenAI-compatible API (OpenAI, Anthropic via proxy, etc.)."""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {}
    if api_key:
        headers['Authorization'] = 'Bearer ' + api_key

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        return _parse_ai_response(content)


def _parse_ai_response(content):
    """Parse AI response to extract JSON recipe data."""
    # Try to parse directly
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the response
    brace_start = content.find('{')
    brace_end = content.rfind('}')
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(content[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse AI response as JSON")


async def extract_from_text(text, settings):
    """Extract recipe from raw text input."""
    content = {'text': text[:8000]}
    return await extract_recipe_with_ai(content, settings)
