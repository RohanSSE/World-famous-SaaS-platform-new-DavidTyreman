import { useLayoutEffect } from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider as ThemeVarsProvider } from '@mui/material/styles';
import { createTheme } from './create-theme';

function ThemeProvider({ themeOverrides, children, ...other }) {
  const theme = createTheme({ themeOverrides });

  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-color-scheme', 'light');
  }, []);

  return (
    <ThemeVarsProvider theme={theme} defaultMode="light" {...other}>
      <CssBaseline enableColorScheme />
      {children}
    </ThemeVarsProvider>
  );
}

export { ThemeProvider };
