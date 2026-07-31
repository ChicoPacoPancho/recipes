<script>
  import { onMount } from 'svelte';
  import { push, link } from 'svelte-spa-router';
  import { recipes, shopping, notes as notesApi, ratings as ratingsApi, imageUrl } from '../lib/api.js';
  import { currentMember, unitSystem, shoppingCount, showToast } from '../lib/stores.js';
  import { formatTime, formatQuantity } from '../lib/utils.js';
  import Rating from '../components/Rating.svelte';
  import Modal from '../components/Modal.svelte';

  export let params = {};

  let recipe = null;
  let loading = true;
  let scaledServings = null;
  let showNoteForm = false;
  let newNote = '';
  let newNotePrivate = false;
  let showRatingModal = false;
  let showRelated = false;

  $: recipeId = parseInt(params.id);
  $: if (recipeId) loadRecipe();

  async function loadRecipe() {
    loading = true;
    try {
      const queryParams = {};
      if (scaledServings) queryParams.servings = scaledServings;
      if ($unitSystem) queryParams.units = $unitSystem;
      recipe = await recipes.get(recipeId, queryParams);
      if (!scaledServings && recipe.servings) {
        scaledServings = recipe.servings;
      }
    } catch (e) {
      showToast('Failed to load recipe', 'error');
    }
    loading = false;
  }

  function changeServings(delta) {
    const newVal = (scaledServings || 1) + delta;
    if (newVal >= 0.5) {
      scaledServings = newVal;
      loadRecipe();
    }
  }

  function toggleUnits() {
    $unitSystem = $unitSystem === 'metric' ? 'imperial' : 'metric';
    loadRecipe();
  }

  async function addToShoppingList() {
    try {
      const scale = recipe.servings ? scaledServings / recipe.servings : 1;
      await shopping.addRecipe(recipeId, scale);
      const items = await shopping.list();
      $shoppingCount = items.filter(i => !i.is_checked).length;
      showToast('Added to shopping list!');
    } catch (e) {
      showToast('Failed to add to shopping list', 'error');
    }
  }

  async function submitNote() {
    if (!newNote.trim() || !$currentMember) return;
    try {
      await notesApi.create(recipeId, {
        member_id: $currentMember.id,
        content: newNote,
        is_private: newNotePrivate ? 1 : 0,
      });
      newNote = '';
      newNotePrivate = false;
      showNoteForm = false;
      loadRecipe();
      showToast('Note added!');
    } catch (e) {
      showToast('Failed to add note', 'error');
    }
  }

  async function deleteNote(noteId) {
    try {
      await notesApi.delete(recipeId, noteId);
      loadRecipe();
    } catch (e) {
      showToast('Failed to delete note', 'error');
    }
  }

  async function archiveRecipe() {
    if (!confirm('Archive this recipe? It will be removed from search and shopping list.')) return;
    try {
      await recipes.archive(recipeId);
      showToast('Recipe archived');
      push('/');
    } catch (e) {
      showToast('Failed to archive recipe', 'error');
    }
  }

  async function cloneRecipe() {
    try {
      const result = await recipes.clone(recipeId, { created_by: $currentMember?.id });
      showToast('Recipe cloned!');
      push(`/recipe/${result.id}/edit`);
    } catch (e) {
      showToast('Failed to clone recipe', 'error');
    }
  }

  function startCooking() {
    push(`/recipe/${recipeId}/cook`);
  }
</script>

