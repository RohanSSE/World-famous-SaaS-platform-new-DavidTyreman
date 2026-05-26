import { useEffect } from "react";
import { varAlpha } from "minimal-shared/utils";
import Box from "@mui/material/Box";
import ListItem from "@mui/material/ListItem";
import { useTheme } from "@mui/material/styles";
import ListItemButton from "@mui/material/ListItemButton";
import Drawer, { drawerClasses } from "@mui/material/Drawer";
import { usePathname } from "@admin/routes/hooks";
import { RouterLink } from "@admin/routes/components";
import { Logo } from "@admin/components/logo";
import { Scrollbar } from "@admin/components/scrollbar";
import { NavUpgrade } from "../components/nav-upgrade";
import { WorkspacesPopover } from "../components/workspaces-popover";
function NavDesktop({
  sx,
  data,
  slots,
  workspaces,
  layoutQuery
}) {
  const theme = useTheme();
  return <Box
    sx={{
      pt: 2.5,
      px: 2.5,
      top: 0,
      left: 0,
      height: 1,
      display: "none",
      position: "fixed",
      flexDirection: "column",
      zIndex: "var(--layout-nav-zIndex)",
      width: "var(--layout-nav-vertical-width)",
      borderRight: `1px solid ${varAlpha(theme.vars.palette.grey["500Channel"], 0.12)}`,
      [theme.breakpoints.up(layoutQuery)]: {
        display: "flex"
      },
      ...sx
    }}
  >
      <NavContent data={data} slots={slots} workspaces={workspaces} />
    </Box>;
}
function NavMobile({
  sx,
  data,
  open,
  slots,
  onClose,
  workspaces
}) {
  const pathname = usePathname();
  useEffect(() => {
    if (open) {
      onClose();
    }
  }, [pathname]);
  return <Drawer
    open={open}
    onClose={onClose}
    sx={{
      [`& .${drawerClasses.paper}`]: {
        pt: 2.5,
        px: 2.5,
        overflow: "unset",
        width: "var(--layout-nav-mobile-width)",
        ...sx
      }
    }}
  >
      <NavContent data={data} slots={slots} workspaces={workspaces} />
    </Drawer>;
}
function NavContent({ data, slots, workspaces, sx }) {
  const pathname = usePathname();
  return <>
      <Logo />

      {slots?.topArea}

      <WorkspacesPopover data={workspaces} sx={{ my: 2 }} />

      <Scrollbar fillContent>
        <Box
    component="nav"
    sx={[
      {
        display: "flex",
        flex: "1 1 auto",
        flexDirection: "column"
      },
      ...Array.isArray(sx) ? sx : [sx]
    ]}
  >
          <Box
    component="ul"
    sx={{
      gap: 0.5,
      display: "flex",
      flexDirection: "column"
    }}
  >
            {data.map((item) => {
    const isActived = item.path === pathname;
    return <ListItem disableGutters disablePadding key={item.title}>
                  <ListItemButton
      disableGutters
      component={RouterLink}
      href={item.path}
      sx={[
        (theme) => ({
          pl: 2,
          py: 1,
          gap: 2,
          pr: 1.5,
          borderRadius: 0.75,
          typography: "body2",
          fontWeight: "fontWeightMedium",
          color: theme.vars.palette.text.secondary,
          minHeight: 44,
          ...isActived && {
            fontWeight: "fontWeightSemiBold",
            color: theme.vars.palette.primary.main,
            bgcolor: varAlpha(theme.vars.palette.primary.mainChannel, 0.08),
            "&:hover": {
              bgcolor: varAlpha(theme.vars.palette.primary.mainChannel, 0.16)
            }
          }
        })
      ]}
    >
                    <Box component="span" sx={{ width: 24, height: 24 }}>
                      {item.icon}
                    </Box>

                    <Box component="span" sx={{ flexGrow: 1 }}>
                      {item.title}
                    </Box>

                    {item.info && item.info}
                  </ListItemButton>
                </ListItem>;
  })}
          </Box>
        </Box>
      </Scrollbar>

      {slots?.bottomArea}

      <NavUpgrade />
    </>;
}
export {
  NavContent,
  NavDesktop,
  NavMobile
};
