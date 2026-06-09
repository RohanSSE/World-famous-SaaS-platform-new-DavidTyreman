import api from "../../services/api";

function adminGet(path, params = {}) {
  return api.get(path, { params }).then((r) => r.data);
}

function adminPost(path, data = {}) {
  return api.post(path, data).then((r) => r.data);
}

function adminPatch(path, data = {}) {
  return api.patch(path, data).then((r) => r.data);
}

export const adminApi = {
  cognitionDashboard: (days = 7) =>
    adminGet("/sessions/admin/cognition-dashboard/", { days }),
  cognitionTraces: (limit = 50) =>
    adminGet("/sessions/admin/cognition-traces/", { limit }),
  feedbackReview: (limit = 50) =>
    adminGet("/sessions/admin/feedback-review/", { limit }),
  productObservability: () => adminGet("/sessions/product-observability/"),
  aiCost: (days = 7) => adminGet("/sessions/ai-cost-dashboard/", { days }),
  ragHealth: () => adminGet("/sessions/rag-system-health/"),
  cognitionLive: (minutes = 30) =>
    adminGet("/sessions/admin/cognition-live/", { minutes }),
  chunkQuality: (limit = 500) =>
    adminGet("/sessions/admin/chunk-quality/", { limit }),
  productSignals: (days = 14) =>
    adminGet("/sessions/admin/product-signals/", { days }),
  opsIntelligence: (days = 14) =>
    adminGet("/sessions/admin/ops-intelligence/", { days }),

  listSubscriptionPlans: () => adminGet("/auth/subscription/plans/"),
  listSubscriptionSubscribers: () => adminGet("/auth/subscription/subscribers/"),
  createSubscriptionPlan: (payload) => adminPost("/auth/subscription/plans/", payload),
  updateSubscriptionPlan: (planId, payload) =>
    adminPatch(`/auth/subscription/plans/${planId}/`, payload),

  listUsers: () => adminGet("/auth/users/"),
  listAgencies: () => adminGet("/auth/agencies/"),
  listSessions: () => adminGet("/sessions/"),
  // Admin: question CRUD (bulk stage replace)
  listQuestions: () => adminGet("/sessions/questions/"),
  bulkSetQuestions: async (payload) => {
    const response = await api.post("/sessions/admin/questions/bulk-set/", payload);
    return response.data;
  },
  updateUser: async (userId, data) => {
    try {
      const response = await api.patch(`/auth/users/${userId}/`, data);
      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Failed to update user";
      throw new Error(typeof msg === "string" ? msg : "Failed to update user");
    }
  },
  updateAgency: async (agencyId, data) => {
    try {
      const response = await api.patch(`/auth/agencies/${agencyId}/`, data);
      return response.data;
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Failed to update agency";
      throw new Error(typeof msg === "string" ? msg : "Failed to update agency");
    }
  },
};

export default adminApi;
