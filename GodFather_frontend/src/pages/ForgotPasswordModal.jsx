import React, { useState } from "react";
import { toast } from "react-toastify";
import mailIcon from "../svg_assets/Email.svg";
import authService from "../services/authService";
import Modal from "./Modal";

const ForgotPasswordModal = ({ isOpen, onClose, defaultEmail = "" }) => {
  const [email, setEmail] = useState(defaultEmail);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error("Please enter your email");
      return;
    }
    setLoading(true);
    try {
      await authService.requestPasswordReset(email);
      toast.success("Password reset email sent! Check your inbox.");
      onClose();
    } catch (err) {
      toast.error(
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
    <Modal isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit} className="forgot-password-modal-form">
        <h2>Forgot Password?</h2>
        <div className="input-group">
          <img src={mailIcon} alt="email" />
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="Enter your email"
            disabled={loading}
          />
        </div>
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Sending..." : "Send Password Reset Email"}
        </button>
      </form>
    </Modal>
  );
};

export default ForgotPasswordModal;
