import React, { useState, useEffect } from "react";
import { X } from "lucide-react";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthProvider";
import authService from "../services/authService";
import "../components/ProfileModal.css";

const ProfileModal = ({ isOpen, onClose }) => {
  const { auth, setAuth } = useAuth();
  const [formData, setFormData] = useState({
    email: auth.user?.email || "",
    phone: auth.user?.phone_number || "",
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Fetch the latest user data when the modal opens
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const userData = await authService.getProfile();
        setFormData({
          email: userData.email || "",
          phone: userData.phone_number || "",
        });
      } catch (error) {
        console.error("Failed to fetch user data:", error);
      }
    };

    if (isOpen) {
      fetchUserData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);

    try {
      if (formData.phone && !/^\+?[\d\s-()]+$/.test(formData.phone)) {
        toast.error("Please enter a valid phone number");
        setLoading(false);
        return;
      }

      const updatedUser = await authService.updateMyProfile({
        phone_number: formData.phone,
      });

      // Update the auth context with the response from the backend
      setAuth((prev) => ({
        ...prev,
        user: {
          ...prev.user,
          ...updatedUser,
        },
      }));

      // Update local state with the new phone number
      setFormData((prev) => ({
        ...prev,
        phone: updatedUser.phone_number,
      }));

      setSuccess(true);
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error("Profile update error:", error);
      toast.error(error.message || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="profile-modal-overlay" onClick={handleOverlayClick}>
      <div className="profile-modal">
        <div className="profile-modal-header">
          <h2 className="profile-modal-title">Edit Profile</h2>
          <button
            className="profile-modal-close"
            onClick={onClose}
            type="button"
          >
            <X size={24} />
          </button>
        </div>

        {success && (
          <div className="profile-success-message">
            Profile updated successfully!
          </div>
        )}

        <form onSubmit={handleSubmit} className="profile-modal-form">
          <div className="profile-form-group">
            <label className="profile-form-label">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              className="profile-form-input profile-input-readonly"
              disabled
            />
            <p className="profile-field-hint">Email cannot be changed</p>
          </div>

          <div className="profile-form-group">
            <label className="profile-form-label">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              placeholder="+1 (555) 123-4567"
              className="profile-form-input"
              disabled={loading}
            />
          </div>

          <div className="profile-modal-actions">
            <button
              type="button"
              className="profile-btn profile-btn-cancel"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="profile-btn profile-btn-save"
              disabled={loading}
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileModal;
