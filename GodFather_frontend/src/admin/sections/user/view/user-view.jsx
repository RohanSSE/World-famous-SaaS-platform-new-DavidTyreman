import { useState, useCallback, useEffect } from "react";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Card from "@mui/material/Card";
import Tabs from "@mui/material/Tabs";
import Table from "@mui/material/Table";
import Alert from "@mui/material/Alert";
import TableBody from "@mui/material/TableBody";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import TableContainer from "@mui/material/TableContainer";
import TablePagination from "@mui/material/TablePagination";
import adminApi from "@admin/lib/adminApi";
import { TableNoData } from "../table-no-data";
import { UserTableRow } from "../user-table-row";
import { AgencyTableRow } from "../agency-table-row";
import { AllTableRow } from "../all-table-row";
import { UserTableHead } from "../user-table-head";
import { TableEmptyRows } from "../table-empty-rows";
import { UserTableToolbar } from "../user-table-toolbar";
import { emptyRows, applyFilter, getComparator } from "../utils";
import {
  isClientUser,
  mapApiUser,
  mapApiAgency,
  buildAllRows,
  buildAgencyTabRows,
  countAllTab,
} from "../directory-mappers";

const USER_HEAD = [
  { id: "name", label: "Email", width: "26%" },
  { id: "company", label: "Agency", width: "20%" },
  { id: "role", label: "Role", width: "12%" },
  { id: "phone", label: "Phone", width: "14%" },
  { id: "status", label: "Status", width: "12%" },
  { id: "actions", label: "Action", align: "right", width: 72 },
];

const AGENCY_HEAD = [
  { id: "name", label: "Agency", width: "32%" },
  { id: "owner_email", label: "Owner", width: "32%" },
  { id: "sessions_count", label: "Sessions", width: "14%" },
  { id: "status", label: "Status", width: "12%" },
  { id: "actions", label: "Action", align: "right", width: 72 },
];

const ALL_HEAD = [
  { id: "recordType", label: "Type", width: "10%" },
  { id: "name", label: "Name", width: "28%" },
  { id: "detail", label: "Agency / Owner", width: "24%" },
  { id: "info", label: "Role", width: "14%" },
  { id: "status", label: "Status", width: "12%" },
  { id: "actions", label: "Action", align: "right", width: 72 },
];

function getTabData(tab, users, agencies) {
  const allCount = countAllTab(users, agencies);
  const activeUsers = users.filter((u) => u.status === "active" && isClientUser(u));

  switch (tab) {
    case "users":
      return {
        mode: "users",
        rows: activeUsers,
        headLabel: USER_HEAD,
        searchKeys: ["name", "company", "role", "phone"],
        searchPlaceholder: "Search active users...",
        count: activeUsers.length,
      };
    case "agencies": {
      const agencyRows = buildAgencyTabRows(agencies);
      return {
        mode: "agencies",
        rows: agencyRows,
        headLabel: AGENCY_HEAD,
        searchKeys: ["name", "owner_email"],
        searchPlaceholder: "Search agencies...",
        count: agencyRows.length,
      };
    }
    case "all":
    default:
      return {
        mode: "all",
        rows: buildAllRows(users, agencies),
        headLabel: ALL_HEAD,
        searchKeys: ["name", "detail", "info", "role", "status"],
        searchPlaceholder: "Search users and agencies...",
        count: allCount,
      };
  }
}

