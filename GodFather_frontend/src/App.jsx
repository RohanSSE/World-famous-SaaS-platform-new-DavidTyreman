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
  AdminCognitionPage,
  AdminReviewPage,
  AdminOpsPage,
  AdminQuestionsPage,
  AdminTrainBgfPage,
  AdminDevPage,
  AdminSubscriptionPage,
} from "./admin/admin-routes";
import IntroductoryPage from "./pages/IntroductoryPage";

import AgencyDashboard from "./pages/AgencyDashboard";
import ChatUnlockPopUp from "./pages/ChatUnlockPopUp";
import UserDashboard from "./pages/UserDashboard";
import ManifestoPage from "./pages/ManifestoPage";
import ManifestoPage1 from "./pages/ManifestoPage1";
import ResetPasswordPage from "./pages/ResetPassword";
import { ToastContainer } from "react-toastify";
import PublicRoute from "./context/PublicRoute";
import ProtectedRoute from "./context/ProtectedRoute";
import SignupLoginModal from "./pages/SignupLoginModal";
import ChatKickOffPage from "./pages/ChatKickOffPage";
import BrandSummaryPage from "./pages/BrandSummaryPage";
import BrandBookReadyPage from "./pages/BrandBookReadyPage";
import Stepper from "./pages/Stepper";
import DeepDivePage from "./pages/Deepdivepage";
import BrandOperatingSystem from "./pages/BrandOperatingSystem";
import BrandOnboarding from "./pages/BrandOnboarding";
import OutputModePage from "./pages/OutputModePage";
import OutputChatPage from "./pages/OutputChatPage";
import WelcomePage from "./pages/WelcomePage";
import AgencyPendingPage from "./pages/AgencyPendingPage";
import BrandIntroPage from "./pages/BrandIntroPage";
import BeforeContinuePage from "./pages/BeforeContinuePage";
import JourneyPhasesPage from "./pages/JourneyPhasesPage";
import PhaseIntroPage from "./pages/PhaseIntroPage";
import PhaseQuestionPage from "./pages/PhaseQuestionPage";
import PhaseCompletePage from "./pages/PhaseCompletePage";
// import IdentityCompleteModal from "./pages/IdentityCompleteModal";

function AppContent() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");
  const hideAssistant = [
    "/welcome",
    "/brand-intro",
    "/before-continue",
    "/journey-phases",
    "/brand-summary",
    "/user-dashboard",
  ].includes(location.pathname) ||
    location.pathname.startsWith("/phase-intro") ||
    location.pathname.startsWith("/phase-questions") ||
    location.pathname.startsWith("/phase-complete");

  return (
    <>
      <Routes>
        {/* Root redirects to introductory page (home) */}
        <Route path="/" element={<Navigate to="/intro-ductory" replace />} />

        {/* Public Routes - Accessible to everyone */}
        <Route path="/intro-ductory" element={<IntroductoryPage />} />
        <Route path="/agency-pending" element={<AgencyPendingPage />} />

        <Route
          path="/signup"
          element={
            <PublicRoute>
              <SignupLoginModal isOpen onClose={() => {}} initialMode="signup" />
            </PublicRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <SignupLoginModal isOpen onClose={() => {}} initialMode="login" />
            </PublicRoute>
          }
        />

        {/* Protected Routes - Require authentication */}
        <Route
          path="/welcome"
          element={
            <ProtectedRoute>
              <WelcomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/brand-intro"
          element={
            <ProtectedRoute>
              <BrandIntroPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/before-continue"
          element={
            <ProtectedRoute>
              <BeforeContinuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/journey-phases"
          element={
            <ProtectedRoute>
              <JourneyPhasesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/phase-intro/:phaseId"
          element={
            <ProtectedRoute>
              <PhaseIntroPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/phase-questions/:phaseId"
          element={
            <ProtectedRoute>
              <PhaseQuestionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/phase-complete/:phaseId"
          element={
            <ProtectedRoute>
              <PhaseCompletePage />
            </ProtectedRoute>
          }
        />
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
          path="/brand-book-ready"
          element={
            <ProtectedRoute>
              <BrandBookReadyPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/output-mode"
          element={
            <ProtectedRoute>
              <OutputModePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/output-chat"
          element={
            <ProtectedRoute>
              <OutputChatPage />
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
          path="/brand-os"
          element={
            <ProtectedRoute>
              <BrandOperatingSystem />
            </ProtectedRoute>
          }
        />
        <Route
          path="/brand-onboarding"
          element={
            <ProtectedRoute>
              <BrandOnboarding />
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
          element={<Navigate to="/phase-questions/1" replace />}
        />
        <Route
          path="/foundation-questions/*"
          element={<Navigate to="/phase-questions/1" replace />}
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
            <Route path="cognition" element={<AdminCognitionPage />} />
            <Route path="review" element={<AdminReviewPage />} />
            <Route path="ops" element={<AdminOpsPage />} />
            <Route path="subscription" element={<AdminSubscriptionPage />} />
            <Route path="questions" element={<AdminQuestionsPage />} />
            <Route path="train-bgf" element={<AdminTrainBgfPage />} />
            <Route path="dev" element={<AdminDevPage />} />
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
      {!isAdminRoute && !hideAssistant && <AssistantAvatar />}
    </>
  );
}

function App() {
  return <AppContent />;
}

export default App;
