import { useState, useCallback } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Avatar from "@mui/material/Avatar";
import Popover from "@mui/material/Popover";
import Divider from "@mui/material/Divider";
import MenuList from "@mui/material/MenuList";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import MenuItem, { menuItemClasses } from "@mui/material/MenuItem";
import { useRouter, usePathname } from "@admin/routes/hooks";
import { _myAccount } from "@admin/_mock";
import { clearAuthSession, getAuthSession } from "@admin/auth/session";
function AccountPopover({ data = [], sx, ...other }) {
  const router = useRouter();
  const pathname = usePathname();
  const authSession = getAuthSession();
  const [openPopover, setOpenPopover] = useState(null);
  const handleOpenPopover = useCallback((event) => {
    setOpenPopover(event.currentTarget);
  }, []);
  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);
  const handleClickItem = useCallback(
    (path) => {
      handleClosePopover();
      router.push(path);
    },
    [handleClosePopover, router]
  );
  const handleLogout = useCallback(() => {
    handleClosePopover();
    clearAuthSession();
    router.replace("/admin/sign-in");
  }, [handleClosePopover, router]);
  return <>
      <IconButton
    onClick={handleOpenPopover}
    sx={{
      p: "2px",
      width: 40,
      height: 40,
      background: (theme) => `conic-gradient(${theme.vars.palette.primary.light}, ${theme.vars.palette.warning.light}, ${theme.vars.palette.primary.light})`,
      ...sx
    }}
    {...other}
  >
        <Avatar src={_myAccount.photoURL} alt={_myAccount.displayName} sx={{ width: 1, height: 1 }}>
          {_myAccount.displayName.charAt(0).toUpperCase()}
        </Avatar>
      </IconButton>

      <Popover
    open={!!openPopover}
    anchorEl={openPopover}
    onClose={handleClosePopover}
    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
    transformOrigin={{ vertical: "top", horizontal: "right" }}
    slotProps={{
      paper: {
        sx: { width: 200 }
      }
    }}
  >
        <Box sx={{ p: 2, pb: 1.5 }}>
          <Typography variant="subtitle2" noWrap>
            {authSession?.name || _myAccount?.displayName}
          </Typography>

          <Typography variant="body2" sx={{ color: "text.secondary" }} noWrap>
            {authSession?.email || _myAccount?.email}
          </Typography>
        </Box>

        <Divider sx={{ borderStyle: "dashed" }} />

        <MenuList
    disablePadding
    sx={{
      p: 1,
      gap: 0.5,
      display: "flex",
      flexDirection: "column",
      [`& .${menuItemClasses.root}`]: {
        px: 1,
        gap: 2,
        borderRadius: 0.75,
        color: "text.secondary",
        "&:hover": { color: "text.primary" },
        [`&.${menuItemClasses.selected}`]: {
          color: "text.primary",
          bgcolor: "action.selected",
          fontWeight: "fontWeightSemiBold"
        }
      }
    }}
  >
          {data.map((option) => <MenuItem
    key={option.label}
    selected={option.href === pathname}
    onClick={() => handleClickItem(option.href)}
  >
              {option.icon}
              {option.label}
            </MenuItem>)}
        </MenuList>

        <Divider sx={{ borderStyle: "dashed" }} />

        <Box sx={{ p: 1 }}>
          <Button fullWidth color="error" size="medium" variant="text" onClick={handleLogout}>
            Logout
          </Button>
        </Box>
      </Popover>
    </>;
}
export {
  AccountPopover
};
