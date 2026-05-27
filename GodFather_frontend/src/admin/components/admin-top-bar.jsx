import { useNavigate } from "react-router-dom";
import { useState, useCallback, useRef, useEffect } from "react";
import Popover from "@mui/material/Popover";
import MenuList from "@mui/material/MenuList";
import MenuItem from "@mui/material/MenuItem";
import Divider from "@mui/material/Divider";
import { Iconify } from "@admin/components/iconify";
import { clearAuthSession, getAuthSession } from "@admin/auth/session";
import authService from "../../services/authService";
import brandLogo from "../../assets/mask-group.png";

function AdminTopBar({ onMenuClick }) {
  const navigate = useNavigate();
  const session = getAuthSession();
  const [anchor, setAnchor] = useState(null);
  const ref = useRef(null);

  const initials =
    session?.name?.charAt(0)?.toUpperCase() ||
    session?.email?.charAt(0)?.toUpperCase() ||
    "A";

  const handleLogout = useCallback(async () => {
    setAnchor(null);
    try {
      await authService.logout();
    } catch {
      /* ignore */
    }
    clearAuthSession();
    navigate("/admin/sign-in", { replace: true });
  }, [navigate]);

  useEffect(() => {
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setAnchor(null);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

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

      <div className="admin-chat-header-actions" ref={ref}>
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
