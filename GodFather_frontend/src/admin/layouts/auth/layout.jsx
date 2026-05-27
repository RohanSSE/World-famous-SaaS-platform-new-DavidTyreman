import { merge } from "es-toolkit";
import Box from "@mui/material/Box";
import { RouterLink } from "@admin/routes/components";
import { AuthContent } from "./content";
import { MainSection } from "../core/main-section";
import { LayoutSection } from "../core/layout-section";
import brandLogo from "../../../assets/mask-group.png";

function AuthLayout({ sx, cssVars, children, slotProps, layoutQuery = "md" }) {
  const renderHeader = () => (
    <Box
      className="admin-chat-header"
      sx={{ position: { [layoutQuery]: "relative" } }}
    >
      <Box className="admin-chat-header-left">
        <RouterLink href="/admin" className="admin-chat-logo-wrap" style={{ textDecoration: "none" }}>
          <img src={brandLogo} alt="The Brand Godfather" className="admin-chat-logo" />
        </RouterLink>
      </Box>
    </Box>
  );

  const renderMain = () => (
    <MainSection
      {...slotProps?.main}
      sx={[
        (theme) => ({
          alignItems: "center",
          justifyContent: "center",
          flex: 1,
          p: theme.spacing(3, 2, 6),
          [theme.breakpoints.up(layoutQuery)]: { p: theme.spacing(6, 2) },
        }),
        ...(Array.isArray(slotProps?.main?.sx) ? slotProps.main.sx : [slotProps?.main?.sx]),
      ]}
    >
      <AuthContent {...slotProps?.content}>{children}</AuthContent>
    </MainSection>
  );

  return (
    <LayoutSection
      className="admin-auth-root"
      headerSection={renderHeader()}
      footerSection={null}
      cssVars={{ "--layout-auth-content-width": "420px", ...cssVars }}
      sx={[
        {
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          bgcolor: "#0B0D1F",
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
    >
      {renderMain()}
    </LayoutSection>
  );
}

export { AuthLayout };
