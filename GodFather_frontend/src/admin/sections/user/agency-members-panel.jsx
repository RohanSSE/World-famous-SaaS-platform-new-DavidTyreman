import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Divider from "@mui/material/Divider";
import Chip from "@mui/material/Chip";
import { Label } from "@admin/components/label";
import { Iconify } from "@admin/components/iconify";

function AgencyMembersPanel({ agency, members, onClose }) {
  if (!agency) return null;

  return (
    <Box className="admin-agency-members-panel">
      <Box className="admin-agency-members-panel-header">
        <Iconify icon="solar:users-group-rounded-bold" width={28} sx={{ color: "#86e3ff", mt: 0.25 }} />
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography variant="overline" sx={{ color: "rgba(255,255,255,0.5)", display: "block", lineHeight: 1.2 }}>
            Members
          </Typography>
          <Typography variant="subtitle1" sx={{ color: "#fff", fontWeight: 600 }} noWrap title={agency.name}>
            {agency.name}
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: "rgba(255,255,255,0.7)" }} aria-label="Close panel">
          <Iconify icon="mingcute:close-line" width={20} />
        </IconButton>
      </Box>

      <Box sx={{ px: 2, pb: 1.5 }}>
        <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.55)", display: "block" }}>
          Owner
        </Typography>
        <Typography variant="body2" sx={{ color: "#fff", fontSize: 13 }} noWrap>
          {agency.owner_email || "—"}
        </Typography>
        <Chip
          size="small"
          label={`${members.length} member${members.length !== 1 ? "s" : ""}`}
          sx={{ mt: 1, height: 22, fontSize: 11, bgcolor: "rgba(57, 89, 229, 0.2)", color: "#86e3ff" }}
        />
      </Box>

      <Divider sx={{ borderColor: "rgba(142, 229, 255, 0.1)" }} />

      <List dense disablePadding sx={{ overflowY: "auto", flex: 1, px: 1, py: 1 }}>
        {members.length === 0 ? (
          <ListItem>
            <ListItemText
              primary="No members yet"
              secondary="Users appear here when linked to this agency"
              primaryTypographyProps={{ color: "rgba(255,255,255,0.65)", fontSize: 13 }}
              secondaryTypographyProps={{ color: "rgba(255,255,255,0.4)", fontSize: 11 }}
            />
          </ListItem>
        ) : (
          members.map((m) => (
            <ListItem
              key={m.id}
              sx={{
                mb: 0.5,
                borderRadius: 1,
                bgcolor: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(142, 229, 255, 0.06)",
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, flexWrap: "wrap" }}>
                    <Typography variant="body2" sx={{ color: "#fff", fontSize: 13 }} noWrap>
                      {m.name}
                    </Typography>
                    {m.isOwner && (
                      <Label color="info" sx={{ height: 18, fontSize: 10 }}>
                        Owner
                      </Label>
                    )}
                  </Box>
                }
                secondary={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                    <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.5)" }}>
                      {m.role}
                    </Typography>
                    <Label color={m.status === "active" ? "success" : "warning"} sx={{ height: 18, fontSize: 10 }}>
                      {m.status === "pending" ? "Pending" : m.status}
                    </Label>
                  </Box>
                }
              />
            </ListItem>
          ))
        )}
      </List>
    </Box>
  );
}

export { AgencyMembersPanel };
