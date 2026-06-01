import { useState, useCallback, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Table from "@mui/material/Table";
import Alert from "@mui/material/Alert";
import TableRow from "@mui/material/TableRow";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import Typography from "@mui/material/Typography";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import CircularProgress from "@mui/material/CircularProgress";
import TableContainer from "@mui/material/TableContainer";
import adminApi from "@admin/lib/adminApi";
import { Label } from "@admin/components/label";
import { Iconify } from "@admin/components/iconify";
import { UserTableHead } from "../user-table-head";
import { TableNoData } from "../table-no-data";
import { UserTableToolbar } from "../user-table-toolbar";
import {
  mapApiUser,
  mapApiAgency,
  getMembersForAgency,
} from "../directory-mappers";

const MEMBER_COLS = [
  { id: "name", label: "Email", width: "40%" },
  { id: "role", label: "Role", width: "20%" },
  { id: "phone", label: "Phone", width: "20%" },
  { id: "status", label: "Status", width: "20%" },
];

function MembersView() {
  const [searchParams] = useSearchParams();
  const agencyFilterId = searchParams.get("agency");
  const [filterName, setFilterName] = useState("");
  const [users, setUsers] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedAgency, setExpandedAgency] = useState(
    agencyFilterId ? `agency-${agencyFilterId}` : false,
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [usersData, agenciesData] = await Promise.all([
        adminApi.listUsers(),
        adminApi.listAgencies(),
      ]);
      const userList = Array.isArray(usersData) ? usersData : usersData?.results || [];
      const agencyList = Array.isArray(agenciesData) ? agenciesData : agenciesData?.results || [];
      setUsers(userList.map(mapApiUser));
      setAgencies(agencyList.map(mapApiAgency));
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Failed to load members.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (agencyFilterId) {
      setExpandedAgency(`agency-${agencyFilterId}`);
    }
  }, [agencyFilterId]);

  const sections = useMemo(() => {
    let list = agencies;
    if (agencyFilterId) {
      list = list.filter((a) => String(a.id) === String(agencyFilterId));
    }
    const q = filterName.trim().toLowerCase();
    return list
      .map((agency) => {
        const members = getMembersForAgency(agency, users);
        const haystack = `${agency.name} ${agency.owner_email} ${members.map((m) => m.name).join(" ")}`.toLowerCase();
        if (q && !haystack.includes(q)) return null;
        return { agency, members };
      })
      .filter(Boolean);
  }, [agencies, users, filterName, agencyFilterId]);

  const totalMembers = useMemo(
    () => sections.reduce((n, s) => n + s.members.length, 0),
    [sections],
  );

  return (
    <>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" className="adb-page-title" sx={{ mb: 0.5 }}>
          Members
        </Typography>
        <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.55)" }}>
          Team members under each agency ({totalMembers} client member{totalMembers !== 1 ? "s" : ""}{" "}
          across {sections.length} agenc{sections.length !== 1 ? "ies" : "y"}). Owners are shown in each
          section header — approve agencies from Users → Agency tab.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 2 }}>
        <UserTableToolbar
          numSelected={0}
          filterName={filterName}
          searchPlaceholder="Search by agency, owner, or member email..."
          onFilterName={(e) => setFilterName(e.target.value)}
        />
      </Card>

      {loading ? (
        <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
          <CircularProgress />
        </Box>
      ) : sections.length === 0 ? (
        <Card sx={{ p: 4 }}>
          <TableNoData searchQuery={filterName || (agencyFilterId ? "this agency" : "")} />
        </Card>
      ) : (
        sections.map(({ agency, members }) => (
          <Accordion
            key={agency.id}
            expanded={expandedAgency === `agency-${agency.id}`}
            onChange={(_, isExpanded) =>
              setExpandedAgency(isExpanded ? `agency-${agency.id}` : false)
            }
            sx={{
              mb: 1.5,
              bgcolor: "rgba(15, 18, 40, 0.6)",
              border: "1px solid rgba(142, 229, 255, 0.1)",
              "&:before": { display: "none" },
            }}
          >
            <AccordionSummary
              expandIcon={<Iconify icon="eva:arrow-ios-downward-fill" width={20} sx={{ color: "#86e3ff" }} />}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap", width: "100%", pr: 2 }}>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle1" sx={{ color: "#fff", fontWeight: 600 }}>
                    {agency.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.5)" }}>
                    Owner: {agency.owner_email || "—"}
                  </Typography>
                </Box>
                <Label color={agency.status === "active" ? "success" : "warning"}>
                  {agency.status === "pending" ? "Pending" : agency.status}
                </Label>
                <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.45)" }}>
                  {members.length} member{members.length !== 1 ? "s" : ""}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails sx={{ pt: 0 }}>
              <TableContainer>
                <Table size="small" className="admin-users-table">
                  <UserTableHead
                    order="asc"
                    orderBy="name"
                    rowCount={members.length}
                    numSelected={0}
                    onSort={() => {}}
                    onSelectAllRows={() => {}}
                    headLabel={MEMBER_COLS}
                    hideCheckbox
                  />
                  <TableBody>
                    {members.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} sx={{ color: "rgba(255,255,255,0.5)", py: 3 }}>
                          No team members added yet. Client users linked to this agency will appear here.
                        </TableCell>
                      </TableRow>
                    ) : (
                      members.map((m) => (
                        <TableRow key={m.id} className="admin-users-table-row">
                          <TableCell sx={{ color: "#fff" }}>{m.name}</TableCell>
                          <TableCell>{m.role}</TableCell>
                          <TableCell>{m.phone || "—"}</TableCell>
                          <TableCell>
                            <Label color={m.status === "active" ? "success" : "warning"}>
                              {m.status === "pending" ? "Pending" : m.status}
                            </Label>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        ))
      )}
    </>
  );
}

export { MembersView };
