<script>
  import { onMount } from 'svelte';
  import { push, link } from 'svelte-spa-router';
  import { recipes, tags as tagsApi, uploadImage } from '../lib/api.js';
  import { currentMember, showToast } from '../lib/stores.js';

  export let params = {};

  let isEdit = false;
  let recipeId = null;
  let loading = false;
  let saving = false;

  // Form fields
  let title = '';
  let description = '';
  let sourceUrl = '';
  let sourceSite = '';
  let imageFilename = '';
  let prepTime = '';
  let cookTime = '';
  let servings = '';
  let servingsUnit = 'servings';
  let ingredients = [{ name: '', quantity: '', unit: '', group_name: '', is_optional: false, notes: '' }];
  let steps = [{ instruction: '', duration_minutes: '', group_name: '' }];
  let tagInput = '';
  let recipeTags = [];
  let allTags = [];
  let imageFile = null;

  onMount(async () => {
    if (params.id) {
      isEdit = true;
      recipeId = parseInt(params.id);
      await loadRecipe();
    }
    loadTags();
  });

  async function loadRecipe() {
    loading = true;
    try {
      const r = await recipes.get(recipeId);
      title = r.title || '';
      description = r.description || '';
      sourceUrl = r.source_url || '';
      sourceSite = r.source_site || '';
      imageFilename = r.image_filename || '';
      prepTime = r.prep_time_minutes || '';
      cookTime = r.cook_time_minutes || '';
      servings = r.servings || '';
      servingsUnit = r.servings_unit || 'servings';
      ingredients = (r.ingredients || []).map(i => ({
        name: i.name,
        quantity: i.quantity ?? '',
        unit: i.unit || '',
        group_name: i.group_name || '',
        is_optional: !!i.is_optional,
        notes: i.notes || '',
        original_text: i.original_text || '',
      }));
      if (ingredients.length === 0) ingredients = [{ name: '', quantity: '', unit: '', group_name: '', is_optional: false, notes: '' }];
      steps = (r.steps || []).map(s => ({
        instruction: s.instruction,
        duration_minutes: s.duration_minutes ?? '',
        group_name: s.group_name || '',
        original_text: s.original_text || '',
      }));
      if (steps.length === 0) steps = [{ instruction: '', duration_minutes: '', group_name: '' }];
      recipeTags = (r.tags || []).map(t => t.name);
    } catch (e) {
      showToast('Failed to load recipe', 'error');
    }
    loading = false;
  }

  async function loadTags() {
    try {
      allTags = await tagsApi.list();
    } catch (e) {
      // ignore
    }
  }

  function addIngredient() {
    ingredients = [...ingredients, { name: '', quantity: '', unit: '', group_name: '', is_optional: false, notes: '' }];
  }

  function removeIngredient(index) {
    if (ingredients.length <= 1) return;
    ingredients = ingredients.filter((_, i) => i !== index);
  }

  function addStep() {
    steps = [...steps, { instruction: '', duration_minutes: '', group_name: '' }];
  }

  function removeStep(index) {
    if (steps.length <= 1) return;
    steps = steps.filter((_, i) => i !== index);
  }

  function addTag() {
    const tag = tagInput.trim();
    if (tag && !recipeTags.includes(tag)) {
      recipeTags = [...recipeTags, tag];
    }
    tagInput = '';
  }

  function removeTag(tag) {
    recipeTags = recipeTags.filter(t => t !== tag);
  }

  function handleTagKeydown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  }

  async function handleImageUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadImage(file);
      imageFilename = result.filename;
      showToast('Image uploaded!');
    } catch (e) {
      showToast('Failed to upload image', 'error');
    }
  }

  async function save() {
    if (!title.trim()) {
      showToast('Title is required', 'error');
      return;
    }

    saving = true;
    try {
      // Extract source site from URL
      let site = sourceSite;
      if (sourceUrl && !site) {
        try {
          site = new URL(sourceUrl).hostname.replace('www.', '');
        } catch { /* ignore */ }
      }

      const data = {
        title: title.trim(),
        description: description.trim() || null,
        source_url: sourceUrl.trim() || null,
        source_site: site || null,
        image_filename: imageFilename || null,
        prep_time_minutes: prepTime ? parseInt(prepTime) : null,
        cook_time_minutes: cookTime ? parseInt(cookTime) : null,
        servings: servings ? parseFloat(servings) : null,
        servings_unit: servingsUnit,
        created_by: $currentMember?.id || null,
        ingredients: ingredients
          .filter(i => i.name.trim())
          .map((i, idx) => ({
            name: i.name.trim(),
            quantity: i.quantity ? parseFloat(i.quantity) : null,
            unit: i.unit.trim() || null,
            group_name: i.group_name.trim() || null,
            is_optional: i.is_optional ? 1 : 0,
            notes: i.notes.trim() || null,
            original_text: i.original_text || null,
            sort_order: idx,
          })),
        steps: steps
          .filter(s => s.instruction.trim())
          .map((s, idx) => ({
            instruction: s.instruction.trim(),
            step_number: idx + 1,
            duration_minutes: s.duration_minutes ? parseInt(s.duration_minutes) : null,
            group_name: s.group_name.trim() || null,
            original_text: s.original_text || null,
          })),
        tags: recipeTags,
      };

      if (isEdit) {
        await recipes.update(recipeId, data);
        showToast('Recipe updated!');
        push(`/recipe/${recipeId}`);
      } else {
        const result = await recipes.create(data);
        showToast('Recipe created!');
        push(`/recipe/${result.id}`);
      }
    } catch (e) {
      showToast(`Failed to save: ${e.message}`, 'error');
    }
    saving = false;
  }
