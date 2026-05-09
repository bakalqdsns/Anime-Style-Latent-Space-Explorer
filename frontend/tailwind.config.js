/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d9ff',
          300: '#a3c2ff',
          400: '#78a2ff',
          500: '#5680f9',
          600: '#3b63e1',
          700: '#2d4fc7',
          800: '#2641a0',
          900: '#243a87',
        },
        dark: {
          100: '#2a2a3e',
          200: '#1e1e2f',
          300: '#16162a',
          400: '#0f0f1a',
          500: '#0a0a12',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(86,128,249,0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(86,128,249,0.6)' },
        },
      },
    },
  },
  plugins: [],
}
