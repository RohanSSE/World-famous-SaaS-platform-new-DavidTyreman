import { useState, useCallback } from "react";
import Box from "@mui/material/Box";
import Avatar from "@mui/material/Avatar";
import Popover from "@mui/material/Popover";
import TableRow from "@mui/material/TableRow";
import Checkbox from "@mui/material/Checkbox";
import MenuList from "@mui/material/MenuList";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import MenuItem, { menuItemClasses } from "@mui/material/MenuItem";
import { Label } from "@admin/components/label";
import { Iconify } from "@admin/components/iconify";
function UserTableRow({
  row,
  selected,
  onSelectRow,
  onAssignRole,
  onActivate,
  onDeactivate
}) {
  const [openPopover, setOpenPopover] = useState(null);
  const handleOpenPopover = useCallback((event) => {
    setOpenPopover(event.currentTarget);
  }, []);
  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);
  return <>
      <TableRow hover tabIndex={-1} role="checkbox" selected={selected} className="admin-users-table-row">
        <TableCell padding="checkbox">
          <Checkbox disableRipple checked={selected} onChange={onSelectRow} />
        </TableCell>

        <TableCell component="th" scope="row">
          <Box
    sx={{
      gap: 2,
      display: "flex",
      alignItems: "center"
    }}
  >
            <Avatar alt={row.name} src={row.avatarUrl} sx={{ width: 32, height: 32 }} />
            <Box component="span" sx={{ overflow: "hidden", textOverflow: "ellipsis" }}>
              {row.name}
            </Box>
          </Box>
        </TableCell>

        <TableCell>{row.company}</TableCell>

        <TableCell>{row.role}</TableCell>

        <TableCell>{row.phone || "—"}</TableCell>

        <TableCell>
          <Label color={row.status === "active" ? "success" : "warning"}>
            {row.status === "pending" ? "Pending" : row.status}
          </Label>
        </TableCell>

        <TableCell align="right" padding="none" sx={{ pr: 1 }}>
          <IconButton size="small" onClick={handleOpenPopover} aria-label="Actions">
            <Iconify icon="eva:more-vertical-fill" width={20} />
          </IconButton>
        </TableCell>
      </TableRow>

      <Popover
    open={!!openPopover}
    anchorEl={openPopover}
    onClose={handleClosePopover}
    anchorOrigin={{ vertical: "top", horizontal: "left" }}
    transformOrigin={{ vertical: "top", horizontal: "right" }}
  >
        <MenuList
    disablePadding
    sx={{
      p: 0.5,
      gap: 0.5,
      width: 140,
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
          <MenuItem
    onClick={() => {
      onAssignRole(row.id);
      handleClosePopover();
    }}
    disabled={row.role === "SuperAdmin"}
  >
            <Iconify icon="solar:pen-bold" />
            Assign
          </MenuItem>

          {row.status !== "active" ? <MenuItem
    onClick={() => {
      onActivate(row.id);
      handleClosePopover();
    }}
  >
              <Iconify icon="solar:check-circle-bold" />
              Activate
            </MenuItem> : <MenuItem
    onClick={() => {
      onDeactivate(row.id);
      handleClosePopover();
    }}
    sx={{ color: "warning.main" }}
  >
              <Iconify icon="solar:check-circle-bold" />
              Deactivate
            </MenuItem>}

        </MenuList>
      </Popover>
    </>;
}
export {
  UserTableRow
};
