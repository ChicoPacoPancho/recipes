<script>
  import { link } from 'svelte-spa-router';
  import { imageUrl } from '../lib/api.js';
  import { formatTime } from '../lib/utils.js';

  export let recipe;

  $: totalTime = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);
  $: allTags = [
    ...(recipe.computed_tags || []).map(t => ({ name: t, computed: true })),
    ...(recipe.tag_list ? recipe.tag_list.split(', ').filter(Boolean).map(t => ({ name: t, computed: false })) : []),
  ];
</script>

<a href="/recipe/{recipe.id}" use:link class="card hover:shadow-md transition-shadow block">
  <div class="aspect-[4/3] bg-gray-100 relative overflow-hidden">
    {#if recipe.image_filename}
      <img src={imageUrl(recipe.image_filename)} alt={recipe.title}
           class="w-full h-full object-cover" loading="lazy" />
    {:else}
      <div class="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-cookbook-50 to-cookbook-100">
        🍽️
      </div>
    {/if}
    {#if recipe.avg_rating}
      <div class="absolute top-1.5 right-1.5 bg-white/90 backdrop-blur-sm rounded-full px-1.5 py-0.5 text-xs font-medium flex items-center gap-0.5">
        ⭐ {recipe.avg_rating}
      </div>
    {/if}
  </div>
  <div class="p-2.5">
    <h3 class="font-semibold text-sm leading-tight line-clamp-2 mb-1">{recipe.title}</h3>
    <div class="flex items-center gap-2 text-xs text-gray-500">
      {#if totalTime > 0}
        <span>⏱ {formatTime(totalTime)}</span>
      {/if}
      {#if recipe.source_site}
        <span class="truncate">📎 {recipe.source_site}</span>
      {/if}
    </div>
    {#if allTags.length > 0}
      <div class="flex flex-wrap gap-1 mt-1.5">
        {#each allTags.slice(0, 3) as tag}
          <span class="{tag.computed ? 'badge-computed' : 'badge-primary'} text-[10px] px-1.5 py-0">
            {tag.name}
          </span>
        {/each}
        {#if allTags.length > 3}
          <span class="text-[10px] text-gray-400">+{allTags.length - 3}</span>
        {/if}
      </div>
    {/if}
  </div>
</a>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
