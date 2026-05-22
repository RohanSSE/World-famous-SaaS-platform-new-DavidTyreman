import { Link } from "react-router";
function RouterLink({ href, ref, ...other }) {
  return <Link ref={ref} to={href} {...other} />;
}
export {
  RouterLink
};
