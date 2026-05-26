import "@admin/global.css";
import { useEffect } from "react";
import { usePathname } from "@admin/routes/hooks";
import { ThemeProvider } from "@admin/theme/theme-provider";

function App({ children }) {
  useScrollToTop();

  return <ThemeProvider>{children}</ThemeProvider>;
}

function useScrollToTop() {
  const pathname = usePathname();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
}

export default App;
