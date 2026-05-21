// // tailwind.config.js (Vite + ESM)
// export default {
//   content: [
//     "./index.html",
//     "./src/**/*.{js,jsx,ts,tsx}"
//   ],
//   darkMode: "media", // uses prefers-color-scheme
//   theme: {
//     extend: {
//       colors: {
//         // map your CSS values to token names
//         'page-bg': '#242424',           // background-color from :root
//         'text-default': 'rgba(255,255,255,0.87)', // color from :root
//         'link': '#646cff',
//         'link-hover': '#535bf2',
//         // signup tokens you used earlier (example)
//         'signup-bg': '#0b1220',
//         'signup-border': 'rgba(255,255,255,0.08)',
//         'signup-input-border': 'rgba(255,255,255,0.12)',
//         'signup-primary': '#0b1726',
//         'signup-text-muted': 'rgba(255,255,255,0.6)',
//       },
//       fontFamily: {
//         // system stack you used
//         sans: ['system-ui', 'Avenir', 'Helvetica', 'Arial', 'sans-serif'],
//       },
//       borderRadius: {
//         // override if you used a different default
//         DEFAULT: '8px',
//         '2xl': '1rem'
//       },
//       lineHeight: {
//         relaxed: '1.5' // maps to line-height: 1.5 if you want utility
//       }
//     }
//   },
//   plugins: []
// }

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,jsx}"], // fixed path for your Vite project
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
        brand: {
          navy: "#000122",
          sidebar: "#1C1D31",
          blue: "#3959E5",
          cyan: "#8EE5FF",
          lightCyan: "#C0F9FF",
          border: "#5B6798",
          gray: "#8E8E98",
          darkGray: "#4C4D64",
          scrollbar: "#333340",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
