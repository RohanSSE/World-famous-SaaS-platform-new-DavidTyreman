import { createTheme as createMuiTheme } from "@mui/material/styles";
import { shadows } from "./core/shadows";
import { palette } from "./core/palette";
import { themeConfig } from "./theme-config";
import { components } from "./core/components";
import { typography } from "./core/typography";
import { customShadows } from "./core/custom-shadows";

const baseTheme = {
  defaultColorScheme: "dark",
  colorSchemes: {
    dark: {
      palette: palette.dark,
      shadows: shadows.dark,
      customShadows: customShadows.dark,
    },
    light: {
      palette: palette.dark,
      shadows: shadows.dark,
      customShadows: customShadows.dark,
    },
  },
  components,
  typography,
  shape: { borderRadius: 10 },
  cssVariables: themeConfig.cssVariables,
};

function createTheme({ themeOverrides = {} } = {}) {
  return createMuiTheme(baseTheme, themeOverrides);
}

export { baseTheme, createTheme };
