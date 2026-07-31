<script>
  import { onMount } from 'svelte';
  import { shopping } from '../lib/api.js';
  import { shoppingCount, showToast } from '../lib/stores.js';

  let items = [];
  let loading = true;
  let newItemName = '';
  let newItemQty = '';
  let newItemUnit = '';
  let showAddForm = false;

  onMount(loadList);

  async function loadList() {
    loading = true;
    try {
      items = await shopping.list();
      $shoppingCount = items.filter(i => !i.is_checked).length;
    } catch (e) {
      showToast('Failed to load shopping list', 'error');
    }
    loading = false;
  }

  async function toggleItem(id) {
    try {
      await shopping.toggle(id);
      // Optimistic update
      items = items.map(i => i.id === id ? { ...i, is_checked: !i.is_checked } : i);
      // Re-sort: unchecked first
      items = [...items.filter(i => !i.is_checked), ...items.filter(i => i.is_checked)];
      $shoppingCount = items.filter(i => !i.is_checked).length;
    } catch (e) {
      showToast('Failed to update item', 'error');
    }
  }

  async function removeItem(id) {
    try {
      await shopping.remove(id);
      items = items.filter(i => i.id !== id);
      $shoppingCount = items.filter(i => !i.is_checked).length;
    } catch (e) {
      showToast('Failed to remove item', 'error');
    }
  }

  async function addCustomItem() {
    if (!newItemName.trim()) return;
    try {
      await shopping.addItem({
        name: newItemName.trim(),
        quantity: newItemQty ? parseFloat(newItemQty) : null,
        unit: newItemUnit.trim() || null,
      });
      newItemName = '';
      newItemQty = '';
      newItemUnit = '';
      showAddForm = false;
      loadList();
      showToast('Item added!');
    } catch (e) {
      showToast('Failed to add item', 'error');
    }
  }

  async function clearChecked() {
    try {
      await shopping.clearChecked();
      items = items.filter(i => !i.is_checked);
      $shoppingCount = items.length;
      showToast('Checked items cleared');
    } catch (e) {
      showToast('Failed to clear items', 'error');
    }
  }

  async function clearAll() {
    if (!confirm('Clear the entire shopping list?')) return;
    try {
      await shopping.clearAll();
      items = [];
      $shoppingCount = 0;
      showToast('Shopping list cleared');
    } catch (e) {
      showToast('Failed to clear list', 'error');
    }
  }

  // Group items by recipe
  $: uncheckedItems = items.filter(i => !i.is_checked);
  $: checkedItems = items.filter(i => i.is_checked);

  $: groupedUnchecked = groupByRecipe(uncheckedItems);

  function groupByRecipe(itemList) {
    const groups = {};
    for (const item of itemList) {
      const key = item.recipe_title || 'Custom Items';
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return groups;
  }
</script>

<div class="page-container">
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-2xl font-bold">🛒 Shopping List</h1>
    <div class="flex gap-2">
      <button on:click={() => showAddForm = !showAddForm}
              class="btn-ghost btn-sm text-cookbook-600">
        + Add
      </button>
    </div>
  </div>

  <!-- Add custom item -->
  {#if showAddForm}
    <form on:submit|preventDefault={addCustomItem} class="card p-3 mb-4">
      <div class="flex gap-2">
        <input type="number" bind:value={newItemQty} class="input w-16" placeholder="Qty" step="any" />
        <input type="text" bind:value={newItemUnit} class="input w-16" placeholder="Unit" />
        <input type="text" bind:value={newItemName} class="input flex-1" placeholder="Item name..." required />
        <button type="submit" class="btn-primary btn-sm">Add</button>
      </div>
    </form>
  {/if}

  {#if loading}
    <div class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-cookbook-500 border-t-transparent"></div>
    </div>
  {:else if items.length === 0}
    <div class="text-center py-20">
      <p class="text-6xl mb-4">🛒</p>
      <p class="text-gray-500">Your shopping list is empty.</p>
      <p class="text-sm text-gray-400 mt-1">Add ingredients from a recipe to get started.</p>
    </div>
  {:else}
    <!-- Unchecked items grouped by recipe -->
    {#each Object.entries(groupedUnchecked) as [recipeName, recipeItems]}
      <div class="mb-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 px-1">
          {recipeName}
        </h3>
        <div class="card divide-y divide-gray-50">
          {#each recipeItems as item}
            <div class="flex items-center gap-3 px-3 py-2.5">
              <button on:click={() => toggleItem(item.id)}
                      class="w-5 h-5 rounded-full border-2 border-gray-300 flex-shrink-0
                             hover:border-cookbook-500 transition-colors">
              </button>
              <div class="flex-1 min-w-0">
                <span class="text-sm">
                  {#if item.quantity}
                    <span class="font-medium text-cookbook-700">{item.quantity} {item.unit || ''}</span>
                  {/if}
                  {item.name}
                </span>
              </div>
              <button on:click={() => removeItem(item.id)}
                      class="text-gray-300 hover:text-red-500 flex-shrink-0">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          {/each}
        </div>
      </div>
    {/each}

    <!-- Checked items -->
    {#if checkedItems.length > 0}
      <div class="mb-4">
        <div class="flex items-center justify-between mb-1 px-1">
          <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Done ({checkedItems.length})
          </h3>
          <button on:click={clearChecked} class="text-xs text-red-400 hover:text-red-600">
            Clear done
          </button>
        </div>
        <div class="card divide-y divide-gray-50 opacity-50">
          {#each checkedItems as item}
            <div class="flex items-center gap-3 px-3 py-2">
              <button on:click={() => toggleItem(item.id)}
                      class="w-5 h-5 rounded-full border-2 border-green-400 bg-green-400
                             flex-shrink-0 flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </button>
              <span class="text-sm line-through text-gray-400 flex-1">
                {#if item.quantity}
                  {item.quantity} {item.unit || ''}
                {/if}
                {item.name}
              </span>
              <span class="text-xs text-gray-300">{item.recipe_title || ''}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Actions -->
    {#if items.length > 0}
      <div class="text-center mt-6">
        <button on:click={clearAll} class="btn-ghost btn-sm text-red-400">
          Clear entire list
        </button>
      </div>
    {/if}
  {/if}
</div>
