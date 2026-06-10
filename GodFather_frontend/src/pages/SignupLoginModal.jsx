import React, { useState, useEffect } from "react";
import "../components/Signup.css";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthProvider";
import { toast } from "react-toastify";
import { Eye, EyeOff } from "lucide-react";
import mailIcon from "../svg_assets/Email.svg";
import lockIcon from "../svg_assets/Password.svg";
import googleIcon from "../svg_assets/Google.svg";
import appleIcon from "../svg_assets/Apple.svg";
import signupImg from "../assets/signup-bg.png";
import authService from "../services/authService";
import ForgotPasswordModal from "./ForgotPasswordModal";
import { clearAdminAuthSession, isAdminUser, saveAuthSession } from "@admin/auth/session";

const SignupLoginModal = ({ isOpen, onClose, initialMode = "signup" }) => {
  const [showForgotForm, setShowForgotForm] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);

  const navigate = useNavigate();
  const { login, signup, auth } = useAuth();

  const [isLogin, setIsLogin] = useState(initialMode === "login");
  const [userType, setUserType] = useState(""); // "user" or "agency"
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsLogin(initialMode === "login");
      setUserType("");
      setFormData({ email: "", password: "", confirmPassword: "" });
      setError("");
      setSuccessMessage("");
      setShowPassword(false);
      setShowConfirmPassword(false);
    }
  }, [initialMode, isOpen]);

  useEffect(() => {
    setShowPassword(false);
    setShowConfirmPassword(false);
  }, [isLogin]);

  if (!isOpen) return null;

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError("");
  };

  const isFormDisabled = !isLogin && !userType;

  const validateForm = () => {
    if (!isLogin && !userType) {
      setError("Please select a user type first");
      return false;
    }
    if (!formData.email || !formData.password) {
      setError("Email and password are required");
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }

    if (!isLogin && formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    return true;
  };

  // Post-login: Welcome first, then stepper journey (old: direct /stepper or /user-dashboard)
  const getRedirectRoute = async (userData) => {
    if (isAdminUser(userData)) return "/admin";
    const roleName = userData?.role_name;
    if (roleName === "agency") {
      try {
        const redirect = await authService.getAgencyOnboardingRedirect();
        return redirect.route;
      } catch {
        return "/welcome";
      }
    }
    if (roleName === "client") {
      if (typeof localStorage !== "undefined" && localStorage.getItem("sessionId")) {
        return "/phase-questions/1";
      }
      return "/welcome";
    }
    const roleId = userData?.role;
    if (roleId === 3) {
      try {
        const redirect = await authService.getAgencyOnboardingRedirect();
        return redirect.route;
      } catch {
        return "/welcome";
      }
    }
    // if (roleId === 2) return "/stepper";
    // return "/user-dashboard";
    return "/welcome";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");
    if (!validateForm()) {
      return;
    }
    setLoading(true);
    try {
      if (isLogin) {
        try {
          // Attempt to log in
          const result = await login(formData.email, formData.password);
          const profile = await authService.getProfile();
          const userData = profile || result.user || auth.user;
          const roleName = (profile || result.user)?.role_name;
          if (
            roleName === "agency" &&
            profile?.is_active === false
          ) {
            await authService.logout();
            onClose();
            navigate("/agency-pending", {
              state: { email: formData.email },
            });
            return;
          }
          if (isAdminUser(userData)) {
            saveAuthSession({
              email: formData.email.trim().toLowerCase(),
              name: userData.email || "Admin User",
              mode: "normal-login",
              role: userData.role_name,
              is_staff: userData.is_staff,
              is_superuser: userData.is_superuser,
              loggedInAt: new Date().toISOString(),
            });
          } else {
            clearAdminAuthSession();
          }
          const redirectRoute = await getRedirectRoute(userData);
          setSuccessMessage("Login successful! Redirecting...");
          setTimeout(() => {
            onClose();
            navigate(redirectRoute);
          }, 500);
        } catch (err) {
          console.error("Login error:", err);
          const isPending =
            err.code === "agency_pending_approval" ||
            err.status === 403 ||
            String(err.detail || err.message || "")
              .toLowerCase()
              .includes("pending");
          if (isPending) {
            onClose();
            navigate("/agency-pending", {
              state: {
                email: formData.email,
                message: err.detail || err.message,
              },
            });
            return;
          }
          setError(
            err.message ||
              err.error ||
              err.detail ||
              "Login failed. Please check your credentials."
          );
        }
      } else {
        try {
          // Attempt to sign up (don't auto-login, switch to login form)
          const result = await signup(
            formData.email,
            formData.password,
            formData.confirmPassword,
            userType
          );
          setSuccessMessage(
            result?.message ||
              (userType === "agency"
                ? "Agency registered. An admin must activate your account before you can sign in."
                : "Account created successfully! Please log in."),
          );
          // Clear form and switch to login mode after a short delay
          setTimeout(() => {
            setFormData({ email: "", password: "", confirmPassword: "" });
            setUserType("");
            setIsLogin(true);
            setSuccessMessage("Account created! Please log in with your credentials.");
          }, 1500);
        } catch (err) {
          console.error("Signup error:", err);
          if (err.email) {
            setError(`Email: ${err.email[0]}`);
          } else if (err.password) {
            setError(`Password: ${err.password[0]}`);
          } else if (err.confirm_password) {
            setError(`Confirm Password: ${err.confirm_password[0]}`);
          } else if (err.non_field_errors) {
            setError(err.non_field_errors[0]);
          } else {
            setError(
              err.message ||
                err.error ||
                err.detail ||
                "Signup failed. Please try again."
            );
          }
        }
      }
    } catch (err) {
      console.error("Unexpected error:", err);
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      console.log("Google login initiated");
      setError("Google login not yet implemented");
    } catch (err) {
      setError("Google login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAppleLogin = async () => {
    try {
      setLoading(true);
      console.log("Apple login initiated");
      setError("Apple login not yet implemented");
    } catch (err) {
      setError("Apple login failed");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setUserType("");
    setFormData({ email: "", password: "", confirmPassword: "" });
    setError("");
    setSuccessMessage("");
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      setError("Enter your email to reset your password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await authService.requestPasswordReset(resetEmail);
      setSuccessMessage("Password reset email sent! Please check your inbox.");
      setShowForgotForm(false);
    } catch (err) {
      setError(
        err?.email?.[0] ||
          err?.detail ||
          err?.message ||
          "Failed to send password reset email."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Left Side - Form */}
        <div className="modal-left">
          <div className="modal-form-container">
            <h2 className="modal-heading">
              {isLogin ? (
                <>
                  Log in to your account{" "}
                  <span className="heading-light">
                    or{" "}
                    <button className="mode-toggle-btn" onClick={toggleMode}>
                      Sign up
                    </button>
                  </span>
                </>
              ) : (
                <>
                  New to this platform? <span>Sign up</span>
                  <span className="heading-light">
                    {" "}
                    or{" "}
                    <button className="mode-toggle-btn" onClick={toggleMode}>
                      Log in
                    </button>
                  </span>
                </>
              )}
            </h2>

            {error && <div className="message-error">{error}</div>}
            {successMessage && (
              <div className="message-success">{successMessage}</div>
            )}

            {/* User Type Selector — only on signup */}
            {!isLogin && (
              <div className="user-type-selector">
                <label className="user-type-label">I am a</label>
                <div className="user-type-options">
                  <button
                    type="button"
                    className={`user-type-btn ${userType === "user" ? "active" : ""}`}
                    onClick={() => { setUserType("user"); setError(""); }}
                  >
                    <span className="user-type-icon">👤</span>
                    User / Client
                  </button>
                  <button
                    type="button"
                    className={`user-type-btn ${userType === "agency" ? "active" : ""}`}
                    onClick={() => { setUserType("agency"); setError(""); }}
                  >
                    <span className="user-type-icon">🏢</span>
                    Agency
                  </button>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className={isFormDisabled ? "form-disabled" : ""}>
              <div className="input-group">
                <img src={mailIcon} alt="email" />
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleInputChange}
                  disabled={loading || isFormDisabled}
                />
              </div>

              <div className="input-group">
                <img src={lockIcon} alt="password" />
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleInputChange}
                  disabled={loading || isFormDisabled}
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  disabled={loading || isFormDisabled}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>

              {!isLogin && (
                <div className="input-group">
                  <img src={lockIcon} alt="confirm password" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    disabled={loading || isFormDisabled}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    disabled={loading || isFormDisabled}
                    aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                    title={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                  >
                    {showConfirmPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              )}

              <button type="submit" className="submit-btn" disabled={loading || isFormDisabled}>
                {loading ? "Please wait..." : "Continue"}
              </button>
            </form>

            {isLogin && (
              <div className="remember-forgot">
                <label>
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>
                <button
                  className="forgot-btn"
                  type="button"
                  onClick={() => setShowForgotPasswordModal(true)}
                >
                  Forgot Password?
                </button>
              </div>
            )}

            {/* Social login — only on signup */}
            {!isLogin && (
              <>
                <div className="divider">
                  <hr />
                  <span>OR</span>
                  <hr />
                </div>

                <button
                  className="social-btn"
                  onClick={handleGoogleLogin}
                  disabled={loading || isFormDisabled}
                >
                  <img src={googleIcon} alt="google" />
                  Continue with Google
                </button>
                <button
                  className="social-btn"
                  onClick={handleAppleLogin}
                  disabled={loading || isFormDisabled}
                >
                  <img src={appleIcon} alt="apple" />
                  Continue with Apple
                </button>
              </>
            )}

            {!isLogin && (
              <p className="terms-text">
                By signing up, you agree to our <a href="#">Terms of service</a>{" "}
                and <a href="#">privacy policy</a>.
              </p>
            )}
          </div>
        </div>
        {/* Right Side - Image */}
        <div className="modal-right">
          <img src={signupImg} alt="Signup visual" />
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>
      </div>
      <ForgotPasswordModal
  isOpen={showForgotPasswordModal}
  onClose={() => setShowForgotPasswordModal(false)}
  defaultEmail={formData.email}
/>

    </div>
  );
};

export default SignupLoginModal;
