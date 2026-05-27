import Box from "@mui/material/Box";
import TableRow from "@mui/material/TableRow";
import Checkbox from "@mui/material/Checkbox";
import TableHead from "@mui/material/TableHead";
import TableCell from "@mui/material/TableCell";
import TableSortLabel from "@mui/material/TableSortLabel";
import { visuallyHidden } from "./utils";
function UserTableHead({
  order,
  onSort,
  orderBy,
  rowCount,
  headLabel,
  numSelected,
  onSelectAllRows,
  hideCheckbox = false,
}) {
  return <TableHead>
      <TableRow>
        {!hideCheckbox && (
        <TableCell padding="checkbox">
          <Checkbox
    indeterminate={numSelected > 0 && numSelected < rowCount}
    checked={rowCount > 0 && numSelected === rowCount}
    onChange={(event) => onSelectAllRows(event.target.checked)}
  />
        </TableCell>
        )}

        {headLabel.map((headCell) => {
          const isAction = headCell.id === "actions";
          return (
            <TableCell
              key={headCell.id || "actions"}
              align={headCell.align || "left"}
              sortDirection={!isAction && orderBy === headCell.id ? order : false}
              sx={{
                width: headCell.width,
                minWidth: headCell.minWidth,
                px: 1.5,
                py: 1.25,
                whiteSpace: "nowrap",
              }}
            >
              {isAction ? (
                headCell.label
              ) : (
                <TableSortLabel
                  hideSortIcon
                  active={orderBy === headCell.id}
                  direction={orderBy === headCell.id ? order : "asc"}
                  onClick={() => onSort(headCell.id)}
                >
                  {headCell.label}
                  {orderBy === headCell.id ? (
                    <Box sx={{ ...visuallyHidden }}>
                      {order === "desc" ? "sorted descending" : "sorted ascending"}
                    </Box>
                  ) : null}
                </TableSortLabel>
              )}
            </TableCell>
          );
        })}
      </TableRow>
    </TableHead>;
}
export {
  UserTableHead
};
