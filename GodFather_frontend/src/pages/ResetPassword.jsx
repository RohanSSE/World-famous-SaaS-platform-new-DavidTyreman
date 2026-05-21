import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import authService from "../services/authService";
import "../components/ResetPassword.css"
const ResetPasswordPage = () => {
  const { uid, token } = useParams();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.newPassword || !formData.confirmPassword) {
      toast.error("Please fill all fields.");
      return;
    }
    if (formData.newPassword.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (formData.newPassword !== formData.confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await authService.resetPasswordConfirm(
        uid,
        token,
        formData.newPassword,
        formData.confirmPassword
      );
      toast.success("Password reset! You can now log in.");
      setTimeout(() => {
        navigate("/intro-ductory");
      }, 1500);
    } catch (err) {
      toast.error(
        err?.new_password?.[0] ||
        err?.token?.[0] ||
        err?.detail ||
        err?.message ||
        "Failed to reset password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reset-password-root">
     <form className="reset-password-form" onSubmit={handleSubmit}>
  <h2>Set New Password</h2>
  <input
    type="password"
    name="newPassword"
    placeholder="New Password"
    value={formData.newPassword}
    onChange={handleChange}
    disabled={loading}
  />
  <input
    type="password"
    name="confirmPassword"
    placeholder="Confirm New Password"
    value={formData.confirmPassword}
    onChange={handleChange}
    disabled={loading}
  />
  <button type="submit" disabled={loading}>
    {loading ? "Resetting..." : "Reset Password"}
  </button>
</form>

    </div>
  );
};

export default ResetPasswordPage;
