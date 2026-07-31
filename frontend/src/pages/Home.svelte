<script>
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { recipes, tags as tagsApi } from '../lib/api.js';
  import { formatTime } from '../lib/utils.js';
  import { imageUrl } from '../lib/api.js';
  import RecipeCard from '../components/RecipeCard.svelte';

  let recipeList = [];
  let allTags = [];
  let loading = true;
  let searchQuery = '';
  let selectedTag = '';
  let maxTime = '';
  let showFilters = false;
  let searchTimeout;

  onMount(loadRecipes);

  async function loadRecipes() {
    loading = true;
    try {
      const params = {};
      if (searchQuery) params.q = searchQuery;
      if (selectedTag) params.tag = selectedTag;
      if (maxTime) params.max_time = maxTime;
      recipeList = await recipes.list(params);
    } catch (e) {
      console.error('Failed to load recipes:', e);
    }
    loading = false;
  }

  async function loadTags() {
    try {
      allTags = await tagsApi.list();
    } catch (e) {
      console.error('Failed to load tags:', e);
    }
  }

  function handleSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadRecipes, 300);
  }

  function selectTag(tagName) {
    selectedTag = selectedTag === tagName ? '' : tagName;
    loadRecipes();
  }

  function clearFilters() {
    searchQuery = '';
    selectedTag = '';
    maxTime = '';
    loadRecipes();
  }

  // Load tags when filters are shown
  $: if (showFilters && allTags.length === 0) loadTags();
</script>

<div class="page-container">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-2xl font-bold text-gray-900">🍳 Recipes</h1>
  </div>

  <!-- Search bar -->
  <div class="relative mb-3">
    <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
    <input
      type="search"
      bind:value={searchQuery}
      on:input={handleSearch}
      placeholder="Search recipes..."
      class="input pl-10 pr-10"
    />
    <button
      on:click={() => showFilters = !showFilters}
      class="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md
             {showFilters || selectedTag || maxTime ? 'text-cookbook-600' : 'text-gray-400'}
             hover:bg-gray-100">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
      </svg>
    </button>
  </div>

  <!-- Filters -->
  {#if showFilters}
    <div class="card p-3 mb-4 space-y-3">
      <div>
        <label class="label">Max Total Time (minutes)</label>
        <input type="number" bind:value={maxTime} on:change={loadRecipes}
               placeholder="e.g. 30" class="input" min="1" />
      </div>

      {#if allTags.length > 0}
        <div>
          <label class="label">Tags</label>
          <div class="flex flex-wrap gap-1.5">
            {#each allTags as tag}
              <button
                on:click={() => selectTag(tag.name)}
                class="badge {selectedTag === tag.name ? 'bg-cookbook-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}">
                {tag.name}
                <span class="ml-1 opacity-60">{tag.recipe_count}</span>
              </button>
            {/each}
          </div>
        </div>
      {/if}

      {#if searchQuery || selectedTag || maxTime}
        <button on:click={clearFilters} class="btn-ghost btn-sm text-red-500">
          Clear all filters
        </button>
      {/if}
    </div>
  {/if}

  <!-- Recipe grid -->
  {#if loading}
    <div class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-cookbook-500 border-t-transparent"></div>
    </div>
  {:else if recipeList.length === 0}
    <div class="text-center py-20">
      <p class="text-6xl mb-4">📖</p>
      {#if searchQuery || selectedTag || maxTime}
        <p class="text-gray-500">No recipes match your search.</p>
        <button on:click={clearFilters} class="btn-ghost btn-sm mt-2">Clear filters</button>
      {:else}
        <p class="text-gray-500 mb-2">Your cookbook is empty!</p>
        <p class="text-sm text-gray-400 mb-4">Add your first recipe to get started.</p>
        <a href="/recipe/new" use:link class="btn-primary">Create Recipe</a>
        <span class="mx-2 text-gray-300">or</span>
        <a href="/import" use:link class="btn-secondary">Import from URL</a>
      {/if}
    </div>
  {:else}
    <div class="grid grid-cols-2 gap-3">
      {#each recipeList as recipe (recipe.id)}
        <RecipeCard {recipe} />
      {/each}
    </div>
  {/if}
</div>
