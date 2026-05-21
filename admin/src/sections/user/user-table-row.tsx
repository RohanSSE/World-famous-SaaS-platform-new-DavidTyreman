import { useState, useCallback } from 'react';

import Box from '@mui/material/Box';
import Avatar from '@mui/material/Avatar';
import Popover from '@mui/material/Popover';
import TableRow from '@mui/material/TableRow';
import Checkbox from '@mui/material/Checkbox';
import MenuList from '@mui/material/MenuList';
import TableCell from '@mui/material/TableCell';
import IconButton from '@mui/material/IconButton';
import MenuItem, { menuItemClasses } from '@mui/material/MenuItem';

import { Label } from 'src/components/label';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

export type UserRole = 'SuperAdmin' | 'Agency' | 'User';
export type UserStatus = 'active' | 'inactive';

export type UserProps = {
  id: string;
  name: string;
  role: UserRole;
  status: UserStatus;
  company: string;
  avatarUrl: string;
  isVerified: boolean;
};

type UserTableRowProps = {
  row: UserProps;
  selected: boolean;
  onSelectRow: () => void;
  onAssignRole: (id: string) => void;
  onActivate: (id: string) => void;
  onDeactivate: (id: string) => void;
};

export function UserTableRow({
  row,
  selected,
  onSelectRow,
  onAssignRole,
  onActivate,
  onDeactivate,
}: UserTableRowProps) {
  const [openPopover, setOpenPopover] = useState<HTMLButtonElement | null>(null);

  const handleOpenPopover = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    setOpenPopover(event.currentTarget);
  }, []);

  const handleClosePopover = useCallback(() => {
    setOpenPopover(null);
  }, []);

  return (
    <>
      <TableRow hover tabIndex={-1} role="checkbox" selected={selected}>
        <TableCell padding="checkbox">
          <Checkbox disableRipple checked={selected} onChange={onSelectRow} />
        </TableCell>

        <TableCell component="th" scope="row">
          <Box
            sx={{
              gap: 2,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Avatar alt={row.name} src={row.avatarUrl} />
            {row.name}
          </Box>
        </TableCell>

        <TableCell>{row.company}</TableCell>

        <TableCell>{row.role}</TableCell>

        <TableCell align="center">
          {row.isVerified ? (
            <Iconify width={22} icon="solar:check-circle-bold" sx={{ color: 'success.main' }} />
          ) : (
            '-'
          )}
        </TableCell>

        <TableCell>
          <Label color={row.status === 'inactive' ? 'warning' : 'success'}>{row.status}</Label>
        </TableCell>

        <TableCell align="right">
          <IconButton onClick={handleOpenPopover}>
            <Iconify icon="eva:more-vertical-fill" />
          </IconButton>
        </TableCell>
      </TableRow>

      <Popover
        open={!!openPopover}
        anchorEl={openPopover}
        onClose={handleClosePopover}
        anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuList
          disablePadding
          sx={{
            p: 0.5,
            gap: 0.5,
            width: 140,
            display: 'flex',
            flexDirection: 'column',
            [`& .${menuItemClasses.root}`]: {
              px: 1,
              gap: 2,
              borderRadius: 0.75,
              [`&.${menuItemClasses.selected}`]: { bgcolor: 'action.selected' },
            },
          }}
        >
          <MenuItem
            onClick={() => {
              onAssignRole(row.id);
              handleClosePopover();
            }}
            disabled={row.role === 'SuperAdmin'}
          >
            <Iconify icon="solar:pen-bold" />
            Assign
          </MenuItem>

          {row.status === 'inactive' ? (
            <MenuItem
              onClick={() => {
                onActivate(row.id);
                handleClosePopover();
              }}
            >
              <Iconify icon="solar:check-circle-bold" />
              Activate
            </MenuItem>
          ) : (
            <MenuItem
              onClick={() => {
                onDeactivate(row.id);
                handleClosePopover();
              }}
              sx={{ color: 'warning.main' }}
            >
              <Iconify icon="solar:check-circle-bold" />
              Deactivate
            </MenuItem>
          )}

        </MenuList>
      </Popover>
    </>
  );
}
