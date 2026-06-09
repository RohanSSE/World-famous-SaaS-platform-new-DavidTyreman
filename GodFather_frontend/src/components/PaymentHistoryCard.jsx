import { useEffect, useState } from "react";
import { CreditCard, Download, ReceiptText } from "lucide-react";
import authService from "../services/authService";
import "./PaymentHistoryCard.css";

function paymentUrl(payment = {}) {
  return payment.invoice_pdf || payment.hosted_invoice_url || payment.receipt_url || "";
}

function paymentActionLabel(payment = {}) {
  if (payment.invoice_pdf) return "Download invoice";
  if (payment.hosted_invoice_url) return "View invoice";
  if (payment.receipt_url) return "View receipt";
  return "Unavailable";
}

export default function PaymentHistoryCard({ title = "Billing & invoices" }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [payments, setPayments] = useState([]);
  const [stripeError, setStripeError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadBilling() {
      setLoading(true);
      setError("");
      try {
        const data = await authService.getBillingHistory();
        if (cancelled) return;
        setPayments(Array.isArray(data?.payments) ? data.payments : []);
        setStripeError(data?.stripe_error || "");
      } catch (err) {
        if (!cancelled) setError(err?.message || "Failed to load billing history");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadBilling();
    return () => {
      cancelled = true;
    };
  }, []);

  const openDocument = (payment) => {
    const url = paymentUrl(payment);
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <section className="payment-history-card">
      <div className="payment-history-header">
        <div>
          <h3><CreditCard size={20} /> {title}</h3>
          <p>Your subscription payment records and invoice downloads.</p>
        </div>
      </div>

      {loading && <div className="payment-history-state">Loading billing history...</div>}
      {error && <div className="payment-history-error">{error}</div>}
      {!loading && !error && stripeError && (
        <div className="payment-history-warning">Stripe documents could not be refreshed. Local payment records are shown.</div>
      )}
      {!loading && !error && payments.length === 0 && (
        <div className="payment-history-empty">No subscription payments yet.</div>
      )}

      {!loading && !error && payments.length > 0 && (
        <div className="payment-history-list">
          {payments.map((item) => {
            const payment = item.payment || {};
            const plan = item.plan || {};
            const docUrl = paymentUrl(payment);
            return (
              <div className="payment-history-row" key={item.id}>
                <div className="payment-history-icon"><ReceiptText size={18} /></div>
                <div className="payment-history-main">
                  <strong>{plan.name || "Subscription"}</strong>
                  <span>{payment.amount_display || plan.price_display || "Payment recorded"}</span>
                  <small>Status: {item.status || payment.payment_status || "pending"}</small>
                </div>
                <div className="payment-history-meta">
                  <span>{item.updated_at ? new Date(item.updated_at).toLocaleDateString() : ""}</span>
                  <button type="button" onClick={() => openDocument(payment)} disabled={!docUrl}>
                    <Download size={14} /> {paymentActionLabel(payment)}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
