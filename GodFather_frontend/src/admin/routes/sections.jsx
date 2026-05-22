import { lazy, Suspense } from "react";
import { varAlpha } from "minimal-shared/utils";
import { Navigate, Outlet } from "react-router-dom";
import Box from "@mui/material/Box";
import LinearProgress, { linearProgressClasses } from "@mui/material/LinearProgress";
import { AuthLayout } from "@admin/layouts/auth";
import { DashboardLayout } from "@admin/layouts/dashboard";
import { isAuthenticated } from "@admin/auth/session";
const DashboardPage = lazy(() => import("@admin/pages/dashboard"));
const UserPage = lazy(() => import("@admin/pages/user"));
const SignInPage = lazy(() => import("@admin/pages/sign-in"));
const renderFallback = () => <Box
  sx={{
    display: "flex",
    flex: "1 1 auto",
    alignItems: "center",
    justifyContent: "center"
  }}
>
    <LinearProgress
  sx={{
    width: 1,
    maxWidth: 320,
    bgcolor: (theme) => varAlpha(theme.vars.palette.text.primaryChannel, 0.16),
    [`& .${linearProgressClasses.bar}`]: { bgcolor: "text.primary" }
  }}
/>
  </Box>;
function AuthenticatedOnly({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/sign-in" replace />;
  }
  return <>{children}</>;
}
function GuestOnly({ children }) {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
const routesSection = [
  {
    element: <AuthenticatedOnly>
        <DashboardLayout>
          <Suspense fallback={renderFallback()}>
            <Outlet />
          </Suspense>
        </DashboardLayout>
      </AuthenticatedOnly>,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "user", element: <UserPage /> }
    ]
  },
  {
    path: "sign-in",
    element: <GuestOnly>
        <AuthLayout>
          <SignInPage />
        </AuthLayout>
      </GuestOnly>
  }
];
export {
  DashboardPage,
  SignInPage,
  UserPage,
  routesSection
};
