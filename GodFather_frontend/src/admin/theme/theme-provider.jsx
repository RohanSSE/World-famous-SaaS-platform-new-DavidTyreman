import { useLayoutEffect } from "react";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider as ThemeVarsProvider } from "@mui/material/styles";
import { createTheme } from "./create-theme";

function ThemeProvider({ themeOverrides, children, ...other }) {
  const theme = createTheme({ themeOverrides });

  useLayoutEffect(() => {
    document.documentElement.setAttribute("data-color-scheme", "dark");
    document.body.classList.add("godfather-admin");
    return () => {
      document.documentElement.removeAttribute("data-color-scheme");
      document.body.classList.remove("godfather-admin");
    };
  }, []);

  return (
    <ThemeVarsProvider theme={theme} defaultMode="dark" {...other}>
      <CssBaseline enableColorScheme />
      {children}
    </ThemeVarsProvider>
  );
}

export { ThemeProvider };
