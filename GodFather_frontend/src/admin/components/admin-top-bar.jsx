import { useNavigate } from "react-router-dom";
import { useState, useCallback } from "react";
import Popover from "@mui/material/Popover";
import MenuList from "@mui/material/MenuList";
import MenuItem from "@mui/material/MenuItem";
import Divider from "@mui/material/Divider";
import { Iconify } from "@admin/components/iconify";
import { clearAuthSession, getAuthSession } from "@admin/auth/session";
import { useAuth } from "../../context/AuthProvider";
import brandLogo from "../../assets/mask-group.png";

function AdminTopBar({ onMenuClick }) {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const session = getAuthSession();
  const [anchor, setAnchor] = useState(null);

  const initials =
    session?.name?.charAt(0)?.toUpperCase() ||
    session?.email?.charAt(0)?.toUpperCase() ||
    "A";

  const handleLogout = useCallback(async () => {
    setAnchor(null);
    try {
      await logout();
    } catch {
      /* ignore */
    }
    clearAuthSession();
    navigate("/intro-ductory", { replace: true });
  }, [logout, navigate]);

  return (
    <header className="admin-chat-header">
      <div className="admin-chat-header-left">
        <button type="button" className="admin-menu-btn" onClick={onMenuClick} aria-label="Menu">
          <Iconify icon="solar:hamburger-menu-bold" width={22} />
        </button>
        <div
          className="admin-chat-logo-wrap"
          onClick={() => navigate("/admin")}
          onKeyDown={(e) => e.key === "Enter" && navigate("/admin")}
          role="button"
          tabIndex={0}
        >
          <img src={brandLogo} alt="The Brand Godfather" className="admin-chat-logo" />
        </div>
      </div>

      <div className="admin-chat-header-actions">
        <button
          type="button"
          className="admin-avatar-top"
          onClick={(e) => setAnchor(e.currentTarget)}
          aria-label="Account menu"
        >
          {initials}
        </button>
        <Popover
          open={!!anchor}
          anchorEl={anchor}
          onClose={() => setAnchor(null)}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
          slotProps={{
            paper: {
              sx: {
                mt: 1,
                minWidth: 180,
                bgcolor: "#12132d",
                border: "1px solid rgba(142, 229, 255, 0.12)",
                backgroundImage: "none",
              },
            },
          }}
        >
          <MenuList sx={{ py: 1 }}>
            <MenuItem disabled sx={{ opacity: 1, color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
              {session?.email || "Admin"}
            </MenuItem>
            <Divider sx={{ borderColor: "rgba(142, 229, 255, 0.08)" }} />
            <MenuItem onClick={handleLogout} sx={{ color: "#ff8a80" }}>
              Log out
            </MenuItem>
          </MenuList>
        </Popover>
      </div>
    </header>
  );
}

export { AdminTopBar };
