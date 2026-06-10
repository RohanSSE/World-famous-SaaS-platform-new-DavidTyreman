import api from "./api";

const API_BASE_URL = api.defaults.baseURL;

/** Parse DRF / axios errors into a single user-facing string */
export function formatApiError(error, fallback = "Request failed") {
  if (!error) return fallback;
  const data = error.response?.data ?? (typeof error === "object" ? error : null);
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const parts = [];
    for (const [key, val] of Object.entries(data)) {
      if (["detail", "message", "status"].includes(key)) continue;
      if (Array.isArray(val)) parts.push(`${key}: ${val.join(" ")}`);
      else if (typeof val === "string") parts.push(`${key}: ${val}`);
    }
    if (parts.length) return parts.join(" · ");
  }
  if (data?.detail) {
    return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  }
  if (data?.message) return data.message;
  if (error.message) return error.message;
  return fallback;
}

function normalizeSessionId(session) {
  return session?.id ?? session?.pk ?? session?.session_id ?? null;
}

function isCompletedSession(session) {
  const status = String(session?.status || "").toLowerCase();
  const progress = Number(session?.progress ?? session?.completion_pct ?? 0);
  return status === "completed" || status === "locked" || progress >= 100;
}

function clampPhase(value) {
  const phase = Number(value);
  if (!Number.isFinite(phase)) return 1;
  return Math.max(1, Math.min(3, phase));
}

