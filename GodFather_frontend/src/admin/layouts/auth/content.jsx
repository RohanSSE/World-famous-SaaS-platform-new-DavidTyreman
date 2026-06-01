import { mergeClasses } from "minimal-shared/utils";
import Box from "@mui/material/Box";
import { layoutClasses } from "../core/classes";

function AuthContent({ sx, children, className, ...other }) {
  return (
    <Box
      className={mergeClasses([layoutClasses.content, className])}
      sx={[
        {
          py: 5,
          px: 3,
          width: 1,
          zIndex: 2,
          borderRadius: 2,
          display: "flex",
          flexDirection: "column",
          maxWidth: "var(--layout-auth-content-width)",
          bgcolor: "rgba(26, 28, 58, 0.65)",
          border: "1.5px solid #5B6798",
          boxShadow: "0 12px 40px rgba(0, 0, 0, 0.45)",
          backdropFilter: "blur(16px)",
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
      {...other}
    >
      {children}
    </Box>
  );
}

export { AuthContent };
