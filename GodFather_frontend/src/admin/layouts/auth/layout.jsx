import { merge } from "es-toolkit";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Alert from "@mui/material/Alert";
import { RouterLink } from "@admin/routes/components";
import { Logo } from "@admin/components/logo";
import { AuthContent } from "./content";
import { MainSection } from "../core/main-section";
import { LayoutSection } from "../core/layout-section";
import { HeaderSection } from "../core/header-section";
function AuthLayout({
  sx,
  cssVars,
  children,
  slotProps,
  layoutQuery = "md"
}) {
  const renderHeader = () => {
    const headerSlotProps = { container: { maxWidth: false } };
    const headerSlots = {
      topArea: <Alert severity="info" sx={{ display: "none", borderRadius: 0 }}>
          This is an info Alert.
        </Alert>,
      leftArea: <>
          {
        /** @slot Logo */
      }
          <Logo />
        </>,
      rightArea: <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 1, sm: 1.5 } }}>
          {
        /** @slot Help link */
      }
          <Link href="#" component={RouterLink} color="inherit" sx={{ typography: "subtitle2" }}>
            Need help?
          </Link>
        </Box>
    };
    return <HeaderSection
      disableElevation
      layoutQuery={layoutQuery}
      {...slotProps?.header}
      slots={{ ...headerSlots, ...slotProps?.header?.slots }}
      slotProps={merge(headerSlotProps, slotProps?.header?.slotProps ?? {})}
      sx={[
        { position: { [layoutQuery]: "fixed" } },
        ...Array.isArray(slotProps?.header?.sx) ? slotProps?.header?.sx ?? [] : [slotProps?.header?.sx]
      ]}
    />;
  };
  const renderFooter = () => null;
  const renderMain = () => <MainSection
    {...slotProps?.main}
    sx={[
      (theme) => ({
        alignItems: "center",
        p: theme.spacing(3, 2, 10, 2),
        [theme.breakpoints.up(layoutQuery)]: {
          justifyContent: "center",
          p: theme.spacing(10, 0, 10, 0)
        }
      }),
      ...Array.isArray(slotProps?.main?.sx) ? slotProps?.main?.sx ?? [] : [slotProps?.main?.sx]
    ]}
  >
      <AuthContent {...slotProps?.content}>{children}</AuthContent>
    </MainSection>;
  return <LayoutSection
    headerSection={renderHeader()}
    footerSection={renderFooter()}
    cssVars={{ "--layout-auth-content-width": "420px", ...cssVars }}
    sx={[
      (theme) => ({
        position: "relative",
        "&::before": backgroundStyles()
      }),
      ...Array.isArray(sx) ? sx : [sx]
    ]}
  >
      {renderMain()}
    </LayoutSection>;
}
const backgroundStyles = () => ({
  zIndex: 1,
  opacity: 0.24,
  width: "100%",
  height: "100%",
  content: "''",
  position: "absolute",
  backgroundSize: "cover",
  backgroundRepeat: "no-repeat",
  backgroundPosition: "center center",
  backgroundImage: "url(/assets/background/overlay.jpg)"
});
export {
  AuthLayout
};
