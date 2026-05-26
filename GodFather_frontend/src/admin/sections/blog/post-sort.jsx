import { useState, useCallback } from "react";
import { varAlpha } from "minimal-shared/utils";
import Button from "@mui/material/Button";
import Popover from "@mui/material/Popover";
import MenuList from "@mui/material/MenuList";
import MenuItem, { menuItemClasses } from "@mui/material/MenuItem";
import { Iconify } from "@admin/components/iconify";
function PostSort({ options, sortBy, onSort, sx, ...other }) {
  const [openPopover, setOpenPopover] = useState(null);
  const handleOpenPopover = useCallback((event) => {
    setOpenPopover(event.currentTarget);
  }, []);
  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);
  return <>
      <Button
    disableRipple
    color="inherit"
    onClick={handleOpenPopover}
    endIcon={<Iconify
      icon={openPopover ? "eva:arrow-ios-upward-fill" : "eva:arrow-ios-downward-fill"}
      sx={{
        ml: -0.5
      }}
    />}
    sx={[
      {
        bgcolor: (theme) => varAlpha(theme.vars.palette.grey["500Channel"], 0.08)
      },
      ...Array.isArray(sx) ? sx : [sx]
    ]}
    {...other}
  >
        {options.find((option) => option.value === sortBy)?.label}
      </Button>

      <Popover
    open={!!openPopover}
    anchorEl={openPopover}
    onClose={handleClosePopover}
    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
    transformOrigin={{ vertical: "top", horizontal: "right" }}
  >
        <MenuList
    disablePadding
    sx={{
      p: 0.5,
      gap: 0.5,
      width: 160,
      display: "flex",
      flexDirection: "column",
      [`& .${menuItemClasses.root}`]: {
        px: 1,
        gap: 2,
        borderRadius: 0.75,
        [`&.${menuItemClasses.selected}`]: { bgcolor: "action.selected" }
      }
    }}
  >
          {options.map((option) => <MenuItem
    key={option.value}
    selected={option.value === sortBy}
    onClick={() => {
      onSort(option.value);
      handleClosePopover();
    }}
  >
              {option.label}
            </MenuItem>)}
        </MenuList>
      </Popover>
    </>;
}
export {
  PostSort
};
