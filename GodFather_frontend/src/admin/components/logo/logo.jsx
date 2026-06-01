import { mergeClasses } from "minimal-shared/utils";
import Link from "@mui/material/Link";
import { styled } from "@mui/material/styles";
import { RouterLink } from "@admin/routes/components";
import { logoClasses } from "./classes";
import brandLogo from "../../../assets/mask-group.png";

function Logo({ sx, disabled, className, href = "/admin", ...other }) {
  return (
    <LogoRoot
      component={RouterLink}
      href={href}
      aria-label="The Brand Godfather"
      underline="none"
      className={mergeClasses([logoClasses.root, className])}
      sx={[
        { display: "inline-flex", ...disabled && { pointerEvents: "none" } },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
      {...other}
    >
      <img src={brandLogo} alt="The Brand Godfather" className="admin-chat-logo" />
    </LogoRoot>
  );
}

const LogoRoot = styled(Link)(() => ({
  flexShrink: 0,
  display: "inline-flex",
  verticalAlign: "middle",
}));

export { Logo };
