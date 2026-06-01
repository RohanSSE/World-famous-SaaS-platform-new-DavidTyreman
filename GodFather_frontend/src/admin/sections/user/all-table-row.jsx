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

function AllTableRow({
  row,
  selected,
  onSelectRow,
  onActivateUser,
  onDeactivateUser,
  onActivateAgency,
  onDeactivateAgency,
}) {
  const [openPopover, setOpenPopover] = useState(null);
  const isOrg = row.recordType === "agency-org";

  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);

  const handleActivate = () => {
    if (isOrg) onActivateAgency(row.id);
    else onActivateUser(row.id);
    handleClosePopover();
  };

  const handleDeactivate = () => {
    if (isOrg) onDeactivateAgency(row.id);
    else onDeactivateUser(row.id);
    handleClosePopover();
  };

  const typeLabel = isOrg ? "Agency" : "User";
  const typeColor = isOrg ? "secondary" : "info";

  return (
    <>
      <TableRow hover tabIndex={-1} role="checkbox" selected={selected} className="admin-users-table-row">
        <TableCell padding="checkbox">
          <Checkbox disableRipple checked={selected} onChange={onSelectRow} />
        </TableCell>

        <TableCell>
          <Label color={typeColor}>{typeLabel}</Label>
        </TableCell>

        <TableCell component="th" scope="row">
          {!isOrg ? (
            <Box sx={{ gap: 1, display: "flex", alignItems: "center" }}>
              <Avatar alt={row.name} src={row.avatarUrl} sx={{ width: 32, height: 32 }} />
              <Box component="span" sx={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                {row.name}
              </Box>
            </Box>
          ) : (
            <Box sx={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis" }}>
              {row.name}
            </Box>
          )}
        </TableCell>

        <TableCell sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }}>
          {row.detail || "—"}
        </TableCell>

        <TableCell>{isOrg ? "—" : row.info || "—"}</TableCell>

        <TableCell>
          <Label color={row.status === "active" ? "success" : "warning"}>
            {row.status === "pending" ? "Pending" : row.status}
          </Label>
        </TableCell>

        <TableCell align="right" padding="none" sx={{ pr: 1 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setOpenPopover(e.currentTarget);
            }}
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
            <MenuItem onClick={handleActivate}>Activate</MenuItem>
          ) : (
            <MenuItem onClick={handleDeactivate} sx={{ color: "error.main" }}>
              Deactivate
            </MenuItem>
          )}
        </MenuList>
      </Popover>
    </>
  );
}

export { AllTableRow };
