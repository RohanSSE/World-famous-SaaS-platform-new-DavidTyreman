import { SvgColor } from "@admin/components/svg-color";

const icon = (name) => <SvgColor src={`/assets/icons/navbar/${name}.svg`} />;

const navData = [
  {
    title: "Dashboard",
    path: "/admin",
    icon: icon("ic-analytics"),
  },
  {
    title: "User",
    path: "/admin/user",
    icon: icon("ic-user"),
  },
  {
    title: "Cognition",
    path: "/admin/cognition",
    icon: icon("ic-analytics"),
  },
  {
    title: "Review",
    path: "/admin/review",
    icon: icon("ic-blog"),
  },
  {
    title: "AI Ops",
    path: "/admin/ops",
    icon: icon("ic-lock"),
  },
  {
    title: "Questions",
    path: "/admin/questions",
    icon: icon("ic-blog"),
  },
];

export { navData };
