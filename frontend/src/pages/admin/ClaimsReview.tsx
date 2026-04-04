import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import apiClient from "../../api/client";
import {
  CloudRain, Wind, Thermometer, AlertTriangle, Zap, Shield,
  CheckCircle2, XCircle, Clock, AlertCircle, Loader2, RefreshCw,
  MapPin, ChevronDown, ChevronUp, User, Check, X,
} from "lucide-react";

/* ─── Config ─────────────────────────────────────────────────── */
const TRIGGER_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  rainfall: { icon: CloudRain,     color: "text-blue-400",   label: "Heavy Rain"    },
  heat:     { icon: Thermometer,   color: "text-orange-400", label: "Heat Advisory" },
  aqi:      { icon: Wind,          color: "text-purple-400", label: "AQI Crisis"    },
  curfew:   { icon: AlertTriangle, color: "text-amber-400",  label: "Curfew/Bandh"  },
  outage:   { icon: Zap,           color: "text-rose-400",   label: "Outage"        },
  other:    { icon: Shield,        color: "text-slate-400",  label: "Other"         },
};

const STATUS_INFO: Record<string, { label: string; css: string }> = {
  auto_approved: { label: "Auto Approved",  css: "text-success-400 bg-success-500/10 border-success-500/25" },
  under_review:  { label: "Needs Review",   css: "text-warning-400 bg-warning-500/10 border-warning-500/25" },
  auto_denied:   { label: "Auto Denied",    css: "text-danger-400  bg-danger-500/10  border-danger-500/25"  },
  approved:      { label: "Approved",       css: "text-success-400 bg-success-500/10 border-success-500/25" },
  denied:        { label: "Denied",         css: "text-danger-400  bg-danger-500/10  border-danger-500/25"  },
  pending:       { label: "Pending",        css: "text-slate-400   bg-slate-500/10   border-slate-500/25"   },
};

