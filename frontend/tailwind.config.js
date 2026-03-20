/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0d10',
        sidebar: '#13151a',
        panel: '#181b21',
        borderContent: '#262a30',
        military: {
          green: '#2d5016',
          khaki: '#c4b5a0',
          olive: '#4b5d3a',
          red: '#8f3d3d',
          darkRed: '#3d1c1c',
          orange: '#a35022',
          yellow: '#9c7322',
          blue: '#1f3b5c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
