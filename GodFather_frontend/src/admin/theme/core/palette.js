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
  dark: createPaletteChannel({
    primary: "#FFFFFF",
    secondary: "#99A1B8",
    disabled: "#6B7280",
  }),
};

const background = {
  dark: createPaletteChannel({
    paper: "#1A1C3A",
    default: "#0B0D1F",
    neutral: "#12132D",
  }),
};

const action = {
  dark: {
    hover: varAlpha(primary.mainChannel, 0.1),
    selected: varAlpha(primary.mainChannel, 0.18),
    focus: varAlpha(primary.mainChannel, 0.24),
    disabled: varAlpha(grey["500Channel"], 0.8),
    disabledBackground: varAlpha(grey["500Channel"], 0.24),
    hoverOpacity: 0.08,
    disabledOpacity: 0.48,
    active: "#86E3FF",
  },
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
  divider: varAlpha(grey["500Channel"], 0.16),
};

const palette = {
  dark: {
    ...basePalette,
    divider: varAlpha(primary.mainChannel, 0.12),
    text: text.dark,
    background: background.dark,
    action: action.dark,
  },
};

export {
  action,
  background,
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
  warning,
};