{#if loading}
  <div class="page-container flex items-center justify-center py-20">
    <div class="animate-spin rounded-full h-8 w-8 border-2 border-cookbook-500 border-t-transparent"></div>
  </div>
{:else if recipe}
  <div class="page-container">
    <!-- Back button -->
    <a href="/" use:link class="inline-flex items-center text-sm text-gray-500 mb-3 hover:text-gray-700">
      ← Back to recipes
    </a>

    <!-- Hero image -->
    {#if recipe.image_filename}
      <div class="rounded-xl overflow-hidden mb-4 -mx-4">
        <img src={imageUrl(recipe.image_filename)} alt={recipe.title}
             class="w-full h-48 object-cover" />
      </div>
    {/if}

    <!-- Title & meta -->
    <h1 class="text-2xl font-bold mb-1">{recipe.title}</h1>

    {#if recipe.source_url}
      <a href={recipe.source_url} target="_blank" rel="noopener"
         class="text-sm text-cookbook-600 hover:underline mb-2 block">
        📎 {recipe.source_site || 'View source'}
      </a>
    {/if}

    {#if recipe.description}
      <p class="text-gray-600 text-sm mb-3">{recipe.description}</p>
    {/if}

    <!-- Time & servings -->
    <div class="flex flex-wrap gap-3 mb-4 text-sm">
      {#if recipe.prep_time_minutes}
        <div class="flex items-center gap-1 text-gray-600">
          <span>🔪</span> Prep: {formatTime(recipe.prep_time_minutes)}
        </div>
      {/if}
      {#if recipe.cook_time_minutes}
        <div class="flex items-center gap-1 text-gray-600">
          <span>🔥</span> Cook: {formatTime(recipe.cook_time_minutes)}
        </div>
      {/if}
      {#if recipe.household_avg_cook_time?.avg_duration_seconds}
        <div class="flex items-center gap-1 text-gray-500 text-xs">
          <span>👨‍👩‍👧‍👦</span> Avg: {formatTime(Math.round(recipe.household_avg_cook_time.avg_duration_seconds / 60))}
        </div>
      {/if}
    </div>

    <!-- Tags -->
    {#if (recipe.tags?.length > 0) || (recipe.computed_tags?.length > 0)}
      <div class="flex flex-wrap gap-1.5 mb-4">
        {#each recipe.computed_tags || [] as tag}
          <span class="badge-computed">{tag}</span>
        {/each}
        {#each recipe.tags || [] as tag}
          <span class="badge-primary">{tag.name}</span>
        {/each}
      </div>
    {/if}

    <!-- Ratings -->
    {#if recipe.ratings?.length > 0}
      <div class="card p-3 mb-4">
        <h3 class="font-semibold text-sm mb-2">Ratings</h3>
        <div class="flex flex-wrap gap-3">
          {#each recipe.ratings as rating}
            <div class="flex items-center gap-1.5 text-sm">
              <span class="text-lg">{rating.member_avatar}</span>
              <div>
                <span class="font-medium">{rating.member_name}</span>
                {#if rating.sticker}
                  <span class="text-lg ml-1">{rating.sticker}</span>
                {/if}
                {#if rating.score}
                  <span class="text-amber-500 ml-1">{'⭐'.repeat(rating.score)}</span>
                {/if}
                {#if rating.comment}
                  <p class="text-xs text-gray-500">{rating.comment}</p>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Servings & scaling -->
    {#if recipe.servings}
      <div class="flex items-center gap-3 mb-4 card p-3">
        <span class="text-sm font-medium text-gray-700">Servings:</span>
        <button on:click={() => changeServings(-1)}
                class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 text-lg">−</button>
        <span class="text-lg font-bold min-w-[2rem] text-center">{scaledServings}</span>
        <button on:click={() => changeServings(1)}
                class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 text-lg">+</button>
        <span class="text-sm text-gray-500">{recipe.servings_unit || 'servings'}</span>
        <button on:click={toggleUnits}
                class="ml-auto btn-ghost btn-sm text-xs">
          {$unitSystem === 'metric' ? '🇺🇸 Imperial' : '🌍 Metric'}
        </button>
      </div>
    {/if}

    <!-- Ingredients -->
    <div class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Ingredients</h2>
      {#each recipe.ingredients || [] as ing, i}
        {#if i === 0 || ing.group_name !== recipe.ingredients[i-1]?.group_name}
          {#if ing.group_name}
            <h3 class="font-semibold text-sm text-gray-600 mt-3 mb-1">{ing.group_name}</h3>
          {/if}
        {/if}
        <div class="flex items-start gap-2 py-1.5 border-b border-gray-50 last:border-0
                    {ing.is_optional ? 'opacity-60' : ''}">
          <div class="flex-1">
            <span class="font-medium text-cookbook-700">
              {ing.formatted_quantity || ''}
              {ing.display_unit || ''}
            </span>
            <span>{ing.name}</span>
            {#if ing.is_optional}
              <span class="text-xs text-gray-400">(optional)</span>
            {/if}
            {#if ing.notes}
              <span class="text-xs text-gray-500"> — {ing.notes}</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Steps -->
    <div class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Instructions</h2>
      {#each recipe.steps || [] as step, i}
        {#if i === 0 || step.group_name !== recipe.steps[i-1]?.group_name}
          {#if step.group_name}
            <h3 class="font-semibold text-sm text-gray-600 mt-4 mb-2">{step.group_name}</h3>
          {/if}
        {/if}
        <div class="flex gap-3 py-3 border-b border-gray-50 last:border-0">
          <div class="flex-shrink-0 w-7 h-7 rounded-full bg-cookbook-100 text-cookbook-700
                      flex items-center justify-center text-sm font-bold">
            {step.step_number}
          </div>
          <div class="flex-1">
            <p class="text-sm leading-relaxed">{step.instruction}</p>
            {#if step.ingredients?.length > 0}
              <div class="mt-1.5 flex flex-wrap gap-1">
                {#each step.ingredients as ing}
                  <span class="text-xs bg-cookbook-50 text-cookbook-700 px-1.5 py-0.5 rounded">
                    {ing.formatted_quantity || ''} {ing.display_unit || ''} {ing.name}
                  </span>
                {/each}
              </div>
            {/if}
            {#if step.duration_minutes}
              <span class="text-xs text-gray-400 mt-1 block">⏱ {formatTime(step.duration_minutes)}</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Notes -->
    <div class="card p-4 mb-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="font-bold text-lg">Notes</h2>
        <button on:click={() => showNoteForm = !showNoteForm} class="btn-ghost btn-sm">
          {showNoteForm ? 'Cancel' : '+ Add Note'}
        </button>
      </div>

      {#if showNoteForm}
        <div class="mb-3 space-y-2">
          <textarea bind:value={newNote} class="input" rows="3"
                    placeholder="Add a note about this recipe..."></textarea>
          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" bind:checked={newNotePrivate} class="rounded" />
              Private (only you can see)
            </label>
            <button on:click={submitNote} class="btn-primary btn-sm"
                    disabled={!newNote.trim() || !$currentMember}>
              Save Note
            </button>
          </div>
          {#if !$currentMember}
            <p class="text-xs text-red-500">Select a member in Settings first</p>
          {/if}
        </div>
      {/if}

      {#each recipe.notes || [] as note}
        <div class="py-2 border-b border-gray-50 last:border-0">
          <div class="flex items-center gap-2 mb-1">
            <span>{note.member_avatar}</span>
            <span class="font-medium text-sm">{note.member_name}</span>
            {#if note.is_private}
              <span class="text-xs text-gray-400">🔒 Private</span>
            {/if}
            <span class="text-xs text-gray-400 ml-auto">{new Date(note.created_at).toLocaleDateString()}</span>
            {#if $currentMember?.id === note.member_id}
              <button on:click={() => deleteNote(note.id)} class="text-xs text-red-400 hover:text-red-600">×</button>
            {/if}
          </div>
          <p class="text-sm text-gray-700">{note.content}</p>
        </div>
      {:else}
        <p class="text-sm text-gray-400">No notes yet.</p>
      {/each}
    </div>

    <!-- Related Recipes -->
    {#if recipe.related_recipes?.length > 0}
      <div class="card p-4 mb-4">
        <h2 class="font-bold text-lg mb-3">Related Recipes</h2>
        {#each recipe.related_recipes as rel}
          <a href="/recipe/{rel.id}" use:link
             class="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0 hover:bg-gray-50 rounded">
            {#if rel.image_filename}
              <img src={imageUrl(rel.image_filename)} alt="" class="w-12 h-12 rounded-lg object-cover" />
            {:else}
              <div class="w-12 h-12 rounded-lg bg-cookbook-50 flex items-center justify-center">🍽️</div>
            {/if}
            <div>
              <p class="font-medium text-sm">{rel.title}</p>
              <span class="text-xs text-gray-400">{rel.relationship_type}</span>
            </div>
          </a>
        {/each}
      </div>
    {/if}

    <!-- Cooking Stats -->
    {#if recipe.cooking_stats?.length > 0}
      <div class="card p-4 mb-4">
        <h2 class="font-bold text-lg mb-3">Cooking Times</h2>
        {#each recipe.cooking_stats as stat}
          <div class="flex justify-between text-sm py-1">
            <span>{stat.member_name}</span>
            <span class="text-gray-500">
              ~{formatTime(Math.round(stat.avg_duration_seconds / 60))}
              ({stat.session_count} {stat.session_count === 1 ? 'time' : 'times'})
            </span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Action buttons -->
    <div class="grid grid-cols-2 gap-3 mb-4">
      <button on:click={startCooking} class="btn-primary py-3 text-lg">
        👨‍🍳 Cook
      </button>
      <button on:click={addToShoppingList} class="btn-secondary py-3">
        🛒 Add to List
      </button>
    </div>

    <div class="flex flex-wrap gap-2 mb-4">
      <a href="/recipe/{recipeId}/edit" use:link class="btn-ghost btn-sm">✏️ Edit</a>
      <button on:click={() => showRatingModal = true} class="btn-ghost btn-sm">⭐ Rate</button>
      <button on:click={cloneRecipe} class="btn-ghost btn-sm">📋 Clone</button>
      <button on:click={archiveRecipe} class="btn-ghost btn-sm text-red-500">📦 Archive</button>
    </div>
  </div>

  <!-- Rating modal -->
  {#if showRatingModal}
    <Modal on:close={() => showRatingModal = false} title="Rate this recipe">
      <Rating
        {recipeId}
        existingRatings={recipe.ratings || []}
        on:saved={() => { showRatingModal = false; loadRecipe(); }}
      />
    </Modal>
  {/if}
{/if}
