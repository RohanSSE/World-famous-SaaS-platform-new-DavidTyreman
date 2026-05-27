import { CONFIG } from "@admin/config-global";
import { AdminDashboardView } from "@admin/sections/overview/view/admin-dashboard-view";

function Page() {
  return (
    <>
      <title>{`Dashboard - ${CONFIG.appName}`}</title>
      <meta name="description" content="Brand Godfather admin overview" />
      <AdminDashboardView />
    </>
  );
}

export { Page as default };
