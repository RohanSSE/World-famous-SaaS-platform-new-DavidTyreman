import { useEffect } from "react";
import Drawer from "@mui/material/Drawer";
import { usePathname } from "@admin/routes/hooks";
import { RouterLink } from "@admin/routes/components";

function NavDesktop({ data }) {
  return (
    <aside className="admin-agency-sidebar">
      <NavContent data={data} />
    </aside>
  );
}

function NavMobile({ data, open, onClose }) {
  const pathname = usePathname();
  useEffect(() => {
    if (open) onClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- close drawer on route change only
  }, [pathname]);

  return (
    <Drawer
      open={open}
      onClose={onClose}
      className="admin-mobile-drawer"
      PaperProps={{ className: "admin-mobile-drawer" }}
    >
      <aside className="admin-agency-sidebar" style={{ display: "flex", width: "100%", minWidth: "unset" }}>
        <NavContent data={data} />
      </aside>
    </Drawer>
  );
}

function NavContent({ data }) {
  const pathname = usePathname();

  return (
    <div className="admin-agency-sidebar-inner">
      <div className="admin-agency-sidebar-header">
        <span className="admin-agency-sidebar-label">Menu</span>
        <h3 className="admin-agency-sidebar-title">Admin Panel</h3>
      </div>

      <nav>
        <ul className="admin-agency-sidebar-nav">
          {data.map((item) => {
            const isActive = item.path === pathname;
            return (
              <li key={item.title}>
                <RouterLink
                  href={item.path}
                  className={`admin-agency-sidebar-item ${isActive ? "active" : ""}`}
                >
                  {item.icon}
                  <span>{item.title}</span>
                </RouterLink>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}

export { NavContent, NavDesktop, NavMobile };