function UserView() {
  const [tab, setTab] = useState("all");
  const [filterName, setFilterName] = useState("");
  const [users, setUsers] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const table = useTable();

  const loadUsers = useCallback(async () => {
    const data = await adminApi.listUsers();
    const list = Array.isArray(data) ? data : data?.results || [];
    setUsers(list.map(mapApiUser));
  }, []);

  const loadAgencies = useCallback(async () => {
    const data = await adminApi.listAgencies();
    const list = Array.isArray(data) ? data : data?.results || [];
    setAgencies(list.map(mapApiAgency));
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      await Promise.all([loadUsers(), loadAgencies()]);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to load data. Sign out and sign in again at /admin/sign-in with an admin or superuser account.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }, [loadUsers, loadAgencies]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const tabData = getTabData(tab, users, agencies);
  const { mode, rows, headLabel, searchKeys, searchPlaceholder } = tabData;

  const activeUsersCount = users.filter((u) => u.status === "active" && isClientUser(u)).length;
  const agencyTabCount = agencies.length;
  const allCount = countAllTab(users, agencies);

  const dataFiltered = applyFilter({
    inputData: rows,
    comparator: getComparator(table.order, table.orderBy),
    filterName,
    searchKeys,
  });

  const handleActivateUser = useCallback(async (id) => {
    setActionError("");
    try {
      await adminApi.updateUser(id, { is_active: true });
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? { ...u, status: "active", isVerified: true } : u)),
      );
    } catch (err) {
      setActionError(err?.message || "Failed to activate user");
    }
  }, []);

  const handleDeactivateUser = useCallback(async (id) => {
    setActionError("");
    try {
      await adminApi.updateUser(id, { is_active: false });
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? { ...u, status: "pending", isVerified: false } : u)),
      );
    } catch (err) {
      setActionError(err?.message || "Failed to deactivate user");
    }
  }, []);

  const handleActivateAgency = useCallback(async (id) => {
    setActionError("");
    try {
      await adminApi.updateAgency(id, { is_active: true });
      await loadAll();
    } catch (err) {
      setActionError(err?.message || "Failed to activate agency");
    }
  }, [loadAll]);

  const handleDeactivateAgency = useCallback(async (id) => {
    setActionError("");
    try {
      await adminApi.updateAgency(id, { is_active: false });
      await loadAll();
    } catch (err) {
      setActionError(err?.message || "Failed to deactivate agency");
    }
  }, [loadAll]);

  const notFound = !dataFiltered.length && !!filterName;

  return (
    <>
      <Box sx={{ mb: 3, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="h4" className="adb-page-title" sx={{ mb: 0 }}>
          Users & Agencies
        </Typography>
      </Box>

      <Tabs
        value={tab}
        onChange={(_, v) => {
          setTab(v);
          setFilterName("");
          table.onResetPage();
        }}
        sx={{ mb: 3 }}
      >
        <Tab value="all" label={`All (${allCount})`} />
        <Tab value="users" label={`Users (${activeUsersCount})`} />
        <Tab value="agencies" label={`Agency (${agencyTabCount})`} />
      </Tabs>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {actionError && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setActionError("")}>
          {actionError}
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 2, bgcolor: "rgba(57, 89, 229, 0.12)", color: "#86e3ff" }} icon={false}>
        Use ⋮ on a row to activate or deactivate agencies and users.
      </Alert>

      <Card>
        <UserTableToolbar
          numSelected={table.selected.length}
          filterName={filterName}
          searchPlaceholder={searchPlaceholder}
          onFilterName={(event) => {
            setFilterName(event.target.value);
            table.onResetPage();
          }}
        />

        {loading ? (
          <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer className="admin-users-table-wrap">
              <Table className="admin-users-table" size="small">
                <UserTableHead
                  order={table.order}
                  orderBy={table.orderBy}
                  rowCount={rows.length}
                  numSelected={table.selected.length}
                  onSort={table.onSort}
                  onSelectAllRows={(checked) =>
                    table.onSelectAllRows(
                      checked,
                      rows.map((r) => r.rowKey || r.id),
                    )
                  }
                  headLabel={headLabel}
                />
                <TableBody>
                  {dataFiltered
                    .slice(
                      table.page * table.rowsPerPage,
                      table.page * table.rowsPerPage + table.rowsPerPage,
                    )
                    .map((row) => {
                      const rowId = row.rowKey || row.id;
                      if (mode === "users") {
                        return (
                          <UserTableRow
                            key={rowId}
                            row={row}
                            selected={table.selected.includes(rowId)}
                            onSelectRow={() => table.onSelectRow(rowId)}
                            onAssignRole={() => {}}
                            onActivate={handleActivateUser}
                            onDeactivate={handleDeactivateUser}
                          />
                        );
                      }
                      if (mode === "agencies") {
                        return (
                          <AgencyTableRow
                            key={rowId}
                            row={row}
                            selected={table.selected.includes(rowId)}
                            onSelectRow={() => table.onSelectRow(rowId)}
                            onActivate={handleActivateAgency}
                            onDeactivate={handleDeactivateAgency}
                          />
                        );
                      }
                      return (
                        <AllTableRow
                          key={rowId}
                          row={row}
                          selected={table.selected.includes(rowId)}
                          onSelectRow={() => table.onSelectRow(rowId)}
                          onActivateUser={handleActivateUser}
                          onDeactivateUser={handleDeactivateUser}
                          onActivateAgency={handleActivateAgency}
                          onDeactivateAgency={handleDeactivateAgency}
                        />
                      );
                    })}

                  <TableEmptyRows
                    height={68}
                    emptyRows={emptyRows(table.page, table.rowsPerPage, rows.length)}
                  />

                  {notFound && <TableNoData searchQuery={filterName} />}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              page={table.page}
              count={dataFiltered.length}
              rowsPerPage={table.rowsPerPage}
              onPageChange={table.onChangePage}
              rowsPerPageOptions={[5, 10, 25, 50]}
              onRowsPerPageChange={table.onChangeRowsPerPage}
            />
          </>
        )}
      </Card>
    </>
  );
}

function useTable() {
  const [page, setPage] = useState(0);
  const [orderBy, setOrderBy] = useState("name");
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selected, setSelected] = useState([]);
  const [order, setOrder] = useState("asc");

  const onSort = useCallback(
    (id) => {
      const isAsc = orderBy === id && order === "asc";
      setOrder(isAsc ? "desc" : "asc");
      setOrderBy(id);
    },
    [order, orderBy],
  );

  const onSelectAllRows = useCallback((checked, newSelecteds) => {
    setSelected(checked ? newSelecteds : []);
  }, []);

  const onSelectRow = useCallback(
    (inputValue) => {
      setSelected((prev) =>
        prev.includes(inputValue)
          ? prev.filter((v) => v !== inputValue)
          : [...prev, inputValue],
      );
    },
    [],
  );

  const onResetPage = useCallback(() => setPage(0), []);
  const onChangePage = useCallback((_, newPage) => setPage(newPage), []);
  const onChangeRowsPerPage = useCallback((event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  return {
    page,
    order,
    onSort,
    orderBy,
    selected,
    rowsPerPage,
    onSelectRow,
    onResetPage,
    onChangePage,
    onSelectAllRows,
    onChangeRowsPerPage,
  };
}

export { UserView };
