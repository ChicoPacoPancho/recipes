<script>
  import { onMount } from 'svelte';
  import { members as membersApi, settings as settingsApi, tags as tagsApi } from '../lib/api.js';
  import { currentMember, unitSystem, showToast } from '../lib/stores.js';

  let memberList = [];
  let appSettings = {};
  let allTags = [];
  let loading = true;

  // New member form
  let newMemberName = '';
  let newMemberAvatar = '👤';
  let showMemberForm = false;

  // Available avatars
  const avatars = ['👤', '👩', '👨', '👧', '👦', '🧑', '👶', '🧓', '👴', '👵',
                   '🦸', '🧑‍🍳', '🧙', '🦹', '🤴', '👸', '🧑‍🎨', '🧑‍🚀'];

  onMount(loadData);

  async function loadData() {
    loading = true;
    try {
      [memberList, appSettings, allTags] = await Promise.all([
        membersApi.list(),
        settingsApi.get(),
        tagsApi.list(),
      ]);
    } catch (e) {
      showToast('Failed to load settings', 'error');
    }
    loading = false;
  }

  async function addMember() {
    if (!newMemberName.trim()) return;
    try {
      await membersApi.create({ name: newMemberName.trim(), avatar: newMemberAvatar });
      newMemberName = '';
      newMemberAvatar = '👤';
      showMemberForm = false;
      await loadData();
      showToast('Member added!');
    } catch (e) {
      showToast(e.message, 'error');
    }
  }

  async function removeMember(id) {
    if (!confirm('Remove this member?')) return;
    try {
      await membersApi.delete(id);
      if ($currentMember?.id === id) {
        $currentMember = null;
      }
      await loadData();
      showToast('Member removed');
    } catch (e) {
      showToast('Failed to remove member', 'error');
    }
  }

  function selectMember(member) {
    $currentMember = member;
    showToast(`Switched to ${member.name}`);
  }

  async function saveSetting(key, value) {
    try {
      await settingsApi.update({ [key]: value });
      appSettings[key] = value;
    } catch (e) {
      showToast('Failed to save setting', 'error');
    }
  }

  function toggleUnitSystem() {
    const newSystem = $unitSystem === 'metric' ? 'imperial' : 'metric';
    $unitSystem = newSystem;
    saveSetting('unit_system', newSystem);
  }

  async function deleteTag(tagId) {
    try {
      await tagsApi.delete(tagId);
      allTags = allTags.filter(t => t.id !== tagId);
      showToast('Tag deleted');
    } catch (e) {
      showToast('Failed to delete tag', 'error');
    }
  }
</script>

