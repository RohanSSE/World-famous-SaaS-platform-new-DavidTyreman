import { lazy, Suspense } from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import Box from '@mui/material/Box';
import LinearProgress, { linearProgressClasses } from '@mui/material/LinearProgress';

import { isAuthenticated } from '@admin/auth/session';
import { AuthLayout } from '@admin/layouts/auth';
import { DashboardLayout } from '@admin/layouts/dashboard';

const DashboardPage = lazy(() => import('@admin/pages/dashboard'));
const UserPage = lazy(() => import('@admin/pages/user'));
const CognitionPage = lazy(() => import('@admin/pages/cognition'));
const ReviewPage = lazy(() => import('@admin/pages/review'));
const OpsPage = lazy(() => import('@admin/pages/ops'));
const QuestionsPage = lazy(() => import('@admin/pages/questions'));
const SignInPage = lazy(() => import('@admin/pages/sign-in'));

const ADMIN_SIGN_IN = '/admin/sign-in';
const ADMIN_HOME = '/admin';

function Loading() {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        width: 1,
      }}
    >
      <LinearProgress
        sx={{
          width: 1,
          maxWidth: 320,
          [`& .${linearProgressClasses.bar}`]: { bgcolor: 'primary.main' },
        }}
      />
    </Box>
  );
}

export function AdminGuestOnly({ children }) {
  if (isAuthenticated()) {
    return <Navigate to={ADMIN_HOME} replace />;
  }
  return children;
}

export function AdminAuthOnly({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to={ADMIN_SIGN_IN} replace />;
  }
  return children;
}

export function AdminSignInRoute() {
  return (
    <AdminGuestOnly>
      <AuthLayout>
        <Suspense fallback={<Loading />}>
          <SignInPage />
        </Suspense>
      </AuthLayout>
    </AdminGuestOnly>
  );
}

export function AdminDashboardLayout() {
  return (
    <AdminAuthOnly>
      <DashboardLayout>
        <Suspense fallback={<Loading />}>
          <Outlet />
        </Suspense>
      </DashboardLayout>
    </AdminAuthOnly>
  );
}

export function AdminDashboardPage() {
  return <DashboardPage />;
}

export function AdminUserPage() {
  return <UserPage />;
}

export function AdminCognitionPage() {
  return <CognitionPage />;
}

export function AdminReviewPage() {
  return <ReviewPage />;
}

export function AdminOpsPage() {
  return <OpsPage />;
}

export function AdminQuestionsPage() {
  return <QuestionsPage />;
}