function resolveAgencyOnboardingRedirect(dashboard = {}) {
  const sessions = Array.isArray(dashboard.sessions) ? dashboard.sessions : [];
  const journey = Array.isArray(dashboard.journey_progress) ? dashboard.journey_progress : [];
  const completed = sessions.some(isCompletedSession) || journey.some(isCompletedSession);

  if (completed) {
    return { route: "/agency-dashboard", completed: true, session: null };
  }

  const latestSessionId = dashboard.latest_session_id ?? normalizeSessionId(sessions[0]);
  const session = sessions.find((item) => String(normalizeSessionId(item)) === String(latestSessionId)) || sessions[0] || null;
  const progress = journey.find((item) => String(item.session_id) === String(latestSessionId)) || journey[0] || null;
  const sessionId = normalizeSessionId(session) ?? progress?.session_id ?? null;

  if (sessionId) {
    const sessionForStorage = session || {
      id: sessionId,
      title: progress?.title || "Agency Brand Discovery",
      status: progress?.status || "in_progress",
      progress: progress?.progress || 0,
    };
    try {
      localStorage.setItem("session", JSON.stringify(sessionForStorage));
      localStorage.setItem("sessionId", String(sessionId));
    } catch {
      /* ignore storage failures */
    }
    const nextPhase = clampPhase(progress?.current_stage_num || 1);
    return { route: `/phase-questions/${nextPhase}`, completed: false, session: sessionForStorage };
  }

  return { route: "/welcome", completed: false, session: null };
}

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
      const data = error.response?.data || {};
      throw {
        ...data,
        message: data.detail || data.message || "Login failed",
        status: error.response?.status,
      };
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

  // Get all questions, optionally scoped to a session/stage for progression checks
  getQuestions: async (sessionId, stage, options = {}) => {
    try {
      const params = {};
      if (sessionId) params.session_id = sessionId;
      if (stage) params.stage = stage;
      if (options.forceRefine) params.force_refine = 1;
      const response = await api.get("/sessions/questions/", { params });
      const body = response.data;

      if (sessionId || stage) return body;

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
      throw {
        message: msg,
        code: error.response?.data?.code,
        status: error.response?.status,
      };
    }
  },

  getBillingStatus: async () => {
    try {
      const response = await api.get("/auth/subscription/");
      const currentUser = authService.getCurrentUser() || {};
      localStorage.setItem(
        "user",
        JSON.stringify({
          ...currentUser,
          has_active_subscription: !!response.data?.has_active_subscription,
          active_subscription: response.data?.subscription || null,
          subscription_plan: response.data?.plan || null,
        })
      );
      return response.data;
    } catch (error) {
      const msg = formatApiError(error, "Failed to load subscription");
      throw { message: msg, status: error.response?.status };
    }
  },

  getBillingHistory: async () => {
    try {
      const response = await api.get("/auth/subscription/invoices/");
      return response.data;
    } catch (error) {
      const msg = formatApiError(error, "Failed to load billing history");
      throw { message: msg, status: error.response?.status };
    }
  },

  createSubscriptionCheckout: async (payload = {}) => {
    try {
      const response = await api.post("/auth/subscription/checkout/", payload);
      return response.data;
    } catch (error) {
      const msg = formatApiError(error, "Failed to start checkout");
      throw { message: msg, status: error.response?.status };
    }
  },

  verifySubscriptionCheckout: async (checkoutSessionId) => {
    try {
      const response = await api.post("/auth/subscription/verify/", {
        checkout_session_id: checkoutSessionId,
      });
      const currentUser = authService.getCurrentUser() || {};
      localStorage.setItem(
        "user",
        JSON.stringify({
          ...currentUser,
          has_active_subscription: !!response.data?.has_active_subscription,
          active_subscription: response.data?.subscription || null,
          subscription_plan: response.data?.plan || null,
        })
      );
      return response.data;
    } catch (error) {
      const msg = formatApiError(error, "Failed to verify checkout");
      throw { message: msg, status: error.response?.status };
    }
  },

  // Create a new session
  createSession: async (payload) => {
    try {
      const body = { title: String(payload?.title || "").trim() };
      const agencyId = payload?.agency != null ? Number(payload.agency) : NaN;
      if (Number.isFinite(agencyId) && agencyId > 0) {
        body.agency = agencyId;
      }
      const response = await api.post("/sessions/create/", body);
      return response.data;
    } catch (error) {
      throw { message: formatApiError(error, "Failed to create session") };
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

  getBrandBookHeadingInsight: async (sessionId, payload) => {
    if (!sessionId) throw new Error("Missing sessionId for getBrandBookHeadingInsight");
    if (!payload?.heading) throw new Error("heading is required for getBrandBookHeadingInsight");
    try {
      const response = await api.post(
        `/sessions/${encodeURIComponent(sessionId)}/brand-book-insight/`,
        {
          heading: payload.heading,
          content: payload.content ?? "",
          page_id: payload.page_id ?? "",
        }
      );
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to get heading insight";
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
      `/sessions/${encodeURIComponent(sessionId)}/generate-foundation-summary/`,
      { async: false }
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
      `/sessions/${encodeURIComponent(sessionId)}/generate-summary/`,
      { async: false }
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
      throw { message: msg, status: error.response?.status, detail: msg };
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

  // RAG query (non-streaming)
  ragQuery: async (query, options = {}) => {
    const {
      sessionId = null,
      agentId = "strategist",
      includeUserDocs = false,
      conversationMessages = [],
      sessionSummary = null,
      includeEvaluation = false,
    } = options;

    if (!query || !query.trim()) {
      throw new Error("Missing query for ragQuery");
    }

    const path = sessionId
      ? `/sessions/${encodeURIComponent(sessionId)}/rag-query/`
      : "/sessions/rag-query/";

    try {
      const response = await api.post(path, {
        query: query.trim(),
        agent_id: agentId,
        include_user_docs: includeUserDocs,
        conversation_messages: conversationMessages,
        session_summary: sessionSummary,
        include_evaluation: includeEvaluation,
      });
      return response.data;
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "RAG query failed";
      throw new Error(msg);
    }
  },

  // RAG query SSE stream URL + helper (use with useRagStream or fetch)
  ragQueryStreamUrl: (sessionId = null) =>
    sessionId
      ? `${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}/rag-query/stream/`
      : `${API_BASE_URL}/sessions/rag-query/stream/`,

  ragQueryStream: async (query, options = {}, callbacks = {}) => {
    const {
      sessionId = null,
      agentId = "strategist",
      includeUserDocs = false,
      conversationMessages = [],
      sessionSummary = null,
      signal = null,
    } = options;

    if (!query || !query.trim()) {
      throw new Error("Missing query for ragQueryStream");
    }

    const token = localStorage.getItem("accessToken");
    const url = authService.ragQueryStreamUrl(sessionId);

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: JSON.stringify({
        query: query.trim(),
        agent_id: agentId,
        include_user_docs: includeUserDocs,
        conversation_messages: conversationMessages,
        session_summary: sessionSummary,
      }),
      signal,
    });

    if (!res.ok) {
      throw new Error(`RAG stream failed: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let accumulated = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "system_health") {
            callbacks.onSystemHealth?.(event.system_health);
          } else if (event.type === "sources") {
            callbacks.onSources?.(event);
          } else if (event.type === "token") {
            accumulated += event.content || "";
            callbacks.onToken?.(event.content, accumulated);
          } else if (event.type === "done") {
            callbacks.onDone?.(accumulated, event);
          } else if (event.type === "error") {
            throw new Error(event.message || "Stream error");
          }
        } catch (parseErr) {
          if (parseErr.message?.includes("Stream")) throw parseErr;
        }
      }
    }

    return accumulated;
  },

  // ========== BRAND OPERATING SYSTEM ==========
  listBrandWorkflows: async () => {
    const response = await api.get("/sessions/brand-workflows/");
    return response.data;
  },

  runBrandWorkflow: async (sessionId, workflow, extraContext = "") => {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/brand-workflow/`,
      { workflow, extra_context: extraContext }
    );
    return response.data;
  },

  getFeedbackLearningProfile: async (sessionId) => {
    const response = await api.get(
      `/sessions/${encodeURIComponent(sessionId)}/feedback-learning/`
    );
    return response.data;
  },

  submitFeedbackLearning: async (sessionId, payload) => {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/feedback-learning/`,
      payload
    );
    return response.data;
  },

  getBrandBrain: async (sessionId) => {
    const response = await api.get(
      `/sessions/${encodeURIComponent(sessionId)}/brand-brain/`
    );
    return response.data;
  },

  exportBrandPack: async (sessionId, workflow = "pack") => {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/brand-export/`,
      { workflow, format: "json" }
    );
    return response.data;
  },

  downloadBrandExport: async (sessionId, workflow = "pack", format = "pdf", styled = false) => {
    const response = await api.get(
      `/sessions/${encodeURIComponent(sessionId)}/brand-export/`,
      {
        params: { workflow, export_format: format, ...(styled ? { styled: "premium" } : {}) },
        responseType: "blob",
      }
    );
    const ext = format === "pptx" ? "pptx" : format === "pdf" ? "pdf" : "json";
    const blob = new Blob([response.data], {
      type: response.headers["content-type"] || "application/octet-stream",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brand-${workflow}-${sessionId}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
    return true;
  },

  downloadBrandSummaryExport: async (sessionId, payload = {}) => {
    const response = await api.post(
      `/sessions/${encodeURIComponent(sessionId)}/brand-export/`,
      {
        workflow: "brand_summary",
        export_format: "pdf",
        styled: "premium",
        ...payload,
      },
      { responseType: "blob" }
    );
    const blob = new Blob([response.data], {
      type: response.headers["content-type"] || "application/pdf",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brand-summary-${sessionId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    return true;
  },

  getProductObservability: async () => {
    const response = await api.get("/sessions/product-observability/");
    return response.data;
  },

  listDemoBrands: async () => {
    const response = await api.get("/sessions/demo-brands/");
    return response.data;
  },

  runDemoPack: async (sessionId, demoId = "luxury") => {
    const response = await api.post(`/sessions/${encodeURIComponent(sessionId)}/demo-pack/`, {
      demo_id: demoId,
    });
    return response.data;
  },

  recordPilotEvent: async (sessionId, signal, meta = {}) => {
    const response = await api.post(`/sessions/${encodeURIComponent(sessionId)}/pilot-event/`, {
      signal,
      meta,
    });
    return response.data;
  },

  getSessionPilotKpis: async (sessionId) => {
    const response = await api.get(`/sessions/${encodeURIComponent(sessionId)}/pilot-kpis/`);
    return response.data;
  },

  getUserPilotSummary: async (days = 30) => {
    const response = await api.get("/sessions/pilot-summary/", { params: { days } });
    return response.data;
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

  getAgencyOnboardingRedirect: async () => {
    const dashboard = await authService.getUserDashboard();
    return resolveAgencyOnboardingRedirect(dashboard);
  },
};

export default authService;
