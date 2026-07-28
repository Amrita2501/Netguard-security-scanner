/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#d9e6ff',
          200: '#bcd2ff',
          300: '#8fb4ff',
          400: '#5c8dff',
          500: '#3366ff',
          600: '#1f47e6',
          700: '#1936b4',
          800: '#182f8f',
          900: '#182b70',
        },
        surface: {
          light: '#f8fafc',
          dark: '#0b1120',
        },
        panel: {
          light: '#ffffff',
          dark: '#111827',
        },
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.08)',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: 0, transform: 'translateY(4px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        pulseSlow: { '0%,100%': { opacity: 1 }, '50%': { opacity: 0.6 } },
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-out',
        pulseSlow: 'pulseSlow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
