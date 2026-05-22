import AssistantAvatar from './components/AssistantAvatar.jsx';

// import { Routes, Route, Navigate } from "react-router-dom";
// import IntroductoryPage from "./pages/IntroductoryPage";

// import AgencyDashboard from "./pages/AgencyDashboard";
// import ChatUnlockPopUp from "./pages/ChatUnlockPopUp";
// import UserDashboard from "./pages/UserDashboard";
// import FoundationQuestionScreen from "./pages/FoundationQuestionScreen";
// import ManifestoSecondPage from "./pages/ManifestoPage2";
// import ManifestoPage1 from "./pages/ManifestoPage1";
// import ResetPasswordPage from "./pages/ResetPassword";
// import { ToastContainer } from "react-toastify";
// import PublicRoute from "./context/PublicRoute";
// import ProtectedRoute from "./context/ProtectedRoute";
// import SignupLoginModal from "./pages/SignupLoginModal";
// import ChatKickOffPage from "./pages/ChatKickOffPage";

// function App() {
//   return (
//     <>
//       <Routes>
//         {/* Root redirects to introductory page (home) */}
//         <Route path="/" element={<Navigate to="/intro-ductory" replace />} />

//         {/* Public Routes - Accessible to everyone */}
//         <Route path="/intro-ductory" element={<IntroductoryPage />} />

//         <Route
//           path="/signup"
//           element={
//             <PublicRoute>
//               <SignupLoginModal />
//             </PublicRoute>
//           }
//         />
//         <Route
//           path="/login"
//           element={
//             <PublicRoute>
//               <SignupLoginModal />
//             </PublicRoute>
//           }
//         />

//         {/* Protected Routes - Require authentication */}
//         <Route
//           path="/ChatKickoffPage"
//           element={
//             <ProtectedRoute>
//               <ChatKickOffPage/>
//             </ProtectedRoute>
//           }
//         />
//         {/* <Route
//           path="/chat-interface"
//           element={
//             <ProtectedRoute>
//               <ChatInterfacePage />
//             </ProtectedRoute>
//           }
//         /> */}
//         <Route
//           path="/agency-dashboard"
//           element={
//             <ProtectedRoute>
//               <AgencyDashboard />
//             </ProtectedRoute>
//           }
//         />
//         <Route
//           path="/user-dashboard"
//           element={
//             <ProtectedRoute>
//               <UserDashboard />
//             </ProtectedRoute>
//           }
//         />
//         <Route
//           path="/chat-unlock"
//           element={
//             <ProtectedRoute>
//               <ChatUnlockPopUp />
//             </ProtectedRoute>
//           }
//         />

//         <Route
//           path="/foundation-questions"
//           element={
//             <ProtectedRoute>
//               <FoundationQuestionScreen />
//             </ProtectedRoute>
//           }
//         />

//         <Route
//           path="/manifesto"
//           element={
//             <ProtectedRoute>
//               <ManifestoSecondPage/>
//             </ProtectedRoute>
//           }
//         />

//          <Route
//           path="/manifestoFirstPage"
//           element={
//             <ProtectedRoute>
//               <ManifestoPage1 />
//             </ProtectedRoute>
//           }
//         />

//        <Route
//   path="/reset-password/:uid/:token/"
//   element={<ResetPasswordPage />}
// />

//         {/* Catch all - redirect to home */}
//         <Route path="*" element={<Navigate to="/intro-ductory" replace />} />
//       </Routes>

//       <ToastContainer
//         position="top-center"
//         autoClose={3000}
//         hideProgressBar={false}
//         newestOnTop={false}
//         closeOnClick
//         rtl={false}
//         pauseOnFocusLoss
//         draggable
//         pauseOnHover
//         theme="dark"
//       />
//     </>
//   );
// }

// export default App;

import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import AdminRoot from "./admin/AdminRoot";
import {
  AdminSignInRoute,
  AdminDashboardLayout,
  AdminDashboardPage,
  AdminUserPage,
} from "./admin/admin-routes";
import IntroductoryPage from "./pages/IntroductoryPage";

import AgencyDashboard from "./pages/AgencyDashboard";
import ChatUnlockPopUp from "./pages/ChatUnlockPopUp";
import UserDashboard from "./pages/UserDashboard";
import FoundationQuestionScreen from "./pages/FoundationQuestionScreen";
import ManifestoPage from "./pages/ManifestoPage";
import ManifestoPage1 from "./pages/ManifestoPage1";
import ResetPasswordPage from "./pages/ResetPassword";
import { ToastContainer } from "react-toastify";
import PublicRoute from "./context/PublicRoute";
import ProtectedRoute from "./context/ProtectedRoute";
import SignupLoginModal from "./pages/SignupLoginModal";
import ChatKickOffPage from "./pages/ChatKickOffPage";
import BrandSummaryPage from "./pages/BrandSummaryPage";
import Stepper from "./pages/Stepper";
import DeepDivePage from "./pages/Deepdivepage";
// import IdentityCompleteModal from "./pages/IdentityCompleteModal";

function AppContent() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");

  return (
    <>
      <Routes>
        {/* Root redirects to introductory page (home) */}
        <Route path="/" element={<Navigate to="/intro-ductory" replace />} />

        {/* Public Routes - Accessible to everyone */}
        <Route path="/intro-ductory" element={<IntroductoryPage />} />

        <Route
          path="/signup"
          element={
            <PublicRoute>
              <SignupLoginModal />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <SignupLoginModal />
            </PublicRoute>
          }
        />

        {/* Protected Routes - Require authentication */}
        <Route
          path="/ChatKickoffPage"
          element={
            <ProtectedRoute>
              <ChatKickOffPage />
            </ProtectedRoute>
          }
        />

        {/* ── NEW: Deep Dive (Stage 4 optional questions) ── */}
        <Route
          path="/DeepDivePage"
          element={
            <ProtectedRoute>
              <DeepDivePage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/brand-summary"
          element={
            <ProtectedRoute>
              <BrandSummaryPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/stepper"
          element={
            <ProtectedRoute>
              <Stepper />
            </ProtectedRoute>
          }
        />

        {/* <Route 
          path="/chat-interface" 
          element={
            <ProtectedRoute>
              <ChatInterfacePage />
            </ProtectedRoute>
          } 
        /> */}
        <Route
          path="/agency-dashboard"
          element={
            <ProtectedRoute>
              <AgencyDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/user-dashboard"
          element={
            <ProtectedRoute>
              <UserDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat-unlock"
          element={
            <ProtectedRoute>
              <ChatUnlockPopUp />
            </ProtectedRoute>
          }
        />

        <Route
          path="/foundation-questions"
          element={
            <ProtectedRoute>
              <FoundationQuestionScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/manifesto"
          element={
            <ProtectedRoute>
              <ManifestoPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/manifestoFirstPage"
          element={
            <ProtectedRoute>
              <ManifestoPage1 />
            </ProtectedRoute>
          }
        />

        <Route
          path="/reset-password/:uid/:token/"
          element={<ResetPasswordPage />}
        />

        {/* Admin panel — nested routes (relative paths under /admin) */}
        <Route path="/admin" element={<AdminRoot />}>
          <Route path="sign-in" element={<AdminSignInRoute />} />
          <Route element={<AdminDashboardLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="user" element={<AdminUserPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/admin/sign-in" replace />} />
        </Route>

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/intro-ductory" replace />} />
      </Routes>

      <ToastContainer
        position="top-center"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
      {/* Hide main-app assistant on admin routes */}
      {!isAdminRoute && <AssistantAvatar />}
    </>
  );
}

function App() {
  return <AppContent />;
}

export default App;
