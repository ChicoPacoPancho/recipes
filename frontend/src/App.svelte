<script>
  import Router from 'svelte-spa-router';
  import Navigation from './components/Navigation.svelte';
  import Toast from './components/Toast.svelte';
  import Home from './pages/Home.svelte';
  import RecipeDetail from './pages/RecipeDetail.svelte';
  import RecipeForm from './pages/RecipeForm.svelte';
  import CookingMode from './pages/CookingMode.svelte';
  import ShoppingList from './pages/ShoppingList.svelte';
  import Settings from './pages/Settings.svelte';
  import ImportRecipe from './pages/ImportRecipe.svelte';
  import { shopping } from './lib/api.js';
  import { shoppingCount, currentMember } from './lib/stores.js';

  const routes = {
    '/': Home,
    '/recipe/new': RecipeForm,
    '/recipe/:id': RecipeDetail,
    '/recipe/:id/edit': RecipeForm,
    '/recipe/:id/cook': CookingMode,
    '/shopping': ShoppingList,
    '/settings': Settings,
    '/import': ImportRecipe,
  };

  // Load shopping count on mount
  async function loadShoppingCount() {
    try {
      const items = await shopping.list();
      $shoppingCount = items.filter(i => !i.is_checked).length;
    } catch {
      // ignore
    }
  }

  loadShoppingCount();

  // Check if we're in cooking mode (hide nav)
  let isCookingMode = false;
  function handleRouteEvent(event) {
    isCookingMode = event.detail?.location?.includes('/cook') || false;
  }
</script>

<div class="min-h-screen bg-gray-50">
  <Router {routes} on:routeLoaded={handleRouteEvent} />
  {#if !isCookingMode}
    <Navigation />
  {/if}
  <Toast />
</div>
