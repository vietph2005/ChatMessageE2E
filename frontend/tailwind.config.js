/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        messenger: {
          blue: '#0084FF',
          darkBlue: '#006BCE',
          lightBlue: '#E7F3FF',
          gradientStart: '#0084FF',
          gradientEnd: '#00C6FF',
        },
      },
      animation: {
        'bounce-subtle': 'bounce-subtle 1.4s infinite ease-in-out',
        'pulse-subtle': 'pulse-subtle 2s infinite ease-in-out',
      },
      keyframes: {
        'bounce-subtle': {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1.0)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
};
