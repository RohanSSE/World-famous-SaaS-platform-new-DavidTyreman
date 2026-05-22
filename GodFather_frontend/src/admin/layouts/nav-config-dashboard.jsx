import { SvgColor } from "@admin/components/svg-color";
const icon = (name) => <SvgColor src={`/assets/icons/navbar/${name}.svg`} />;
const navData = [
  {
    title: "Dashboard",
    path: "/admin",
    icon: icon("ic-analytics")
  },
  {
    title: "User",
    path: "/admin/user",
    icon: icon("ic-user")
  },
  {
    title: "Welcome Super Admin",
    path: "/admin/sign-in",
    icon: icon("ic-lock")
  },
  {
    title: "Not found",
    path: "/404",
    icon: icon("ic-disabled")
  }
];
export {
  navData
};
