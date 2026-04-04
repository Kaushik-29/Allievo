import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import apiClient from "../../api/client";
import {
  CloudRain, Wind, Thermometer, AlertTriangle, Zap,
  CheckCircle2, Clock, Shield, CreditCard, XCircle,
  ChevronDown, ChevronUp, Loader2, PlusCircle, X,
  MapPin, FileText, AlertCircle, RefreshCw, Star,
} from "lucide-react";

/* ─── Config maps ─────────────────────────────────────────── */
const TRIGGER_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  rainfall: { icon: CloudRain,      color: "text-blue-400 bg-blue-500/10 border-blue-500/20",   label: "Monsoon Rainfall" },
  heat:     { icon: Thermometer,    color: "text-orange-400 bg-orange-500/10 border-orange-500/20", label: "Heat Advisory"  },
  aqi:      { icon: Wind,           color: "text-purple-400 bg-purple-500/10 border-purple-500/20", label: "AQI Crisis"    },
  curfew:   { icon: AlertTriangle,  color: "text-amber-400 bg-amber-500/10 border-amber-500/20",  label: "Curfew / Bandh" },
  outage:   { icon: Zap,            color: "text-rose-400 bg-rose-500/10 border-rose-500/20",     label: "Platform Outage"},
  other:    { icon: Shield,         color: "text-slate-400 bg-slate-500/10 border-slate-500/20",  label: "Other Disruption"},
  Unknown:  { icon: Shield,         color: "text-slate-400 bg-slate-500/10 border-slate-500/20",  label: "Disruption"     },
};

const STATUS_CONFIG: Record<string, { color: string; label: string; icon: any }> = {
  auto_approved: { color: "text-success-400 bg-success-500/10 border-success-500/20", label: "Auto Approved", icon: CheckCircle2 },
  approved:      { color: "text-success-400 bg-success-500/10 border-success-500/20", label: "Approved",      icon: CheckCircle2 },
  under_review:  { color: "text-warning-400 bg-warning-500/10 border-warning-500/20", label: "Under Review",  icon: Clock       },
  auto_denied:   { color: "text-danger-400 bg-danger-500/10 border-danger-500/20",    label: "Auto Denied",   icon: XCircle     },
  denied:        { color: "text-danger-400 bg-danger-500/10 border-danger-500/20",    label: "Denied",        icon: XCircle     },
  pending:       { color: "text-slate-400 bg-slate-500/10 border-slate-500/20",       label: "Processing",    icon: Loader2     },
};

const AUTO_RESULT_CONF: Record<string, { color: string; label: string }> = {
  auto_approve: { color: "text-success-400", label: "✅ Auto-approved" },
  review:       { color: "text-warning-400", label: "⏳ Needs review"  },
  auto_deny:    { color: "text-danger-400",  label: "❌ Auto-denied"   },
};

