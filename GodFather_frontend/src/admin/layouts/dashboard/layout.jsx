import { useBoolean } from "minimal-shared/hooks";
import { AdminTopBar } from "@admin/components/admin-top-bar";
import { NavMobile, NavDesktop } from "./nav";
import { navData } from "../nav-config-dashboard";

function DashboardLayout({ children }) {
  const { value: open, onFalse: onClose, onTrue: onOpen } = useBoolean();

  return (
    <div className="admin-adb-root">
      <AdminTopBar onMenuClick={onOpen} />

      <div className="adb-background" aria-hidden>
        <div className="adb-glow-left" />
        <div className="adb-glow-right" />
      </div>

      <div className="admin-adb-layout">
        <NavDesktop data={navData} />
        <NavMobile data={navData} open={open} onClose={onClose} />

        <main className="adb-main-content admin-adb-main">{children}</main>
      </div>
    </div>
  );
}

export { DashboardLayout };