<div class="page-container">
  <h1 class="text-2xl font-bold mb-6">⚙️ Settings</h1>

  {#if loading}
    <div class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-cookbook-500 border-t-transparent"></div>
    </div>
  {:else}

    <!-- Current Member -->
    <section class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Who's cooking?</h2>
      {#if $currentMember}
        <div class="flex items-center gap-2 mb-3 p-2 bg-cookbook-50 rounded-lg">
          <span class="text-2xl">{$currentMember.avatar}</span>
          <span class="font-medium">{$currentMember.name}</span>
          <span class="badge-primary ml-auto">Active</span>
        </div>
      {:else}
        <p class="text-sm text-gray-500 mb-3">Select a member below to get started.</p>
      {/if}

      <div class="space-y-2">
        {#each memberList as member}
          <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50
                      {$currentMember?.id === member.id ? 'bg-cookbook-50 border border-cookbook-200' : ''}">
            <span class="text-xl">{member.avatar}</span>
            <span class="font-medium flex-1">{member.name}</span>
            {#if $currentMember?.id !== member.id}
              <button on:click={() => selectMember(member)} class="btn-ghost btn-sm">
                Switch
              </button>
            {/if}
            <button on:click={() => removeMember(member.id)}
                    class="text-gray-300 hover:text-red-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {/each}
      </div>

      <button on:click={() => showMemberForm = !showMemberForm}
              class="btn-ghost btn-sm text-cookbook-600 mt-3 w-full">
        + Add Member
      </button>

      {#if showMemberForm}
        <form on:submit|preventDefault={addMember} class="mt-3 space-y-2">
          <div>
            <label class="label">Name</label>
            <input type="text" bind:value={newMemberName} class="input" placeholder="Name" required />
          </div>
          <div>
            <label class="label">Avatar</label>
            <div class="flex flex-wrap gap-1">
              {#each avatars as av}
                <button type="button" on:click={() => newMemberAvatar = av}
                        class="text-2xl p-1 rounded-lg {newMemberAvatar === av ? 'bg-cookbook-100 ring-2 ring-cookbook-500' : 'hover:bg-gray-100'}">
                  {av}
                </button>
              {/each}
            </div>
          </div>
          <button type="submit" class="btn-primary btn-sm w-full">Add Member</button>
        </form>
      {/if}
    </section>

    <!-- Preferences -->
    <section class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Preferences</h2>

      <div class="flex items-center justify-between py-2">
        <div>
          <span class="font-medium text-sm">Unit System</span>
          <p class="text-xs text-gray-500">Default measurement display</p>
        </div>
        <button on:click={toggleUnitSystem} class="btn-secondary btn-sm">
          {$unitSystem === 'metric' ? '🌍 Metric' : '🇺🇸 Imperial'}
        </button>
      </div>

      <div class="flex items-center justify-between py-2 border-t border-gray-50">
        <div>
          <span class="font-medium text-sm">"Quick" Recipe Threshold</span>
          <p class="text-xs text-gray-500">Recipes under this time get the Quick tag</p>
        </div>
        <div class="flex items-center gap-1">
          <input type="number" value={appSettings.quick_recipe_threshold || 30}
                 on:change={(e) => saveSetting('quick_recipe_threshold', e.target.value)}
                 class="input w-20 text-center" min="5" step="5" />
          <span class="text-xs text-gray-500">min</span>
        </div>
      </div>
    </section>

    <!-- AI Configuration -->
    <section class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">AI Recipe Import</h2>

      <div class="space-y-3">
        <div>
          <label class="label">Provider</label>
          <select class="input" value={appSettings.ai_provider || 'ollama'}
                  on:change={(e) => saveSetting('ai_provider', e.target.value)}>
            <option value="ollama">Ollama (Local)</option>
            <option value="openai">OpenAI Compatible</option>
          </select>
        </div>

        <div>
          <label class="label">API Base URL</label>
          <input type="url" class="input" value={appSettings.ai_base_url || 'http://localhost:11434'}
                 on:change={(e) => saveSetting('ai_base_url', e.target.value)}
                 placeholder="http://localhost:11434" />
        </div>

        <div>
          <label class="label">Model</label>
          <input type="text" class="input" value={appSettings.ai_model || 'llama3.2'}
                 on:change={(e) => saveSetting('ai_model', e.target.value)}
                 placeholder="llama3.2" />
        </div>

        <div>
          <label class="label">API Key (if needed)</label>
          <input type="password" class="input" value={appSettings.ai_api_key || ''}
                 on:change={(e) => saveSetting('ai_api_key', e.target.value)}
                 placeholder="Leave blank for Ollama" />
        </div>
      </div>
    </section>

    <!-- Tags Management -->
    <section class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Tags</h2>
      {#if allTags.length > 0}
        <div class="flex flex-wrap gap-1.5">
          {#each allTags as tag}
            <span class="badge-primary flex items-center gap-1">
              {tag.name}
              <span class="text-xs text-gray-400 ml-0.5">{tag.recipe_count}</span>
              {#if tag.recipe_count === 0}
                <button on:click={() => deleteTag(tag.id)}
                        class="text-cookbook-600 hover:text-red-500 ml-0.5">×</button>
              {/if}
            </span>
          {/each}
        </div>
      {:else}
        <p class="text-sm text-gray-400">No tags yet. Tags are created when you add them to recipes.</p>
      {/if}
    </section>

    <!-- Household Name -->
    <section class="card p-4 mb-4">
      <h2 class="font-bold text-lg mb-3">Household</h2>
      <div>
        <label class="label">Cookbook Name</label>
        <input type="text" class="input" value={appSettings.household_name || 'Our Family'}
               on:change={(e) => saveSetting('household_name', e.target.value)}
               placeholder="Our Family" />
      </div>
    </section>

    <!-- App info -->
    <div class="text-center text-xs text-gray-400 mt-8 mb-4">
      <p>Family Cookbook v1.0.0</p>
      <p>Your recipes, your way 🍳</p>
    </div>
  {/if}
</div>
