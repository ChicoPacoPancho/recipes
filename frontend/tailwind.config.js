/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{svelte,js,ts}',
  ],
  theme: {
    extend: {
      colors: {
        cookbook: {
          50: '#fdf8f0',
          100: '#faebd7',
          200: '#f5d5ae',
          300: '#efb97b',
          400: '#e89845',
          500: '#e37f1e',
          600: '#d46614',
          700: '#b04d13',
          800: '#8d3d17',
          900: '#733316',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
