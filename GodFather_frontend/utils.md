Brand UI Utilities

This file defines reusable design tokens and utility styles for consistent UI development.

 Color Palette
Role	Hex	Meaning	Usage
Primary	#3959E5	Certainty	Main buttons, links, highlights
Secondary	#000122	Authority	Backgrounds, dark sections
Accent	#C0F9FF	Clarity	Subtle highlights, glow effects
Neutral / Base	#FFFFFF	Respect	Text on dark backgrounds, base layouts

 Gradient System
Primary Brand Gradient
--gradient-primary: linear-gradient(
  34.78deg,
  #3959E5 15.08%,
  #507FEC 47.16%,
  #8EE5FF 83.33%
);
Usage

CTA buttons

Active states

Premium feature highlights

Important tags


 Utility Classes
🎯 Gradient Button
.btn-gradient {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4px 20px;
  gap: 10px;

  height: 38px;
  border-radius: 30px;

  background: var(--gradient-primary);
  color: #FFFFFF;

  font-family: 'Haas Grot Text R Trial', sans-serif;
  font-size: 16px;
  font-weight: 400;
  line-height: 30px;

  border: none;
  cursor: pointer;
}
🌙 Dark Background Utility
.bg-dark {
  background-color: #000122;
}
🔵 Primary Text
.text-primary {
  color: #3959E5;
}
⚪ White Text
.text-white {
  color: #FFFFFF;
}

 CSS Variables (Recommended Setup)

Add this to your global CSS:

:root {
  --color-primary: #3959E5;
  --color-secondary: #000122;
  --color-accent: #C0F9FF;
  --color-white: #FFFFFF;

  --gradient-primary: linear-gradient(
    34.78deg,
    #3959E5 15.08%,
    #507FEC 47.16%,
    #8EE5FF 83.33%
  );
}


 Design Philosophy

Primary Blue (#3959E5) → Trust & intelligence

Deep Navy (#000122) → Authority & depth

Cyan Accent (#C0F9FF) → Innovation & clarity

White (#FFFFFF) → Openness & simplicity


🔤 Typography System
1️⃣ Primary Brand Font

Font Name: NeueHaasGrotTextRound
Usage: Headings, important UI text, brand-driven components

Font Declaration
@font-face {
  font-family: 'NeueHaasGrotTextRound';
  src: url('./assets/fonts/NeueHaasGrotTextRound-76BoldItalic-Trial.otf')
       format('opentype');
  font-weight: 700;
  font-style: italic;
}
2️⃣ Global Font Stack

Applied to entire application:

html, body {
  font-family: 'NeueHaasGrotTextRound',
               'Inter',
               -apple-system,
               BlinkMacSystemFont,
               "Segoe UI",
               Roboto,
               sans-serif;
}
3️⃣ Typography Hierarchy

| Usage           | Font                  | Weight  | Style  |
| --------------- | --------------------- | ------- | ------ |
| Hero / Headings | NeueHaasGrotTextRound | 700     | Italic |
| Body Text       | Inter / System        | 400–500 | Normal |
| Buttons         | NeueHaasGrotTextRound | 500–700 | Normal |
