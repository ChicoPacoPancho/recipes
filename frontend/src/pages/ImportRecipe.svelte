<script>
  import { push, link } from 'svelte-spa-router';
  import { importRecipe, recipes as recipesApi } from '../lib/api.js';
  import { currentMember, showToast } from '../lib/stores.js';

  let url = '';
  let rawText = '';
  let mode = 'url'; // 'url' or 'text'
  let loading = false;
  let preview = null;
  let error = '';

  async function handleImport() {
    error = '';
    preview = null;
    loading = true;

    try {
      if (mode === 'url') {
        if (!url.trim()) {
          error = 'Please enter a URL';
          loading = false;
          return;
        }
        preview = await importRecipe.fromUrl(url.trim());
      } else {
        if (!rawText.trim()) {
          error = 'Please enter recipe text';
          loading = false;
          return;
        }
        preview = await importRecipe.fromText(rawText.trim());
      }
    } catch (e) {
      error = e.message;
    }
    loading = false;
  }

  async function saveImported() {
    if (!preview) return;
    loading = true;

    try {
      // Download image if available
      let imageFilename = null;
      if (preview.image_url) {
        try {
          const imgResult = await importRecipe.downloadImage(preview.image_url);
          imageFilename = imgResult.filename;
        } catch (e) {
          console.warn('Failed to download image:', e);
        }
      }

      const recipeData = {
        title: preview.title,
        description: preview.description,
        source_url: preview.source_url || url || null,
        source_site: preview.source_site || null,
        image_filename: imageFilename,
        prep_time_minutes: preview.prep_time_minutes,
        cook_time_minutes: preview.cook_time_minutes,
        servings: preview.servings,
        servings_unit: preview.servings_unit || 'servings',
        created_by: $currentMember?.id,
        original_data: preview.original_data,
        ingredients: (preview.ingredients || []).map((ing, i) => ({
          name: ing.name,
          quantity: ing.quantity,
          unit: ing.unit,
          group_name: ing.group_name,
          is_optional: ing.is_optional ? 1 : 0,
          notes: ing.notes,
          original_text: ing.original_text,
          sort_order: i,
        })),
        steps: (preview.steps || []).map((step, i) => ({
          instruction: step.instruction,
          step_number: step.step_number || i + 1,
          duration_minutes: step.duration_minutes,
          group_name: step.group_name,
          original_text: step.original_text,
          ingredient_names: step.ingredient_names || [],
        })),
        tags: preview.tags || [],
      };

      const result = await recipesApi.create(recipeData);
      showToast('Recipe imported!');
      push(`/recipe/${result.id}`);
    } catch (e) {
      error = e.message;
      showToast('Failed to save recipe', 'error');
    }
    loading = false;
  }

  function editBeforeSaving() {
    // Redirect to recipe form with imported data in sessionStorage
    sessionStorage.setItem('importedRecipe', JSON.stringify(preview));
    push('/recipe/new');
  }
</script>

<div class="page-container">
  <h1 class="text-2xl font-bold mb-4">📥 Import Recipe</h1>

  <!-- Mode toggle -->
  <div class="flex gap-2 mb-4">
    <button on:click={() => { mode = 'url'; preview = null; error = ''; }}
            class="btn-sm flex-1 {mode === 'url' ? 'btn-primary' : 'btn-secondary'}">
      From URL
    </button>
    <button on:click={() => { mode = 'text'; preview = null; error = ''; }}
            class="btn-sm flex-1 {mode === 'text' ? 'btn-primary' : 'btn-secondary'}">
      From Text
    </button>
  </div>

  <!-- Input -->
  {#if !preview}
    {#if mode === 'url'}
      <div class="mb-4">
        <label class="label">Recipe URL</label>
        <input type="url" bind:value={url} class="input" placeholder="https://www.example.com/recipe..."
               on:keydown={(e) => e.key === 'Enter' && handleImport()} />
        <p class="text-xs text-gray-400 mt-1">
          Paste a link to a recipe page and our AI will extract the details.
        </p>
      </div>
    {:else}
      <div class="mb-4">
        <label class="label">Recipe Text</label>
        <textarea bind:value={rawText} class="input" rows="10"
                  placeholder="Paste the recipe text here..."></textarea>
        <p class="text-xs text-gray-400 mt-1">
          Paste recipe text from any source and our AI will structure it.
        </p>
      </div>
    {/if}

    {#if error}
      <div class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-700">
        {error}
      </div>
    {/if}

    <button on:click={handleImport} class="btn-primary w-full py-3" disabled={loading}>
      {#if loading}
        <div class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
        Extracting recipe...
      {:else}
        🤖 Extract Recipe
      {/if}
    </button>

    <p class="text-xs text-gray-400 text-center mt-3">
      Requires an AI service to be configured in <a href="/settings" use:link class="text-cookbook-600 hover:underline">Settings</a>.
    </p>
  {:else}
    <!-- Preview -->
    <div class="space-y-4">
      <div class="card p-4">
        <h2 class="font-bold text-xl mb-1">{preview.title || 'Untitled Recipe'}</h2>
        {#if preview.description}
          <p class="text-sm text-gray-600 mb-2">{preview.description}</p>
        {/if}

        <div class="flex gap-3 text-sm text-gray-500 mb-2">
          {#if preview.prep_time_minutes}
            <span>🔪 Prep: {preview.prep_time_minutes} min</span>
          {/if}
          {#if preview.cook_time_minutes}
            <span>🔥 Cook: {preview.cook_time_minutes} min</span>
          {/if}
          {#if preview.servings}
            <span>🍽 {preview.servings} {preview.servings_unit || 'servings'}</span>
          {/if}
        </div>

        {#if preview.tags?.length > 0}
          <div class="flex flex-wrap gap-1 mb-2">
            {#each preview.tags as tag}
              <span class="badge-primary">{tag}</span>
            {/each}
          </div>
        {/if}
      </div>

      {#if preview.ingredients?.length > 0}
        <div class="card p-4">
          <h3 class="font-bold mb-2">Ingredients ({preview.ingredients.length})</h3>
          {#each preview.ingredients as ing}
            <div class="text-sm py-1 border-b border-gray-50 last:border-0">
              <span class="font-medium text-cookbook-700">
                {ing.quantity || ''} {ing.unit || ''}
              </span>
              {ing.name}
              {#if ing.notes}
                <span class="text-gray-400"> — {ing.notes}</span>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

      {#if preview.steps?.length > 0}
        <div class="card p-4">
          <h3 class="font-bold mb-2">Steps ({preview.steps.length})</h3>
          {#each preview.steps as step, i}
            <div class="flex gap-2 py-2 border-b border-gray-50 last:border-0">
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-cookbook-100 text-cookbook-700
                           flex items-center justify-center text-xs font-bold">
                {step.step_number || i + 1}
              </span>
              <p class="text-sm">{step.instruction}</p>
            </div>
          {/each}
        </div>
      {/if}

      {#if error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-3">
        <button on:click={saveImported} class="btn-primary py-3" disabled={loading}>
          {loading ? 'Saving...' : '✓ Save Recipe'}
        </button>
        <button on:click={() => { preview = null; error = ''; }} class="btn-secondary py-3">
          ← Try Again
        </button>
      </div>
    </div>
  {/if}
</div>
