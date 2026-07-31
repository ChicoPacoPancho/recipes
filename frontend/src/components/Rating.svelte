<script>
  import { createEventDispatcher } from 'svelte';
  import { ratings as ratingsApi, members as membersApi } from '../lib/api.js';
  import { currentMember, showToast } from '../lib/stores.js';
  import { STICKERS } from '../lib/stickers.js';

  export let recipeId;
  export let existingRatings = [];

  const dispatch = createEventDispatcher();

  let memberList = [];
  let selectedMemberId = $currentMember?.id || null;
  let score = 0;
  let selectedSticker = '';
  let comment = '';
  let loading = false;

  // Load members
  (async () => {
    try {
      memberList = await membersApi.list();
    } catch (e) {
      console.error('Failed to load members:', e);
    }
  })();

  // Pre-fill if member has existing rating
  $: {
    const existing = existingRatings.find(r => r.member_id === selectedMemberId);
    if (existing) {
      score = existing.score || 0;
      selectedSticker = existing.sticker || '';
      comment = existing.comment || '';
    } else {
      score = 0;
      selectedSticker = '';
      comment = '';
    }
  }

  async function submitRating() {
    if (!selectedMemberId) {
      showToast('Select a member first', 'error');
      return;
    }
    loading = true;
    try {
      await ratingsApi.upsert(recipeId, {
        member_id: selectedMemberId,
        score: score || null,
        sticker: selectedSticker || null,
        comment: comment || null,
        rated_by: $currentMember?.id,
      });
      showToast('Rating saved!');
      dispatch('saved');
    } catch (e) {
      showToast('Failed to save rating', 'error');
    }
    loading = false;
  }

  function setScore(n) {
    score = score === n ? 0 : n;
  }
</script>

<div class="space-y-4">
  <!-- Member selector -->
  <div>
    <label class="label">Who's rating?</label>
    <select bind:value={selectedMemberId} class="input">
      <option value={null}>Select member...</option>
      {#each memberList as member}
        <option value={member.id}>{member.avatar} {member.name}</option>
      {/each}
    </select>
  </div>

  <!-- Star rating -->
  <div>
    <label class="label">Stars</label>
    <div class="flex gap-1">
      {#each [1, 2, 3, 4, 5] as n}
        <button on:click={() => setScore(n)}
                class="text-3xl transition-transform hover:scale-110 active:scale-95">
          {n <= score ? '⭐' : '☆'}
        </button>
      {/each}
    </div>
  </div>

  <!-- Sticker picker -->
  <div>
    <label class="label">Pick a sticker!</label>
    <div class="grid grid-cols-8 gap-1">
      {#each STICKERS as sticker}
        <button
          on:click={() => selectedSticker = selectedSticker === sticker.emoji ? '' : sticker.emoji}
          class="text-2xl p-1.5 rounded-lg transition-all
                 {selectedSticker === sticker.emoji ? 'bg-cookbook-100 scale-110 sticker-animate' : 'hover:bg-gray-100'}"
          title={sticker.label}>
          {sticker.emoji}
        </button>
      {/each}
    </div>
    {#if selectedSticker}
      <p class="text-sm text-gray-500 mt-1">
        Selected: {selectedSticker} {STICKERS.find(s => s.emoji === selectedSticker)?.label || ''}
      </p>
    {/if}
  </div>

  <!-- Comment -->
  <div>
    <label class="label">Comment (optional)</label>
    <input type="text" bind:value={comment} class="input"
           placeholder="Quick thought about this recipe..." maxlength="200" />
  </div>

  <button on:click={submitRating} class="btn-primary w-full" disabled={loading || !selectedMemberId}>
    {loading ? 'Saving...' : 'Save Rating'}
  </button>
</div>
