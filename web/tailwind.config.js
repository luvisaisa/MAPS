/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6f7f9',
          100: '#b3e5ed',
          200: '#80d3e1',
          300: '#4dc1d5',
          400: '#1aafc9',
          500: '#0a9dbd',  // Main primary color
          600: '#087d97',
          700: '#065d71',
          800: '#043e4b',
          900: '#021e25',
        },
        secondary: {
          50: '#f7f7f8',
          100: '#e3e4e6',
          200: '#c7c9cd',
          300: '#abafb4',
          400: '#8f949b',
          500: '#6b7280',  // Main secondary color
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
      },
    },
  },
  plugins: [],
}
