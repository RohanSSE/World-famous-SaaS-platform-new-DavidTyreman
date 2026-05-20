import React, { useState } from "react";
import { toast } from "react-toastify";
import authService from "../services/authService";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
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
      toast.success("Password reset email sent. Please check your inbox!");
    } catch (err) {
      toast.error(
        err?.email?.[0] ||
        err?.detail ||
        err?.message ||
        "Failed to send reset email"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Forgot Password</h2>
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="Enter your email"
        disabled={loading}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Sending..." : "Send Reset Email"}
      </button>
    </form>
  );
};

export default ForgotPassword;