/* ─── Main Component ─────────────────────────────────────────── */
export default function ClaimHistory() {
  const { userId } = useAuthStore();
  const [claims, setClaims] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { if (userId) fetchClaims(); }, [userId]);

  const fetchClaims = async () => {
    if (!userId) return;
    try {
      const res = await apiClient.get(`/api/v1/manual-claims/my/${userId}`);
      setClaims(res.data.claims || []);
    } catch {
      setClaims([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => { setRefreshing(true); fetchClaims(); };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">My Claims</h1>
          <p className="page-subtitle">{claims.length} claim{claims.length !== 1 ? "s" : ""} filed</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary p-2"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4" />
            <span className="hidden sm:inline">File a Claim</span>
            <span className="sm:hidden">File</span>
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {claims.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Filed",     value: claims.length, color: "text-slate-200" },
            { label: "Approved",        value: claims.filter(c => ["approved","auto_approved"].includes(c.status)).length, color: "text-success-400" },
            { label: "Under Review",    value: claims.filter(c => c.status === "under_review").length, color: "text-warning-400" },
            { label: "Total Payout",    value: `₹${claims.filter(c => ["approved","auto_approved"].includes(c.status)).reduce((s,c) => s+(c.payout_amount||c.estimated_payout||0),0).toFixed(0)}`, color: "text-brand-400" },
          ].map(item => (
            <div key={item.label} className="card p-4">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{item.label}</p>
              <p className={`text-xl font-display font-bold mt-1 ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Claims list */}
      {loading ? (
        <div className="flex items-center justify-center h-48 text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          <span className="text-sm">Loading claims...</span>
        </div>
      ) : claims.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="w-12 h-12 text-slate-700 mx-auto mb-4" />
          <p className="font-bold text-slate-400 text-sm mb-1">No Claims Yet</p>
          <p className="text-xs text-slate-600 mb-6">
            If you experienced a disruption while working within your zone,<br />
            you can file a claim and we'll verify it automatically.
          </p>
          <button onClick={() => setShowModal(true)} className="btn-primary mx-auto">
            <PlusCircle className="w-4 h-4 mr-2" /> File Your First Claim
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {claims.map((claim, i) => {
            const tc = TRIGGER_CONFIG[claim.disruption_type] || TRIGGER_CONFIG.Unknown;
            const sc = STATUS_CONFIG[claim.status] || STATUS_CONFIG.pending;
            const TrigIcon = tc.icon;
            const StatusIcon = sc.icon;
            const isExpanded = expandedId === claim.id;

            return (
              <motion.div
                key={claim.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card overflow-hidden"
              >
                <button
                  onClick={() => setExpandedId(isExpanded ? null : claim.id)}
                  className="w-full p-4 text-left flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`p-2 rounded-xl border shrink-0 ${tc.color}`}>
                      <TrigIcon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-bold text-slate-200 text-sm truncate">{tc.label}</p>
                      <p className="text-[11px] text-slate-500 truncate">
                        {claim.disruption_hours}h · {new Date(claim.disruption_date).toLocaleDateString("en-IN", { day:"numeric", month:"short" })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-bold text-slate-200">
                        ₹{(claim.payout_amount || claim.estimated_payout || 0).toFixed(0)}
                      </p>
                      <p className="text-[10px] text-slate-500">est. payout</p>
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${sc.color}`}>
                      {sc.label}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </div>
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-border px-4 pb-4 pt-4 space-y-4"
                    >
                      {/* Description */}
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Your Description</p>
                        <p className="text-xs text-slate-400">{claim.description}</p>
                      </div>

                      {/* Auto verification result */}
                      {claim.auto_result && (
                        <div className="bg-surface-2 rounded-xl p-3 space-y-2">
                          <div className="flex items-center justify-between">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Auto Verification</p>
                            <span className={`text-xs font-bold ${AUTO_RESULT_CONF[claim.auto_result]?.color}`}>
                              {AUTO_RESULT_CONF[claim.auto_result]?.label}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400">{claim.auto_reason}</p>

                          {/* Individual checks */}
                          {claim.auto_checks && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-2">
                              {Object.entries(claim.auto_checks).map(([key, val]: [string, any]) => (
                                <div key={key} className="flex items-center gap-2 text-[11px]">
                                  {val.passed === true ? (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-success-400 shrink-0" />
                                  ) : val.passed === false ? (
                                    <XCircle className="w-3.5 h-3.5 text-danger-400 shrink-0" />
                                  ) : (
                                    <AlertCircle className="w-3.5 h-3.5 text-warning-400 shrink-0" />
                                  )}
                                  <span className="text-slate-400 capitalize">
                                    {key.replace(/_/g, " ")}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Fraud/confidence score */}
                          {claim.auto_score !== null && claim.auto_score !== undefined && (
                            <div className="mt-2">
                              <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                                <span>Trust score</span>
                                <span className={claim.auto_score < 0.36 ? "text-success-400" : claim.auto_score < 0.66 ? "text-warning-400" : "text-danger-400"}>
                                  {Math.round((1 - claim.auto_score) * 100)}%
                                </span>
                              </div>
                              <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${claim.auto_score < 0.36 ? "bg-success-500" : claim.auto_score < 0.66 ? "bg-warning-500" : "bg-danger-500"}`}
                                  style={{ width: `${(1 - claim.auto_score) * 100}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* GPS zone check */}
                      <div className="flex items-center gap-2 text-xs">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        {claim.within_15km_radius === true && (
                          <span className="text-success-400">✓ Within 15km zone ({claim.distance_from_zone_km?.toFixed(1)}km)</span>
                        )}
                        {claim.within_15km_radius === false && (
                          <span className="text-danger-400">✗ Outside 15km zone ({claim.distance_from_zone_km?.toFixed(1)}km) — not eligible</span>
                        )}
                        {claim.within_15km_radius === null && (
                          <span className="text-slate-500">Location not provided</span>
                        )}
                      </div>

                      {/* Admin note */}
                      {claim.admin_note && (
                        <div className="bg-brand-500/10 border border-brand-500/20 rounded-xl p-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-brand-400 mb-1">Admin Note</p>
                          <p className="text-xs text-slate-300">{claim.admin_note}</p>
                        </div>
                      )}

                      {/* Payout */}
                      {(claim.status === "approved" || claim.status === "auto_approved") && (
                        <div className="flex items-center gap-3 bg-success-500/10 border border-success-500/20 rounded-xl p-3">
                          <CreditCard className="w-4 h-4 text-success-400 shrink-0" />
                          <div>
                            <p className="text-xs font-bold text-success-400">
                              ₹{(claim.payout_amount || claim.estimated_payout || 0).toFixed(0)} — Payout Approved
                            </p>
                            <p className="text-[10px] text-slate-500">Transfer to your registered UPI ID</p>
                          </div>
                        </div>
                      )}

                      <p className="text-[10px] text-slate-600">
                        Submitted: {new Date(claim.submitted_at).toLocaleString("en-IN")}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* File Claim Modal */}
      <AnimatePresence>
        {showModal && (
          <FileClaimModal
            userId={userId!}
            onClose={() => setShowModal(false)}
            onSuccess={() => { setShowModal(false); fetchClaims(); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── File Claim Modal ───────────────────────────────────────── */
function FileClaimModal({ userId, onClose, onSuccess }: {
  userId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    disruption_type: "rainfall",
    disruption_date: new Date().toISOString().slice(0, 16),
    disruption_hours: "2",
    description: "",
    proof_text: "",
    proof_type: "screenshot",
    declared_was_working: true,
    share_location: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!form.description || form.description.length < 20) {
      setError("Description must be at least 20 characters.");
      return;
    }

    setSubmitting(true);
    setError("");

    let worker_lat: number | undefined;
    let worker_lon: number | undefined;

    // Request location if user agreed
    if (form.share_location && navigator.geolocation) {
      try {
        const pos = await new Promise<GeolocationPosition>((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 })
        );
        worker_lat = pos.coords.latitude;
        worker_lon = pos.coords.longitude;
      } catch {
        // location denied — proceed without
      }
    }

    try {
      const payload: any = {
        disruption_type:    form.disruption_type,
        disruption_date:    new Date(form.disruption_date).toISOString(),
        disruption_hours:   parseFloat(form.disruption_hours),
        description:        form.description,
        proof_text:         form.proof_text || undefined,
        proof_type:         form.proof_type || undefined,
        declared_was_working: form.declared_was_working,
      };
      if (worker_lat) { payload.worker_lat = worker_lat; payload.worker_lon = worker_lon; }

      const res = await apiClient.post("/api/v1/manual-claims/file", payload);
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to submit claim. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const DISRUPTION_TYPES = [
    { value: "rainfall", label: "Heavy Rain" },
    { value: "heat",     label: "Extreme Heat" },
    { value: "aqi",      label: "Poor Air Quality (AQI)" },
    { value: "curfew",   label: "Curfew / Bandh" },
    { value: "outage",   label: "Platform Outage" },
    { value: "other",    label: "Other Disruption" },
  ];

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 z-50"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 24 }}
        className="fixed inset-x-3 top-4 bottom-4 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-[520px] md:top-8 md:bottom-8 bg-[#111827] border border-border rounded-2xl z-50 shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border shrink-0">
          <div>
            <h2 className="font-display font-bold text-slate-100">File a Claim</h2>
            <p className="text-xs text-slate-500 mt-0.5">Describe your disruption — we'll verify it automatically</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        {result ? (
          /* ─ Success / Result view ─ */
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            <div className={`rounded-2xl p-4 border ${
              result.claim?.status === "auto_approved"
                ? "bg-success-500/10 border-success-500/20"
                : result.claim?.status === "auto_denied"
                ? "bg-danger-500/10 border-danger-500/20"
                : "bg-warning-500/10 border-warning-500/20"
            }`}>
              <p className="font-bold text-sm text-slate-200">{result.message}</p>
            </div>

            {/* Verification breakdown */}
            {result.auto_verification && (
              <div className="space-y-3">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Verification Checks</p>
                <div className="space-y-2">
                  {Object.entries(result.auto_verification.checks || {}).map(([key, val]: [string, any]) => (
                    <div key={key} className="flex items-center gap-3 text-sm">
                      {val.passed === true ? (
                        <CheckCircle2 className="w-4 h-4 text-success-400 shrink-0" />
                      ) : val.passed === false ? (
                        <XCircle className="w-4 h-4 text-danger-400 shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-warning-400 shrink-0" />
                      )}
                      <div className="flex-1">
                        <span className="text-slate-300 capitalize">{key.replace(/_/g, " ")}</span>
                        <span className="text-slate-500 text-xs ml-2">{val.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="data-row pt-3 border-t border-border">
                  <span className="text-slate-500 text-sm">Estimated Payout</span>
                  <span className="font-bold text-success-400">₹{result.claim?.estimated_payout?.toFixed(0)}</span>
                </div>
              </div>
            )}

            <button onClick={onSuccess} className="btn-primary w-full mt-2">
              Done
            </button>
          </div>
        ) : (
          /* ─ Form view ─ */
          <div className="flex-1 overflow-y-auto p-5 space-y-4">

            {/* Disruption type */}
            <div>
              <label className="form-label">Type of Disruption</label>
              <div className="grid grid-cols-2 gap-2 mt-1.5">
                {DISRUPTION_TYPES.map(t => (
                  <button
                    key={t.value}
                    onClick={() => setForm(f => ({ ...f, disruption_type: t.value }))}
                    className={`py-2.5 px-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                      form.disruption_type === t.value
                        ? "border-brand-500 bg-brand-500/15 text-brand-300"
                        : "border-border bg-surface-2 text-slate-400 hover:border-slate-500"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Date + Hours */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="form-label">When did it happen?</label>
                <input
                  type="datetime-local"
                  className="form-input mt-1 w-full"
                  value={form.disruption_date}
                  max={new Date().toISOString().slice(0, 16)}
                  onChange={e => setForm(f => ({ ...f, disruption_date: e.target.value }))}
                />
              </div>
              <div>
                <label className="form-label">Hours of work lost</label>
                <select
                  className="form-input mt-1 w-full"
                  value={form.disruption_hours}
                  onChange={e => setForm(f => ({ ...f, disruption_hours: e.target.value }))}
                >
                  {[0.5,1,1.5,2,2.5,3,4,5,6,7,8].map(h => (
                    <option key={h} value={h}>{h} hr{h !== 1 ? "s" : ""}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="form-label">
                Describe what happened <span className="text-danger-400">*</span>
              </label>
              <textarea
                className="form-input mt-1 w-full resize-none"
                rows={3}
                placeholder="e.g. Heavy rain since 6pm, zone flooded, couldn't take deliveries for 3 hours..."
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
              <p className={`text-[10px] mt-1 ${form.description.length < 20 ? "text-slate-600" : "text-success-500"}`}>
                {form.description.length}/20 min chars
              </p>
            </div>

            {/* Proof */}
            <div>
              <label className="form-label">Supporting proof (optional but recommended)</label>
              <select
                className="form-input mt-1 w-full mb-2"
                value={form.proof_type}
                onChange={e => setForm(f => ({ ...f, proof_type: e.target.value }))}
              >
                <option value="screenshot">Screenshot</option>
                <option value="order_history">Order history / app data</option>
                <option value="media">Photo / video</option>
                <option value="other">Other</option>
              </select>
              <textarea
                className="form-input w-full resize-none"
                rows={2}
                placeholder="Describe your proof — e.g. 'Screenshot of app showing no orders from 6–9pm' or 'News link about the curfew'"
                value={form.proof_text}
                onChange={e => setForm(f => ({ ...f, proof_text: e.target.value }))}
              />
            </div>

            {/* Declarations */}
            <div className="space-y-3">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.declared_was_working}
                  onChange={e => setForm(f => ({ ...f, declared_was_working: e.target.checked }))}
                  className="mt-0.5 accent-brand-500"
                />
                <span className="text-sm text-slate-400">
                  I confirm I was actively working (on Zomato/Swiggy) during the disruption period.
                </span>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.share_location}
                  onChange={e => setForm(f => ({ ...f, share_location: e.target.checked }))}
                  className="mt-0.5 accent-brand-500"
                />
                <div>
                  <span className="text-sm text-slate-400">
                    Share my current location for zone verification
                  </span>
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    <MapPin className="w-3 h-3 inline mr-1" />
                    You must be within 15km of your registered zone to be eligible
                  </p>
                </div>
              </label>
            </div>

            {/* Geofence notice */}
            <div className="bg-surface-2 rounded-xl p-3 flex gap-2">
              <AlertCircle className="w-4 h-4 text-warning-400 shrink-0 mt-0.5" />
              <p className="text-xs text-slate-400">
                <span className="font-semibold text-slate-300">15km Zone Rule:</span> Payouts are only approved
                if you were within 15km of your registered work zone during the disruption.
                Share location above to pass this check automatically.
              </p>
            </div>

            {error && (
              <div className="alert-banner danger text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        {!result && (
          <div className="p-4 border-t border-border shrink-0">
            <button
              onClick={handleSubmit}
              disabled={submitting || form.description.length < 20}
              className="btn-primary w-full"
            >
              {submitting ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-2" />Verifying & Submitting...</>
              ) : (
                <><Star className="w-4 h-4 mr-2" />Submit Claim</>
              )}
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
