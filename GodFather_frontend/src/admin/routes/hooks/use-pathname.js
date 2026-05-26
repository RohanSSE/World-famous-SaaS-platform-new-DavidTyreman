import { useMemo } from "react";
import { useLocation } from "react-router";
function usePathname() {
  const { pathname } = useLocation();
  return useMemo(() => pathname, [pathname]);
}
export {
  usePathname
};
