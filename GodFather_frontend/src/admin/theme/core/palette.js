import { varAlpha, createPaletteChannel } from "minimal-shared/utils";
import { themeConfig } from "../theme-config";
const primary = createPaletteChannel(themeConfig.palette.primary);
const secondary = createPaletteChannel(themeConfig.palette.secondary);
const info = createPaletteChannel(themeConfig.palette.info);
const success = createPaletteChannel(themeConfig.palette.success);
const warning = createPaletteChannel(themeConfig.palette.warning);
const error = createPaletteChannel(themeConfig.palette.error);
const common = createPaletteChannel(themeConfig.palette.common);
const grey = createPaletteChannel(themeConfig.palette.grey);
const text = {
  light: createPaletteChannel({
    primary: grey[800],
    secondary: grey[600],
    disabled: grey[500]
  })
};
const background = {
  light: createPaletteChannel({
    paper: "#FFFFFF",
    default: grey[100],
    neutral: grey[200]
  })
};
const baseAction = {
  hover: varAlpha(grey["500Channel"], 0.08),
  selected: varAlpha(grey["500Channel"], 0.16),
  focus: varAlpha(grey["500Channel"], 0.24),
  disabled: varAlpha(grey["500Channel"], 0.8),
  disabledBackground: varAlpha(grey["500Channel"], 0.24),
  hoverOpacity: 0.08,
  disabledOpacity: 0.48
};
const action = {
  light: { ...baseAction, active: grey[600] }
};
const basePalette = {
  primary,
  secondary,
  info,
  success,
  warning,
  error,
  common,
  grey,
  divider: varAlpha(grey["500Channel"], 0.2)
};
const palette = {
  light: {
    ...basePalette,
    text: text.light,
    background: background.light,
    action: action.light
  }
};
export {
  action,
  background,
  baseAction,
  basePalette,
  common,
  error,
  grey,
  info,
  palette,
  primary,
  secondary,
  success,
  text,
  warning
};
