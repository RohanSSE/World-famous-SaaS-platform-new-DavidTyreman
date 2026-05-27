import { useState, useCallback } from "react";
import Box from "@mui/material/Box";
import Popover from "@mui/material/Popover";
import TableRow from "@mui/material/TableRow";
import Checkbox from "@mui/material/Checkbox";
import MenuList from "@mui/material/MenuList";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import MenuItem, { menuItemClasses } from "@mui/material/MenuItem";
import { Label } from "@admin/components/label";
import { Iconify } from "@admin/components/iconify";

function AgencyTableRow({
  row,
  selected,
  onSelectRow,
  onActivate,
  onDeactivate,
}) {
  const [openPopover, setOpenPopover] = useState(null);

  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);

  return (
    <>
      <TableRow hover tabIndex={-1} role="checkbox" selected={selected} className="admin-users-table-row">
        <TableCell padding="checkbox">
          <Checkbox disableRipple checked={selected} onChange={onSelectRow} />
        </TableCell>

        <TableCell component="th" scope="row">
          <Box sx={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis" }}>
            {row.name}
          </Box>
        </TableCell>

        <TableCell sx={{ overflow: "hidden", textOverflow: "ellipsis" }}>{row.owner_email || "—"}</TableCell>

        <TableCell>{row.sessions_count ?? 0}</TableCell>

        <TableCell>
          <Label color={row.status === "active" ? "success" : "warning"}>
            {row.status === "pending" ? "Pending" : row.status}
          </Label>
        </TableCell>

        <TableCell align="right" padding="none" sx={{ pr: 1 }}>
          <IconButton
            size="small"
            onClick={(e) => setOpenPopover(e.currentTarget)}
            aria-label="Actions"
          >
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
            width: 160,
            display: "flex",
            flexDirection: "column",
            [`& .${menuItemClasses.root}`]: { px: 1, gap: 2, borderRadius: 0.75 },
          }}
        >
          {row.status !== "active" ? (
            <MenuItem
              onClick={() => {
                onActivate(row.id);
                handleClosePopover();
              }}
            >
              Activate
            </MenuItem>
          ) : (
            <MenuItem
              onClick={() => {
                onDeactivate(row.id);
                handleClosePopover();
              }}
              sx={{ color: "warning.main" }}
            >
              Deactivate
            </MenuItem>
          )}
        </MenuList>
      </Popover>
    </>
  );
}

export { AgencyTableRow };
