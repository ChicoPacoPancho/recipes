/**
 * API client for the Family Cookbook backend.
 */

const BASE = '/api';

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  if (config.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// --- Recipes ---

export const recipes = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return request(`/recipes${query ? '?' + query : ''}`);
  },
  get(id, params = {}) {
    const query = new URLSearchParams(params).toString();
    return request(`/recipes/${id}${query ? '?' + query : ''}`);
  },
  create(data) {
    return request('/recipes', { method: 'POST', body: data });
  },
  update(id, data) {
    return request(`/recipes/${id}`, { method: 'PUT', body: data });
  },
  archive(id) {
    return request(`/recipes/${id}/archive`, { method: 'POST' });
  },
  unarchive(id) {
    return request(`/recipes/${id}/unarchive`, { method: 'POST' });
  },
  clone(id, data = {}) {
    return request(`/recipes/${id}/clone`, { method: 'POST', body: data });
  },
};

// --- Notes ---

export const notes = {
  list(recipeId, memberId) {
    const params = memberId ? `?member_id=${memberId}` : '';
    return request(`/recipes/${recipeId}/notes${params}`);
  },
  create(recipeId, data) {
    return request(`/recipes/${recipeId}/notes`, { method: 'POST', body: data });
  },
  update(recipeId, noteId, data) {
    return request(`/recipes/${recipeId}/notes/${noteId}`, { method: 'PUT', body: data });
  },
  delete(recipeId, noteId) {
    return request(`/recipes/${recipeId}/notes/${noteId}`, { method: 'DELETE' });
  },
};

// --- Ratings ---

export const ratings = {
  upsert(recipeId, data) {
    return request(`/recipes/${recipeId}/ratings`, { method: 'POST', body: data });
  },
};

// --- Related Recipes ---

export const related = {
  list(recipeId) {
    return request(`/recipes/${recipeId}/related`);
  },
  add(recipeId, data) {
    return request(`/recipes/${recipeId}/related`, { method: 'POST', body: data });
  },
  remove(recipeId, relatedId) {
    return request(`/recipes/${recipeId}/related/${relatedId}`, { method: 'DELETE' });
  },
};

// --- Members ---

export const members = {
  list() {
    return request('/members');
  },
  create(data) {
    return request('/members', { method: 'POST', body: data });
  },
  update(id, data) {
    return request(`/members/${id}`, { method: 'PUT', body: data });
  },
  delete(id) {
    return request(`/members/${id}`, { method: 'DELETE' });
  },
};

// --- Shopping List ---

export const shopping = {
  list() {
    return request('/shopping');
  },
  addRecipe(recipeId, scale = 1.0) {
    return request(`/shopping/add-recipe/${recipeId}`, {
      method: 'POST',
      body: { scale },
    });
  },
  addItem(data) {
    return request('/shopping/add-item', { method: 'POST', body: data });
  },
  toggle(id) {
    return request(`/shopping/${id}/toggle`, { method: 'PUT' });
  },
  remove(id) {
    return request(`/shopping/${id}`, { method: 'DELETE' });
  },
  clearChecked() {
    return request('/shopping/clear-checked', { method: 'POST' });
  },
  clearAll() {
    return request('/shopping/clear-all', { method: 'POST' });
  },
};

// --- Cooking ---

export const cooking = {
  start(data) {
    return request('/cooking/start', { method: 'POST', body: data });
  },
  stop(sessionId, data) {
    return request(`/cooking/${sessionId}/stop`, { method: 'PUT', body: data });
  },
  discard(sessionId) {
    return request(`/cooking/${sessionId}/discard`, { method: 'DELETE' });
  },
};

// --- Tags ---

export const tags = {
  list() {
    return request('/tags');
  },
  create(data) {
    return request('/tags', { method: 'POST', body: data });
  },
  delete(id) {
    return request(`/tags/${id}`, { method: 'DELETE' });
  },
};

// --- Import ---

export const importRecipe = {
  fromUrl(url) {
    return request('/import/url', { method: 'POST', body: { url } });
  },
  fromText(text) {
    return request('/import/text', { method: 'POST', body: { text } });
  },
  downloadImage(url) {
    return request('/import/image', { method: 'POST', body: { url } });
  },
};

// --- Upload ---

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append('image', file);
  return request('/upload/image', {
    method: 'POST',
    body: formData,
  });
}

// --- Settings ---

export const settings = {
  get() {
    return request('/settings');
  },
  update(data) {
    return request('/settings', { method: 'PUT', body: data });
  },
};

// --- Stats ---

export const stats = {
  get() {
    return request('/stats');
  },
};

// --- Source Sites ---

export const sourceSites = {
  list() {
    return request('/source-sites');
  },
};

// --- Image URL helper ---

export function imageUrl(filename) {
  if (!filename) return null;
  return `/api/images/${filename}`;
}
