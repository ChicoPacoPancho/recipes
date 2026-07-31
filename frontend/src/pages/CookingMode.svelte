<script>
  import { onMount, onDestroy } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { recipes as recipesApi, cooking } from '../lib/api.js';
  import { currentMember, unitSystem, showToast } from '../lib/stores.js';
  import { formatTimer, formatQuantity, formatTime } from '../lib/utils.js';

  export let params = {};

  let recipe = null;
  let loading = true;
  let currentStep = 0;
  let sessionId = null;

  // Timer state
  let timerRunning = false;
  let timerSeconds = 0;
  let timerInterval = null;

  // Prevent screen sleep
  let wakeLock = null;

  $: recipeId = parseInt(params.id);
  $: totalSteps = recipe?.steps?.length || 0;
  $: step = recipe?.steps?.[currentStep] || null;
  $: stepIngredients = step?.ingredients || [];
  $: progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0;

  onMount(async () => {
    await loadRecipe();
    await startSession();
    requestWakeLock();
  });

  onDestroy(() => {
    if (timerInterval) clearInterval(timerInterval);
    releaseWakeLock();
  });

  async function loadRecipe() {
    loading = true;
    try {
      recipe = await recipesApi.get(recipeId, { units: $unitSystem });
    } catch (e) {
      showToast('Failed to load recipe', 'error');
      push('/');
    }
    loading = false;
  }

  async function startSession() {
    if (!$currentMember) return;
    try {
      const result = await cooking.start({
        recipe_id: recipeId,
        member_id: $currentMember.id,
      });
      sessionId = result.id;
    } catch (e) {
      console.error('Failed to start cooking session:', e);
    }
  }

  function toggleTimer() {
    if (timerRunning) {
      clearInterval(timerInterval);
      timerRunning = false;
    } else {
      timerInterval = setInterval(() => timerSeconds++, 1000);
      timerRunning = true;
    }
  }

  function resetTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    timerSeconds = 0;
  }

  function nextStep() {
    if (currentStep < totalSteps - 1) {
      currentStep++;
    }
  }

  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
    }
  }

  function goToStep(idx) {
    currentStep = idx;
  }

  async function finishCooking(complete = true) {
    if (timerInterval) clearInterval(timerInterval);
    timerRunning = false;

    if (sessionId) {
      try {
        await cooking.stop(sessionId, {
          duration_seconds: timerSeconds,
          is_complete: complete ? 1 : 0,
        });
      } catch (e) {
        console.error('Failed to save cooking session:', e);
      }
    }

    push(`/recipe/${recipeId}`);
  }

  async function discardSession() {
    if (timerInterval) clearInterval(timerInterval);
    if (sessionId) {
      try {
        await cooking.discard(sessionId);
      } catch (e) { /* ignore */ }
    }
    push(`/recipe/${recipeId}`);
  }

  async function requestWakeLock() {
    try {
      if ('wakeLock' in navigator) {
        wakeLock = await navigator.wakeLock.request('screen');
      }
    } catch { /* ignore */ }
  }

  function releaseWakeLock() {
    wakeLock?.release();
    wakeLock = null;
  }

  // Touch swipe handling
  let touchStartX = 0;
  function handleTouchStart(e) {
    touchStartX = e.touches[0].clientX;
  }
  function handleTouchEnd(e) {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 60) {
      if (diff > 0) nextStep();
      else prevStep();
    }
  }
</script>

{#if loading}
  <div class="cooking-mode flex items-center justify-center">
    <div class="animate-spin rounded-full h-10 w-10 border-2 border-white border-t-transparent"></div>
  </div>
{:else if recipe}
  <div class="cooking-mode flex flex-col"
       on:touchstart={handleTouchStart}
       on:touchend={handleTouchEnd}>

    <!-- Top bar -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-800">
      <button on:click={discardSession} class="text-gray-400 hover:text-white text-sm">
        ✕ Exit
      </button>
      <h1 class="text-sm font-medium text-gray-300 truncate mx-4">{recipe.title}</h1>
      <div class="text-sm font-mono text-cookbook-400">
        {formatTimer(timerSeconds)}
      </div>
    </div>

    <!-- Progress bar -->
    <div class="h-1 bg-gray-800">
      <div class="h-full bg-cookbook-500 transition-all duration-300" style="width: {progress}%"></div>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">

      {#if step}
        <!-- Step content -->
        <div class="flex-1 flex flex-col justify-center px-6 py-4 overflow-y-auto">
          <div class="text-center mb-2">
            <span class="text-cookbook-400 text-sm font-medium">
              Step {currentStep + 1} of {totalSteps}
            </span>
          </div>

          <p class="text-xl leading-relaxed text-center mb-6">
            {step.instruction}
          </p>

          {#if step.duration_minutes}
            <p class="text-center text-gray-500 text-sm mb-4">
              ⏱ About {formatTime(step.duration_minutes)}
            </p>
          {/if}

          <!-- Step ingredients -->
          {#if stepIngredients.length > 0}
            <div class="bg-gray-800 rounded-xl p-4 mx-auto max-w-sm w-full">
              <h3 class="text-xs text-gray-400 uppercase tracking-wider mb-2">Ingredients for this step</h3>
              {#each stepIngredients as ing}
                <div class="flex justify-between py-1 text-sm">
                  <span class="text-gray-300">{ing.name}</span>
                  <span class="text-cookbook-400 font-medium">
                    {ing.formatted_quantity || ''} {ing.display_unit || ''}
                  </span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Step navigation -->
        <div class="flex items-center justify-between px-6 py-4">
          <button on:click={prevStep}
                  class="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center
                         {currentStep === 0 ? 'opacity-30' : 'hover:bg-gray-700 active:bg-gray-600'}"
                  disabled={currentStep === 0}>
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Step dots -->
          <div class="flex gap-1 flex-wrap justify-center max-w-[60%]">
            {#each recipe.steps as _, idx}
              <button on:click={() => goToStep(idx)}
                      class="w-2.5 h-2.5 rounded-full transition-all
                             {idx === currentStep ? 'bg-cookbook-500 scale-125' :
                              idx < currentStep ? 'bg-cookbook-800' : 'bg-gray-700'}">
              </button>
            {/each}
          </div>

          {#if currentStep === totalSteps - 1}
            <button on:click={() => finishCooking(true)}
                    class="w-14 h-14 rounded-full bg-green-600 flex items-center justify-center
                           hover:bg-green-500 active:bg-green-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          {:else}
            <button on:click={nextStep}
                    class="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center
                           hover:bg-gray-700 active:bg-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Bottom timer controls -->
    <div class="flex items-center justify-center gap-4 px-6 py-3 bg-gray-800">
      <button on:click={toggleTimer}
              class="px-6 py-2 rounded-full text-sm font-medium transition-colors
                     {timerRunning ? 'bg-amber-600 hover:bg-amber-500' : 'bg-cookbook-600 hover:bg-cookbook-500'}">
        {timerRunning ? '⏸ Pause' : '▶ Start Timer'}
      </button>
      {#if timerSeconds > 0}
        <button on:click={resetTimer}
                class="px-4 py-2 rounded-full text-sm text-gray-400 hover:text-white">
          Reset
        </button>
      {/if}
    </div>
  </div>
{/if}
