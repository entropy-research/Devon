import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'
// https://github.com/tailwindlabs/tailwindcss-container-queries
import containerQueries from '@tailwindcss/container-queries'

const config: Config = {
  darkMode: 'class',
  content: [
    './frontend/app/**/*.{js,ts,jsx,tsx,mdx}',
    './frontend/components/**/*.{js,ts,jsx,tsx,mdx}',
    './frontend/components/ui/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        day: '#f2f2f2', // 'white' bg
        night: '#242424', // 'black' bg
        shade: '#2e2e2e',
        outline: {
          day: '#f2f2f2',
          night: '#484848',
        },
        orange: '#c97f59',
        aqua: '#55c2f9',
        // input: {
        //   dark: '#484848',
        // },
        primary: '#6096FF', // blue
        'custom-blue': 'rgba(0,187,255,0.5)',
        input: 'var(--input)',
        // primary: {
        //   DEFAULT: "var(--primary)",
        //   foreground: "var(--primary-foreground)",
        // },
        border: 'var(--border)',
        ring: 'var(--ring)',
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        popover: {
          DEFAULT: 'var(--popover)',
          foreground: 'var(--popover-foreground)',
        },
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [animate, containerQueries],
}
export default config