/* ─── Main Component ─────────────────────────────────────────── */
export default function AdminClaimsReview() {
  const [claims, setClaims] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [deciding, setDeciding] = useState<string | null>(null);

  useEffect(() => { fetchQueue(); }, []);

  const fetchQueue = async () => {
    try {
      const res = await apiClient.get("/api/v1/manual-claims/admin/queue");
      setClaims(res.data.claims || []);
      setSummary(res.data.summary || {});
    } catch {
      setClaims([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleDecision = async (claimId: string, decision: "approved" | "denied", note = "", amount?: number) => {
    setDeciding(claimId);
    try {
      await apiClient.post(`/api/v1/manual-claims/admin/${claimId}/decide`, {
        decision,
        admin_note: note,
        payout_amount: amount,
      });
      await fetchQueue();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Decision failed");
    } finally {
      setDeciding(null);
    }
  };

  const FILTER_TABS = [
    { key: "all",          label: "All",           count: claims.length },
    { key: "under_review", label: "Needs Review",  count: summary.under_review || 0 },
    { key: "auto_approved",label: "Auto Approved", count: summary.auto_approved || 0 },
    { key: "auto_denied",  label: "Auto Denied",   count: summary.auto_denied || 0 },
    { key: "approved",     label: "Approved",      count: summary.approved || 0 },
  ];

  const filtered = filter === "all" ? claims : claims.filter(c => c.status === filter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Claims Review</h1>
          <p className="page-subtitle">Worker-filed manual claims with auto-verification results</p>
        </div>
        <button
          onClick={() => { setRefreshing(true); fetchQueue(); }}
          disabled={refreshing}
          className="btn-secondary p-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: "Total",        value: claims.length,              color: "text-slate-200" },
          { label: "Needs Review", value: summary.under_review  || 0, color: "text-warning-400" },
          { label: "Auto Approved",value: summary.auto_approved || 0, color: "text-success-400" },
          { label: "Auto Denied",  value: summary.auto_denied   || 0, color: "text-danger-400"  },
          { label: "Approved",     value: summary.approved      || 0, color: "text-brand-400"   },
        ].map(k => (
          <div key={k.label} className="card p-4">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{k.label}</p>
            <p className={`text-2xl font-display font-bold mt-1 ${k.color}`}>{k.value}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1.5 overflow-x-auto">
        {FILTER_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === tab.key
                ? "bg-brand-500/20 text-brand-300 border border-brand-500/30"
                : "bg-surface-2 text-slate-500 border border-transparent hover:border-border"
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className="ml-1.5 bg-surface-3 text-slate-400 rounded-full px-1.5 py-0.5 text-[10px]">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Claims list */}
      {loading ? (
        <div className="flex justify-center h-48 items-center text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          <span className="text-sm">Loading claims queue...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle2 className="w-10 h-10 text-success-500/30 mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-500">No claims in this queue</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((claim, i) => {
            const tc = TRIGGER_CONFIG[claim.disruption_type] || TRIGGER_CONFIG.other;
            const sc = STATUS_INFO[claim.status] || STATUS_INFO.pending;
            const TrigIcon = tc.icon;
            const isExpanded = expanded === claim.id;
            const needsDecision = ["under_review", "auto_approved", "auto_denied"].includes(claim.status);

            return (
              <motion.div
                key={claim.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`card overflow-hidden border ${needsDecision && claim.status === "under_review" ? "border-warning-500/20" : "border-border"}`}
              >
                {/* Row header */}
                <button
                  onClick={() => setExpanded(isExpanded ? null : claim.id)}
                  className="w-full p-4 text-left flex items-center gap-3"
                >
                  <TrigIcon className={`w-4 h-4 shrink-0 ${tc.color}`} />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-sm text-slate-200">{claim.worker_name}</span>
                      <span className="text-xs text-slate-500">·</span>
                      <span className="text-xs text-slate-400">{tc.label}</span>
                      <span className="text-xs text-slate-500">·</span>
                      <span className="text-xs text-slate-400">{claim.disruption_hours}h</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {new Date(claim.submitted_at).toLocaleString("en-IN", {
                        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
                      })}
                      {claim.worker_city && <span className="ml-2">· {claim.worker_city}</span>}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-bold text-success-400 text-sm">
                      ₹{(claim.estimated_payout || 0).toFixed(0)}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full border ${sc.css}`}>
                      {sc.label}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </div>
                </button>

                {/* Expanded detail */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-border px-4 pb-4 space-y-4 pt-4"
                    >
                      {/* Worker info */}
                      <div className="flex items-center gap-3 text-sm">
                        <User className="w-4 h-4 text-slate-500 shrink-0" />
                        <div>
                          <span className="text-slate-300 font-semibold">{claim.worker_name}</span>
                          {claim.worker_phone && <span className="text-slate-500 ml-2">{claim.worker_phone}</span>}
                        </div>
                      </div>

                      {/* Description */}
                      <div className="bg-surface-2 rounded-xl p-3">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Worker's Description</p>
                        <p className="text-xs text-slate-300">{claim.description}</p>
                        {claim.proof_text && (
                          <div className="mt-2 pt-2 border-t border-border">
                            <p className="text-[10px] font-bold text-slate-500 mt-1">Proof ({claim.proof_type})</p>
                            <p className="text-xs text-slate-400 mt-1">{claim.proof_text}</p>
                          </div>
                        )}
                      </div>

                      {/* Auto verification checks */}
                      {claim.auto_checks && (
                        <div className="bg-surface-2 rounded-xl p-3">
                          <div className="flex justify-between items-center mb-2">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Auto-Verification Checks</p>
                            <span className={`text-xs font-bold ${
                              claim.auto_result === "auto_approve" ? "text-success-400" :
                              claim.auto_result === "auto_deny" ? "text-danger-400" : "text-warning-400"
                            }`}>
                              Score: {((1 - (claim.auto_score || 0)) * 100).toFixed(0)}% trust
                            </span>
                          </div>
                          <div className="space-y-2">
                            {Object.entries(claim.auto_checks).map(([key, val]: [string, any]) => (
                              <div key={key} className="flex items-center justify-between text-xs">
                                <div className="flex items-center gap-2">
                                  {val.passed === true  ? <CheckCircle2 className="w-3.5 h-3.5 text-success-400 shrink-0" /> :
                                   val.passed === false ? <XCircle className="w-3.5 h-3.5 text-danger-400 shrink-0" /> :
                                                         <AlertCircle className="w-3.5 h-3.5 text-warning-400 shrink-0" />}
                                  <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}</span>
                                </div>
                                <span className="text-slate-500 text-[10px] text-right">{val.detail}</span>
                              </div>
                            ))}
                          </div>
                          {claim.auto_reason && (
                            <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-border">{claim.auto_reason}</p>
                          )}
                        </div>
                      )}

                      {/* GPS zone */}
                      <div className="flex items-center gap-2 text-xs">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        {claim.within_15km_radius === true  && <span className="text-success-400">Within 15km zone ({claim.distance_from_zone_km?.toFixed(1)}km away)</span>}
                        {claim.within_15km_radius === false && <span className="text-danger-400">⚠ Outside 15km zone ({claim.distance_from_zone_km?.toFixed(1)}km away)</span>}
                        {claim.within_15km_radius === null  && <span className="text-slate-500">Location not shared by worker</span>}
                      </div>

                      {/* Plan */}
                      <div className="data-row text-xs">
                        <span className="text-slate-500">Plan</span>
                        <span className="capitalize font-semibold text-slate-300">{claim.plan_name || "basic"}</span>
                      </div>

                      {/* Admin note (if already decided) */}
                      {claim.admin_note && (
                        <div className="bg-brand-500/10 border border-brand-500/20 rounded-xl p-3">
                          <p className="text-[10px] font-bold text-brand-400 mb-1">Admin Note</p>
                          <p className="text-xs text-slate-300">{claim.admin_note}</p>
                        </div>
                      )}

                      {/* Decision panel */}
                      {needsDecision && !["approved", "denied"].includes(claim.status) && (
                        <DecisionPanel
                          claim={claim}
                          onDecide={handleDecision}
                          loading={deciding === claim.id}
                        />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Decision Panel ─────────────────────────────────────────── */
function DecisionPanel({ claim, onDecide, loading }: {
  claim: any;
  onDecide: (id: string, decision: "approved" | "denied", note?: string, amount?: number) => void;
  loading: boolean;
}) {
  const [note, setNote] = useState("");
  const [amount, setAmount] = useState<string>(claim.estimated_payout?.toFixed(0) || "");

  return (
    <div className="bg-surface-2 rounded-xl p-4 space-y-3 border border-border">
      <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Admin Decision Required</p>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="form-label">Payout Amount (₹)</label>
          <input
            className="form-input mt-1 w-full"
            type="number"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder={claim.estimated_payout?.toFixed(0)}
          />
        </div>
        <div>
          <label className="form-label">Estimated</label>
          <p className="text-lg font-bold text-success-400 mt-2">₹{claim.estimated_payout?.toFixed(0)}</p>
        </div>
      </div>

      <div>
        <label className="form-label">Admin Note (optional)</label>
        <textarea
          className="form-input mt-1 w-full resize-none text-xs"
          rows={2}
          placeholder="Add context for the worker..."
          value={note}
          onChange={e => setNote(e.target.value)}
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => onDecide(claim.id, "denied", note)}
          disabled={loading}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold bg-danger-500/10 text-danger-400 border border-danger-500/20 hover:bg-danger-500/20 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
          Deny
        </button>
        <button
          onClick={() => onDecide(claim.id, "approved", note, amount ? parseFloat(amount) : undefined)}
          disabled={loading}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold bg-success-500/10 text-success-400 border border-success-500/20 hover:bg-success-500/20 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          Approve
        </button>
      </div>
    </div>
  );
}
