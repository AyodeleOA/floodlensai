/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        floodlens: {
          50: '#eef6ff',
          100: '#d9ebff',
          200: '#bcdcff',
          300: '#8ec5ff',
          400: '#59a6ff',
          500: '#3380ff',
          600: '#1f60f5',
          700: '#1a4ce0',
          800: '#1c3fb5',
          900: '#1d3a8f',
          950: '#142556',
        },
        risk: {
          low: '#22c55e',
          guarded: '#eab308',
          elevated: '#f97316',
          high: '#ef4444',
          'very-high': '#991b1b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
