/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        neutral: {
          800: '#212121',
          900: '#171717',
          200: '#ECECEC',
          400: '#B4B4B4',
          700: '#383838',
        },
      },
      fontFamily: {
        sans: ['Inter', 'San Francisco', 'Helvetica Neue', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
