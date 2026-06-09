import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { DashboardContent } from "@admin/layouts/dashboard/content";
import adminApi from "@admin/lib/adminApi";

const defaultPlanForm = {
  id: null,
  name: "",
  description: "",
  price: "",
  currency: "usd",
  billing_interval: "one_time",
  question_gate_after: 8,
  is_active: true,
  display_order: 0,
};

const currencyOptions = [
  { value: "usd", label: "USD" },
  { value: "inr", label: "INR" },
  { value: "eur", label: "EUR" },
  { value: "gbp", label: "GBP" },
  { value: "aed", label: "AED" },
];

function toPlanForm(plan) {
  if (!plan) return defaultPlanForm;
  return {
    ...defaultPlanForm,
    ...plan,
    price: String(plan.price ?? defaultPlanForm.price),
    question_gate_after: Number(plan.question_gate_after ?? defaultPlanForm.question_gate_after),
  };
}

export default function SubscriptionPage() {
  const [plans, setPlans] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [planForm, setPlanForm] = useState(defaultPlanForm);
  const [planLoading, setPlanLoading] = useState(false);
  const [planSaving, setPlanSaving] = useState(false);
  const [planMessage, setPlanMessage] = useState("");
  const [planError, setPlanError] = useState("");
  const [subscriberLoading, setSubscriberLoading] = useState(false);
  const [subscriberError, setSubscriberError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadPlans() {
      setPlanLoading(true);
      setPlanError("");
      try {
        const list = await adminApi.listSubscriptionPlans();
        if (cancelled) return;
        const normalized = Array.isArray(list) ? list : [];
        setPlans(normalized);
        setPlanForm(toPlanForm(normalized.find((plan) => plan.is_active) || normalized[0]));
      } catch (error) {
        if (!cancelled) setPlanError(error.response?.data?.detail || error.message || "Failed to load plans");
      } finally {
        if (!cancelled) setPlanLoading(false);
      }
    }

    async function loadSubscribers() {
      setSubscriberLoading(true);
      setSubscriberError("");
      try {
        const data = await adminApi.listSubscriptionSubscribers();
        if (cancelled) return;
        setSubscribers(Array.isArray(data?.subscribers) ? data.subscribers : []);
        if (data?.stripe_error) setSubscriberError(data.stripe_error);
      } catch (error) {
        if (!cancelled) setSubscriberError(error.response?.data?.detail || error.message || "Failed to load subscribers");
      } finally {
        if (!cancelled) setSubscriberLoading(false);
      }
    }

    loadPlans();
    loadSubscribers();
    return () => {
      cancelled = true;
    };
  }, []);

  const openPaymentDocument = (payment = {}) => {
    const url = payment.invoice_pdf || payment.hosted_invoice_url || payment.receipt_url;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  const paymentActionLabel = (payment = {}) => {
    if (payment.invoice_pdf) return "Download invoice";
    if (payment.hosted_invoice_url) return "View invoice";
    if (payment.receipt_url) return "View receipt";
    return "No invoice";
  };

  const updatePlanForm = (field) => (event) => {
    const value = event.target.value;
    setPlanForm((prev) => ({ ...prev, [field]: value }));
    setPlanMessage("");
    setPlanError("");
  };

  const savePlan = async (event) => {
    event.preventDefault();
    setPlanSaving(true);
    setPlanMessage("");
    setPlanError("");
    try {
      const payload = {
        name: planForm.name.trim(),
        description: planForm.description.trim(),
        price: planForm.price,
        currency: planForm.currency.trim().toLowerCase() || "usd",
        billing_interval: planForm.billing_interval,
        question_gate_after: Math.max(0, Math.min(30, Number(planForm.question_gate_after) || 0)),
        is_active: true,
        display_order: Number(planForm.display_order) || 0,
        stripe_product_id: "",
        stripe_price_id: "",
      };

      const saved = planForm.id
        ? await adminApi.updateSubscriptionPlan(planForm.id, payload)
        : await adminApi.createSubscriptionPlan(payload);
      const list = await adminApi.listSubscriptionPlans();
      setPlans(Array.isArray(list) ? list : []);
      setPlanForm(toPlanForm(saved));
      setPlanMessage("Subscription plan saved.");
    } catch (error) {
      const detail = error.response?.data || error.message || "Failed to save plan";
      setPlanError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setPlanSaving(false);
    }
  };

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 2 }}>
        Subscription
      </Typography>

      <Card sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" sx={{ mb: 0.5 }}>
          Subscription plan
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
          Set the checkout price and the question number after which users must subscribe.
        </Typography>

        {planError && <Alert severity="error" sx={{ mb: 2 }}>{planError}</Alert>}
        {planMessage && <Alert severity="success" sx={{ mb: 2 }}>{planMessage}</Alert>}

        <Box component="form" onSubmit={savePlan}>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "1.4fr 1fr 1fr 1fr" },
              gap: 2,
            }}
          >
            <TextField
              label="Plan name"
              value={planForm.name}
              onChange={updatePlanForm("name")}
              required
              disabled={planLoading || planSaving}
            />
            <TextField
              label="Price"
              type="number"
              value={planForm.price}
              onChange={updatePlanForm("price")}
              inputProps={{ min: 0, step: "0.01" }}
              required
              disabled={planLoading || planSaving}
            />
            <TextField
              select
              label="Currency"
              value={planForm.currency || "usd"}
              onChange={updatePlanForm("currency")}
              required
              disabled={planLoading || planSaving}
            >
              {currencyOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Checkout after question"
              type="number"
              value={planForm.question_gate_after}
              onChange={updatePlanForm("question_gate_after")}
              inputProps={{ min: 0, max: 30, step: 1 }}
              required
              disabled={planLoading || planSaving}
            />
            <TextField
              select
              label="Billing interval"
              value={planForm.billing_interval}
              onChange={updatePlanForm("billing_interval")}
              disabled={planLoading || planSaving}
            >
              <MenuItem value="one_time">One time</MenuItem>
              <MenuItem value="month">Monthly</MenuItem>
              <MenuItem value="year">Yearly</MenuItem>
            </TextField>
            <TextField
              label="Display order"
              type="number"
              value={planForm.display_order}
              onChange={updatePlanForm("display_order")}
              disabled={planLoading || planSaving}
            />
          </Box>

          <TextField
            label="Description"
            value={planForm.description}
            onChange={updatePlanForm("description")}
            multiline
            minRows={2}
            fullWidth
            sx={{ mt: 2 }}
            disabled={planLoading || planSaving}
          />

          <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: "wrap", rowGap: 1 }}>
            <Button type="submit" variant="contained" disabled={planLoading || planSaving}>
              {planSaving ? "Saving..." : planForm.id ? "Update plan" : "Add plan"}
            </Button>
            <Button type="button" variant="outlined" onClick={() => setPlanForm(defaultPlanForm)} disabled={planSaving}>
              New plan
            </Button>
          </Stack>
        </Box>

        {plans.length > 0 && (
          <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
            {plans.map((plan) => (
              <Chip
                key={plan.id}
                clickable
                color={plan.is_active ? "primary" : "default"}
                label={`${plan.name} - ${plan.price_display} - after Q${plan.question_gate_after}`}
                onClick={() => setPlanForm(toPlanForm(plan))}
              />
            ))}
          </Box>
        )}
      </Card>

      <Card sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 0.5 }}>
          Subscribers & payments
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
          See who purchased a subscription, whether the account is a user or agency, and open their invoice or receipt.
        </Typography>

        {subscriberError && <Alert severity="warning" sx={{ mb: 2 }}>{subscriberError}</Alert>}
        {subscriberLoading && <Typography color="text.secondary">Loading subscribers...</Typography>}
        {!subscriberLoading && subscribers.length === 0 && (
          <Typography color="text.secondary">No subscription payments yet.</Typography>
        )}
        {!subscriberLoading && subscribers.length > 0 && (
          <Box sx={{ overflowX: "auto" }}>
            <Box
              component="table"
              sx={{
                width: "100%",
                minWidth: 920,
                borderCollapse: "collapse",
                "th, td": {
                  textAlign: "left",
                  p: 1.25,
                  borderBottom: "1px solid rgba(255,255,255,0.08)",
                  verticalAlign: "top",
                },
                th: { color: "text.secondary", fontSize: 12, fontWeight: 700 },
                td: { color: "text.primary", fontSize: 13 },
              }}
            >
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Type</th>
                  <th>Agency</th>
                  <th>Plan</th>
                  <th>Status</th>
                  <th>Amount</th>
                  <th>Updated</th>
                  <th>Invoice</th>
                </tr>
              </thead>
              <tbody>
                {subscribers.map((item) => {
                  const user = item.user || {};
                  const plan = item.plan || {};
                  const payment = item.payment || {};
                  const docUrl = payment.invoice_pdf || payment.hosted_invoice_url || payment.receipt_url;
                  return (
                    <tr key={item.id}>
                      <td>{user.email || "-"}</td>
                      <td>
                        <Chip size="small" label={user.account_type === "agency" ? "Agency" : "User"} color={user.account_type === "agency" ? "info" : "default"} />
                      </td>
                      <td>{user.agency_name || "-"}</td>
                      <td>{plan.name || "-"}</td>
                      <td>{item.status || "-"}</td>
                      <td>{payment.amount_display || plan.price_display || "-"}</td>
                      <td>{item.updated_at ? new Date(item.updated_at).toLocaleString() : "-"}</td>
                      <td>
                        <Button size="small" variant="outlined" disabled={!docUrl} onClick={() => openPaymentDocument(payment)}>
                          {paymentActionLabel(payment)}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Box>
          </Box>
        )}
      </Card>
    </DashboardContent>
  );
}