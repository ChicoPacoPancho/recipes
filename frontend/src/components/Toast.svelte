<script>
  import { toast } from '../lib/stores.js';
</script>

{#if $toast}
  <div class="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-slide-down">
    <div class="px-4 py-2 rounded-lg shadow-lg text-sm font-medium
                {$toast.type === 'error' ? 'bg-red-500 text-white' :
                 $toast.type === 'warning' ? 'bg-amber-500 text-white' :
                 'bg-green-500 text-white'}">
      {$toast.message}
    </div>
  </div>
{/if}

<style>
  @keyframes slide-down {
    from { opacity: 0; transform: translate(-50%, -1rem); }
    to { opacity: 1; transform: translate(-50%, 0); }
  }
  .animate-slide-down {
    animation: slide-down 0.2s ease-out;
  }
</style>
