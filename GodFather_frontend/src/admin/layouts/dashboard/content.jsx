import { mergeClasses } from "minimal-shared/utils";
import Container from "@mui/material/Container";
import { layoutClasses } from "../core/classes";
function DashboardContent({
  sx,
  children,
  className,
  disablePadding,
  maxWidth = "lg",
  layoutQuery = "lg",
  ...other
}) {
  return <Container
    className={mergeClasses([layoutClasses.content, className])}
    maxWidth={maxWidth}
    sx={[
      (theme) => ({
        display: "flex",
        flex: "1 1 auto",
        flexDirection: "column",
        pt: "var(--layout-dashboard-content-pt)",
        pb: "var(--layout-dashboard-content-pb)",
        [theme.breakpoints.up(layoutQuery)]: {
          px: "var(--layout-dashboard-content-px)"
        },
        ...disablePadding && {
          p: {
            xs: 0,
            sm: 0,
            md: 0,
            lg: 0,
            xl: 0
          }
        }
      }),
      ...Array.isArray(sx) ? sx : [sx]
    ]}
    {...other}
  >
      {children}
    </Container>;
}
export {
  DashboardContent
};
