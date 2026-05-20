import api from "./api";

const authService = {
  // Sign up new user
  signup: async (email, password, confirmPassword, userType) => {
    try {
      const response = await api.post("/auth/register/", {
        email,
        password,
        confirm_password: confirmPassword,
        user_type: userType || "user", // "user" or "agency"
      });

      // Don't store tokens on signup — user must log in manually
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Signup failed" };
    }
  },

  // Login user
  login: async (email, password) => {
    try {
      const response = await api.post("/auth/login/", {
        email,
        password,
      });

      // Store tokens and user info
      if (response.data.access) {
        localStorage.setItem("accessToken", response.data.access);
        localStorage.setItem("refreshToken", response.data.refresh);
        localStorage.setItem(
          "user",
          JSON.stringify(response.data.user || { email })
        );
      }

      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Login failed" };
    }
  },

  // Logout user
  logout: async () => {
    try {
      const refreshToken = localStorage.getItem("refreshToken");
      await api.post("/auth/logout/", {
        refresh: refreshToken,
      });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local storage
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
    }
  },

  // Change password
  changePassword: async (old_password, new_password, confirm_password) => {
    const res = await api.post("/auth/change-password/", {
      old_password,
      new_password,
      confirm_password,
    });
    return res.data;
  },

  // Forgot password / Reset password request
  // Request password reset
  
  // Step 1: Request password reset email
  requestPasswordReset: async (email) => {
    const res = await api.post("/auth/password/reset/", { email });
    return res.data;
  },

  // Step 2: Confirm password reset from email link
  resetPasswordConfirm: async (uid, token, new_password, confirm_password) => {
    const res = await api.post("/auth/password/reset/confirm/", {
      uid,
      token,
      new_password,
      confirm_password,
    });
    return res.data;
  },
  // Get current user
  getCurrentUser: () => {
    const userStr = localStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem("accessToken");
  },

  // Google OAuth login
  googleLogin: async (tokenId) => {
    try {
      const response = await api.post("/auth/google/", {
        token: tokenId,
      });

      if (response.data.access) {
        localStorage.setItem("accessToken", response.data.access);
        localStorage.setItem("refreshToken", response.data.refresh);
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }

      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Google login failed" };
    }
  },

  // Apple OAuth login
  appleLogin: async (tokenId) => {
    try {
      const response = await api.post("/auth/apple/", {
        token: tokenId,
      });

      if (response.data.access) {
        localStorage.setItem("accessToken", response.data.access);
        localStorage.setItem("refreshToken", response.data.refresh);
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }

      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Apple login failed" };
    }
  },

  // Verify email
  verifyEmail: async (token) => {
    try {
      const response = await api.post("/auth/verify-email/", {
        token,
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Email verification failed" };
    }
  },

  // Refresh access token
  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem("refreshToken");
      const response = await api.post("/auth/token/refresh/", {
        refresh: refreshToken,
      });

      if (response.data.access) {
        localStorage.setItem("accessToken", response.data.access);
      }

      return response.data;
    } catch (error) {
      throw error.response?.data || { message: "Token refresh failed" };
    }
  },

  // ========== USER PROFILE MANAGEMENT ==========

  // Get all users (admin only typically)
  getUsers: async () => {
    try {
      const response = await api.get("/auth/users/");
      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to load users";
      throw { message: msg };
    }
  },

  // Get user by ID
  getUserById: async (userId) => {
    try {
      const response = await api.get(`/auth/users/${userId}/`);
      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to load user profile";
      throw { message: msg };
    }
  },

  // Get current user's profile
  getProfile: async () => {
    const response = await api.get("/auth/me/");
    if (response.data) {
      localStorage.setItem("user", JSON.stringify(response.data));
    }
    return response.data;
  },

  // Update user profile (PUT - full update)
  updateUserProfile: async (userId, userData) => {
    try {
      const response = await api.put(`/auth/users/${userId}/`, userData);

      // Update local storage with new user data
      if (response.data) {
        localStorage.setItem("user", JSON.stringify(response.data));
      }

      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to update profile";
      throw { message: msg };
    }
  },

  // Partially update user profile (PATCH - partial update)

  // Update current user's profile
  updateMyProfile: async (userData) => {
    try {
      const response = await api.put("/auth/me/", userData);
      if (response.data) {
        localStorage.setItem("user", JSON.stringify(response.data));
      }
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        "Failed to update profile";
      throw new Error(msg);
    }
  },

  // Partial update of profile (PATCH)
  updateMyProfilePartial: async (userData) => {
    try {
      const response = await api.patch("/auth/me/", userData);
      if (response.data) {
        // Update localStorage with partial data merged
        const currentUser = authService.getCurrentUser();
        const updatedUser = { ...currentUser, ...response.data };
        localStorage.setItem("user", JSON.stringify(updatedUser));
      }
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        "Failed to update profile";
      throw new Error(msg);
    }
  },

  // Delete user account
  deleteUser: async (userId) => {
    try {
      const response = await api.delete(`/auth/users/${userId}/`);

      // If deleting own account, clear local storage
      const currentUser = authService.getCurrentUser();
      if (currentUser?.id === userId) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
        localStorage.removeItem("session");
        localStorage.removeItem("sessionId");
      }

      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to delete account";
      throw { message: msg };
    }
  },

  // Upload profile image
  uploadProfileImage: async (userId, imageFile) => {
    try {
      const formData = new FormData();
      formData.append("profile_image", imageFile);

      const response = await api.patch(`/auth/users/${userId}/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Update local storage
      if (response.data) {
        localStorage.setItem("user", JSON.stringify(response.data));
      }

      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to upload profile image";
      throw { message: msg };
    }
  },

  // ========== NEW API INTEGRATIONS ==========

  // Get all agencies
  getAgencies: async () => {
    try {
      const response = await api.get("/auth/agencies/");
      const body = response.data;

      // Handle different response shapes
      if (Array.isArray(body)) return body;
      if (Array.isArray(body.results)) return body.results;
      return body;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        JSON.stringify(error.response?.data);
      throw { message: `Failed to load agencies: ${msg}` };
    }
  },

  // Get all sessions from dashboard
  getSessions: async () => {
    try {
      const response = await api.get("/sessions/");
      const body = response.data;

      // Normalize various response shapes into an array
      if (Array.isArray(body)) return body;
      if (Array.isArray(body.results)) return body.results;
      if (Array.isArray(body.sessions)) return body.sessions;
      if (body.session && typeof body.session === "object")
        return [body.session];
      if (body.data && Array.isArray(body.data)) return body.data;

      // Default: empty array
      return [];
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to load sessions";
      throw { message: msg };
    }
  },

  // Get all questions
  getQuestions: async () => {
    try {
      const response = await api.get("/sessions/questions/");
      const body = response.data;

      // Handle different response shapes
      if (Array.isArray(body)) return body;
      if (Array.isArray(body.results)) return body.results;
      if (Array.isArray(body.data)) return body.data;

      // Fallback: empty array
      return [];
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to load questions";
      throw { message: msg };
    }
  },

  // Create a new session
  createSession: async (payload) => {
    try {
      const response = await api.post("/sessions/create/", payload);
      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Failed to create session";
      throw { message: msg };
    }
  },

  // ========== SESSION ANSWER MANAGEMENT ==========
  // 👇 ADD THE NEW METHODS HERE

  createAnswer: async (sessionId, payload) => {
    if (!sessionId) {
      throw new Error("Missing sessionId for createAnswer");
    }

    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/answers/create/`,
        payload
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to create answer";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  getAnswers: async (sessionId, payload) => {
    if (!sessionId) {
      throw new Error("Missing sessionId for getAnswers");
    }

    try {
      const response = await api.get(
        `/sessions/${encodeURIComponent(sessionId)}/answers/`,
        payload
      );
      const body = response.data;

      if (Array.isArray(body)) return body;
      if (Array.isArray(body.results)) return body.results;
      if (Array.isArray(body.answers)) return body.answers;

      return [];
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to load answers";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  updateAnswer: async (sessionId, answerId, payload) => {
    if (!sessionId || !answerId) {
      throw new Error("Missing sessionId or answerId for updateAnswer");
    }

    try {
      const response = await api.patch(
        `/sessions/${encodeURIComponent(
          sessionId
        )}/answers/${encodeURIComponent(answerId)}/`,
        payload
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to update answer";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  deleteAnswer: async (sessionId, answerId) => {
    if (!sessionId || !answerId) {
      throw new Error("Missing sessionId or answerId for deleteAnswer");
    }

    try {
      const response = await api.delete(
        `/sessions/${encodeURIComponent(
          sessionId
        )}/answers/${encodeURIComponent(answerId)}/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to delete answer";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  // Batch save answers (upsert multiple in one request)
  batchSaveAnswers: async (sessionId, answers) => {
    if (!sessionId) {
      throw new Error("Missing sessionId for batchSaveAnswers");
    }
    if (!Array.isArray(answers)) {
      throw new Error("answers must be an array");
    }

    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/answers/batch/`,
        { answers }
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to batch save answers";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  // Contextual assistant suggestion for avatar bubble (activity-based)
  getAssistantSuggestion: async (sessionId, payload) => {
    if (!sessionId) {
      throw new Error("Missing sessionId for getAssistantSuggestion");
    }
    if (!payload?.route) {
      throw new Error("route is required for getAssistantSuggestion");
    }

    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/assistant-suggestion/`,
        {
          route: payload.route,
          time_on_page_seconds: payload.time_on_page_seconds ?? 0,
          current_step_index: payload.current_step_index ?? null,
          total_steps: payload.total_steps ?? null,
          answers_count: payload.answers_count ?? null,
          last_action: payload.last_action ?? "idle",
          available_actions: payload.available_actions ?? null,
        }
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to get assistant suggestion";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  // ========== SESSION COMPLETION ==========
  // ✅ FIXED: Use POST to hit /sessions/{id}/complete/
  completeSession: async (sessionId) => {
    if (!sessionId) {
      throw new Error("Missing sessionId for completeSession");
    }

    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/complete/`
        // No body needed - just hit the endpoint
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to complete session";

      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },
  // Start a session (mark status as in progress)
  startSession: async (sessionId) => {
    if (!sessionId) throw new Error("Missing sessionId for startSession");
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/start/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to start session";
      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },
  addComment: async (sessionId, payload) => {
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/comments/add/`,
        payload
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to add comment";
      throw new Error(msg);
    }
  },
  downloadManifesto: async (sessionId) => {
    try {
      const response = await api.get(
        `/sessions/${encodeURIComponent(sessionId)}/manifesto/download/`,
        { responseType: "blob" } // Important to get file blob
      );
      return response.data; // Blob data
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to download manifesto";
      throw new Error(msg);
    }
  },

  lockSession: async (sessionId) => {
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/lock/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to lock session";
      throw new Error(msg);
    }
  },

  unlockSession: async (sessionId) => {
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/unlock/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to unlock session";
      throw new Error(msg);
    }
  },

  getComments: async (sessionId) => {
    if (!sessionId) throw new Error("Missing sessionId");
    try {
      const response = await api.get(
        `/sessions/${encodeURIComponent(sessionId)}/comments/`
      );
      const data = response.data;
      // Adjust as per your API response structure
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.results)) return data.results;
      return [];
    } catch (error) {
      throw new Error(
        error.response?.data?.message || "Failed to fetch comments"
      );
    }
  },

  generateManifesto: async (sessionId) => {
    try {
      const response = await api.post(
        `/sessions/${sessionId}/generate-manifesto/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to generate manifesto";
      throw new Error(msg);
    }
  },
getManifesto: async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/manifesto/`);
  return response.data.json_output || response.data.data;
},

generateFoundationSummary: async (sessionId) => {
  if (!sessionId) {
    throw new Error("Missing sessionId for generateFoundationSummary");
  }

  try {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/generate-foundation-summary/`
    );
    return response.data; // { summary, total_questions_answered, cached }
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Failed to generate foundation summary";
    throw new Error(msg);
  }
},

generateSessionSummary: async (sessionId) => {
  if (!sessionId) {
    throw new Error("Missing sessionId for generateSessionSummary");
  }
  try {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/generate-summary/`
    );
    return response.data;
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Failed to generate brand summary";
    throw new Error(msg);
  }
},

getFoundationSummary: async (sessionId) => {
  if (!sessionId) {
    throw new Error("Missing sessionId for getFoundationSummary");
  }
  try {
    const response = await api.get(
      `/sessions/${encodeURIComponent(sessionId)}/foundation-summary/`
    );
    return response.data;
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Failed to fetch foundation summary";
    throw new Error(msg);
  }
},

updateFoundationSummary: async (sessionId, payload = {}) => {
  if (!sessionId) {
    throw new Error("Missing sessionId for updateFoundationSummary");
  }
  try {
    const response = await api.put(
      `/sessions/${encodeURIComponent(sessionId)}/update-foundation-summary/`,
      payload
    );
    return response.data;
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Failed to update foundation summary";
    throw new Error(msg);
  }
},


  // ai suggestion draft (returns backend data, e.g. { suggest: "..." })
// aiSuggestionDraft: async (sessionId, questionText, answerText) => {
//   if (!sessionId) {
//     throw new Error('Missing sessionId for aiSuggestionDraft');
//   }
 
//   try {
//     const payload = {
//       question_text: questionText ?? "",
//       answer_text: answerText ?? "",
//     };
 
//     // NOTE: path follows the curl you showed (sessions/sessions/{id}/ai-suggestion/draft/)
//     // If your backend uses /sessions/{id}/ai-suggestion/draft/ change accordingly.
//     const response = await api.post(
//       `/sessions/sessions/${encodeURIComponent(sessionId)}/ai-suggestion/draft/`,
//       payload
//     );
 
//     return response.data; // e.g. { suggest: "..." }
//   } catch (error) {
//     const msg =
//       error?.response?.data?.message ||
//       error?.response?.data?.detail ||
//       error?.message ||
//       'AI suggestion request failed';
//     const err = new Error(msg);
//     err._raw = error;
//     throw err;
//   }
// },


// ai suggestion draft (answer_ai_suggestion_draft)
aiSuggestionDraft: async (sessionId, questionId, draft, refined = false) => {
  if (!sessionId) {
    throw new Error("Missing sessionId for aiSuggestionDraft");
  }
  if (!questionId) {
    throw new Error("Missing questionId for aiSuggestionDraft");
  }
  if (!draft || !draft.trim()) {
    throw new Error("Missing draft text for aiSuggestionDraft");
  }

  try {
    const payload = {
      question_id: Number(questionId),
      draft: draft.trim(),
      refined: !!refined, // 👈 NEW FLAG
    };

    const response = await api.post(
      `/sessions/sessions/${encodeURIComponent(sessionId)}/ai-suggestion/draft/`,
      payload
    );

    return response.data; // { improved_answer, follow_up_question, ... }
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "AI suggestion request failed";

    const err = new Error(msg);
    err._raw = error;
    throw err;
  }
},

// Fetch followups for a session + answer_id (answer_id = "draft" or real Answer.id)
getFollowups: async (sessionId, answerId = "draft") => {
  if (!sessionId) throw new Error("Missing sessionId for getFollowups");
  try {
    const response = await api.get(
      `/sessions/sessions/${encodeURIComponent(sessionId)}/followups/?answer_id=${encodeURIComponent(answerId)}`
    );
    return response.data; // { followups: [...] }
  } catch (error) {
    const msg =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      "Failed to load followups";
    const err = new Error(msg);
    err._raw = error;
    throw err;
  }
},

// Append a user reply (and optionally trigger assistant followup)
appendFollowup: async (sessionId, answerId = "draft", userText, triggerAssistant = true) => {
  if (!sessionId) throw new Error("Missing sessionId for appendFollowup");
  if (!userText) throw new Error("Missing userText for appendFollowup");
  try {
    const payload = {
      answer_id: String(answerId),
      user_text: String(userText),
      trigger_assistant: !!triggerAssistant,
    };
    const response = await api.post(
      `/sessions/sessions/${encodeURIComponent(sessionId)}/followups/append/`,
      payload
    );
    return response.data; // { followups: [...] }
  } catch (error) {
    const msg =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      "Failed to append followup";
    const err = new Error(msg);
    err._raw = error;
    throw err;
  }
},


  setSessionLock: (sessionId, is_locked) =>
    api.patch(`/sessions/${sessionId}/`, { is_locked }),

  // Get conversations for a session by question_id
  getConversations: async (sessionId, questionId) => {
    if (!sessionId) throw new Error("Missing sessionId for getConversations");
    try {
      const url = questionId
        ? `/sessions/${encodeURIComponent(sessionId)}/conversations/?question_id=${encodeURIComponent(questionId)}`
        : `/sessions/${encodeURIComponent(sessionId)}/conversations/`;
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to load conversations";
      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  // Get AI answer suggestions based on user input
  getAiAnswerSuggestions: async (sessionId, questionId, userHint) => {
    if (!sessionId) throw new Error("Missing sessionId for getAiAnswerSuggestions");
    if (!questionId) throw new Error("Missing questionId for getAiAnswerSuggestions");

    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/ai-answer-suggestions/`,
        {
          question_id: Number(questionId),
          hints: typeof userHint === "string" ? userHint.trim() : "",
        }
      );
      return response.data; // { suggestions: [...] }
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to get AI suggestions";
      const err = new Error(msg);
      err._raw = error;
      throw err;
    }
  },

  // ========== AGENCY DASHBOARD ==========
  getAgencyDashboard: async () => {
    try {
      const response = await api.get("/sessions/dashboard/agency/");
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Failed to load agency dashboard";
      throw new Error(msg);
    }
  },

  // Approve/reject a session (agency marks it)
  approveSession: async (sessionId) => {
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/complete/`
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Failed to approve session";
      throw new Error(msg);
    }
  },

  // ========== USER / CLIENT DASHBOARD ==========
  getUserDashboard: async () => {
    try {
      const response = await api.get("/sessions/dashboard/user/");
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Failed to load user dashboard";
      throw new Error(msg);
    }
  },
};

export default authService;
