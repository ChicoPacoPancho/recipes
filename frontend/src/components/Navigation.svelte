<script>
  import { link } from 'svelte-spa-router';
  import { shoppingCount } from '../lib/stores.js';

  // Determine active route
  let currentPath = window.location.hash.slice(1) || '/';
  function updatePath() {
    currentPath = window.location.hash.slice(1) || '/';
  }
  window.addEventListener('hashchange', updatePath);
</script>

<nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40 safe-area-bottom">
  <div class="max-w-2xl mx-auto flex justify-around items-center h-16">
    <a href="/" use:link
       class="flex flex-col items-center gap-0.5 px-3 py-1 transition-colors {currentPath === '/' ? 'text-cookbook-600' : 'text-gray-400 hover:text-gray-600'}">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
      <span class="text-xs">Recipes</span>
    </a>

    <a href="/import" use:link
       class="flex flex-col items-center gap-0.5 px-3 py-1 transition-colors {currentPath === '/import' ? 'text-cookbook-600' : 'text-gray-400 hover:text-gray-600'}">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <span class="text-xs">Import</span>
    </a>

    <a href="/recipe/new" use:link
       class="flex items-center justify-center w-14 h-14 -mt-6 bg-cookbook-500 text-white rounded-full shadow-lg hover:bg-cookbook-600 active:bg-cookbook-700 transition-colors">
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
    </a>

    <a href="/shopping" use:link
       class="flex flex-col items-center gap-0.5 px-3 py-1 transition-colors relative {currentPath === '/shopping' ? 'text-cookbook-600' : 'text-gray-400 hover:text-gray-600'}">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
      </svg>
      <span class="text-xs">Shopping</span>
      {#if $shoppingCount > 0}
        <span class="absolute -top-1 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {$shoppingCount > 99 ? '99+' : $shoppingCount}
        </span>
      {/if}
    </a>

    <a href="/settings" use:link
       class="flex flex-col items-center gap-0.5 px-3 py-1 transition-colors {currentPath === '/settings' ? 'text-cookbook-600' : 'text-gray-400 hover:text-gray-600'}">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <span class="text-xs">Settings</span>
    </a>
  </div>
</nav>

<style>
  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
</style>