</script>

<div class="page-container">
  <div class="flex items-center justify-between mb-4">
    <a href={isEdit ? `/recipe/${recipeId}` : '/'} use:link
       class="text-sm text-gray-500 hover:text-gray-700">← Back</a>
    <h1 class="text-xl font-bold">{isEdit ? 'Edit Recipe' : 'New Recipe'}</h1>
    <div></div>
  </div>

  {#if loading}
    <div class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-cookbook-500 border-t-transparent"></div>
    </div>
  {:else}
    <form on:submit|preventDefault={save} class="space-y-5">
      <!-- Title -->
      <div>
        <label class="label" for="title">Title *</label>
        <input id="title" type="text" bind:value={title} class="input" required
               placeholder="e.g. Grandma's Chocolate Cake" />
      </div>

      <!-- Description -->
      <div>
        <label class="label" for="desc">Description</label>
        <textarea id="desc" bind:value={description} class="input" rows="2"
                  placeholder="Short description of the recipe..."></textarea>
      </div>

      <!-- Image -->
      <div>
        <label class="label">Image</label>
        <input type="file" accept="image/*" on:change={handleImageUpload}
               class="text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg
                      file:border-0 file:bg-cookbook-100 file:text-cookbook-700
                      file:hover:bg-cookbook-200 file:cursor-pointer" />
        {#if imageFilename}
          <p class="text-xs text-green-600 mt-1">✓ Image uploaded</p>
        {/if}
      </div>

      <!-- Source URL -->
      <div>
        <label class="label" for="url">Source URL</label>
        <input id="url" type="url" bind:value={sourceUrl} class="input"
               placeholder="https://..." />
      </div>

      <!-- Times -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label" for="prep">Prep Time (min)</label>
          <input id="prep" type="number" bind:value={prepTime} class="input" min="0" />
        </div>
        <div>
          <label class="label" for="cook">Cook Time (min)</label>
          <input id="cook" type="number" bind:value={cookTime} class="input" min="0" />
        </div>
      </div>

      <!-- Servings -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label" for="servings">Servings</label>
          <input id="servings" type="number" bind:value={servings} class="input" min="0" step="0.5" />
        </div>
        <div>
          <label class="label" for="sunit">Unit</label>
          <input id="sunit" type="text" bind:value={servingsUnit} class="input"
                 placeholder="servings" />
        </div>
      </div>

      <!-- Ingredients -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="label mb-0">Ingredients</label>
          <button type="button" on:click={addIngredient} class="btn-ghost btn-sm text-cookbook-600">+ Add</button>
        </div>
        <div class="space-y-2">
          {#each ingredients as ing, i}
            <div class="card p-3">
              <div class="grid grid-cols-12 gap-2">
                <input type="number" bind:value={ing.quantity} class="input col-span-3" placeholder="Qty" step="any" />
                <input type="text" bind:value={ing.unit} class="input col-span-3" placeholder="Unit" />
                <input type="text" bind:value={ing.name} class="input col-span-5" placeholder="Ingredient name" />
                <button type="button" on:click={() => removeIngredient(i)}
                        class="col-span-1 text-red-400 hover:text-red-600 text-lg"
                        disabled={ingredients.length <= 1}>×</button>
              </div>
              <div class="grid grid-cols-12 gap-2 mt-1">
                <input type="text" bind:value={ing.group_name} class="input col-span-5 text-xs" placeholder="Group (optional)" />
                <input type="text" bind:value={ing.notes} class="input col-span-5 text-xs" placeholder="Notes" />
                <label class="col-span-2 flex items-center gap-1 text-xs text-gray-500">
                  <input type="checkbox" bind:checked={ing.is_optional} />
                  Opt
                </label>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Steps -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="label mb-0">Steps</label>
          <button type="button" on:click={addStep} class="btn-ghost btn-sm text-cookbook-600">+ Add</button>
        </div>
        <div class="space-y-2">
          {#each steps as step, i}
            <div class="card p-3">
              <div class="flex gap-2 items-start">
                <span class="flex-shrink-0 w-7 h-7 rounded-full bg-cookbook-100 text-cookbook-700
                             flex items-center justify-center text-sm font-bold mt-1">
                  {i + 1}
                </span>
                <div class="flex-1 space-y-1">
                  <textarea bind:value={step.instruction} class="input text-sm" rows="2"
                            placeholder="Describe this step..."></textarea>
                  <div class="grid grid-cols-2 gap-2">
                    <input type="number" bind:value={step.duration_minutes} class="input text-xs"
                           placeholder="Duration (min)" min="0" />
                    <input type="text" bind:value={step.group_name} class="input text-xs"
                           placeholder="Group (optional)" />
                  </div>
                </div>
                <button type="button" on:click={() => removeStep(i)}
                        class="text-red-400 hover:text-red-600 text-lg mt-1"
                        disabled={steps.length <= 1}>×</button>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Tags -->
      <div>
        <label class="label">Tags</label>
        <div class="flex gap-2 mb-2">
          <input type="text" bind:value={tagInput} on:keydown={handleTagKeydown}
                 class="input flex-1" placeholder="Add a tag..." list="tag-suggestions" />
          <button type="button" on:click={addTag} class="btn-secondary btn-sm">Add</button>
        </div>
        <datalist id="tag-suggestions">
          {#each allTags as tag}
            <option value={tag.name} />
          {/each}
        </datalist>
        <div class="flex flex-wrap gap-1.5">
          {#each recipeTags as tag}
            <span class="badge-primary flex items-center gap-1">
              {tag}
              <button type="button" on:click={() => removeTag(tag)}
                      class="text-cookbook-600 hover:text-cookbook-800">×</button>
            </span>
          {/each}
        </div>
      </div>

      <!-- Submit -->
      <button type="submit" class="btn-primary w-full py-3 text-lg" disabled={saving}>
        {saving ? 'Saving...' : (isEdit ? 'Update Recipe' : 'Create Recipe')}
      </button>
    </form>
  {/if}
</div>
