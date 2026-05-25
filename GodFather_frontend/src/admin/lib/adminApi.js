import api from "../../services/api";

function adminGet(path, params = {}) {
  return api.get(path, { params }).then((r) => r.data);
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
};

export default adminApi;
