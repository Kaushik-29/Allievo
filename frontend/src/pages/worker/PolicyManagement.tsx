import { useEffect, useState } from "react";
import { useAuthStore } from "../../stores/authStore";
import { usePlanStore } from "../../stores/planStore";
import apiClient from "../../api/client";
import {
  Shield, Zap, Crown, Loader2, CheckCircle2,
  CloudRain, Thermometer, Wind, AlertTriangle, RefreshCw, LayoutGrid,
} from "lucide-react";
import { Link } from "react-router-dom";

/* ─── Plan-specific content ──────────────── */
const PLAN_DETAILS: Record<string, {
  icon: React.ElementType;
  gradient: string;
  accentColor: string;
  coverageLabel: string;
  triggers: { name: string; condition: string; payout: string; icon: React.ElementType }[];
  perks: string[];
}> = {
  basic: {
    icon: Shield,
    gradient: "from-blue-600 to-blue-800",
    accentColor: "text-blue-400",
    coverageLabel: "2 days × 2 hrs",
    triggers: [
      { name: "Monsoon Rainfall", condition: ">64mm/hr in your zone", payout: "Up to ₹160", icon: CloudRain },
      { name: "Heat Wave",        condition: ">44°C sustained 4hrs",   payout: "Up to ₹160", icon: Thermometer },
      { name: "AQI Crisis",       condition: "AQI >400 sustained 4hrs", payout: "Up to ₹160", icon: Wind },
    ],
    perks: [
      "Manual or auto-trigger claim",
      "You choose which 2 days to cover",
      "Standard fraud review (48hr)",
    ],
  },
  dynamic: {
    icon: Zap,
    gradient: "from-brand-600 to-brand-800",
    accentColor: "text-brand-400",
    coverageLabel: "3 days × 4 hrs",
    triggers: [
      { name: "Monsoon Rainfall",  condition: ">64mm/hr in your zone",     payout: "Up to ₹480", icon: CloudRain },
      { name: "Heat Wave",         condition: ">44°C sustained 4hrs",       payout: "Up to ₹408", icon: Thermometer },
      { name: "AQI Crisis",        condition: "AQI >400 sustained 4hrs",    payout: "Up to ₹408", icon: Wind },
      { name: "Curfew / Bandh",    condition: "NDMA alert + 80% order drop",payout: "Up to ₹480", icon: AlertTriangle },
    ],
    perks: [
      "Fully automatic payouts",
      "Premium adjusts every Sunday via live weather",
      "Standard fraud review (48hr)",
    ],
  },
  premium: {
    icon: Crown,
    gradient: "from-amber-600 to-amber-800",
    accentColor: "text-amber-400",
    coverageLabel: "4 days × 6 hrs",
    triggers: [
      { name: "Monsoon Rainfall",  condition: ">64mm/hr in your zone",     payout: "Up to ₹1,152", icon: CloudRain },
      { name: "Heat Wave",         condition: ">44°C sustained 4hrs",       payout: "Up to ₹979",  icon: Thermometer },
      { name: "AQI Crisis",        condition: "AQI >400 sustained 4hrs",    payout: "Up to ₹979",  icon: Wind },
      { name: "Curfew / Bandh",    condition: "NDMA alert + 80% order drop",payout: "Up to ₹1,152",icon: AlertTriangle },
      { name: "Platform Outage",   condition: ">45min Zomato/Swiggy down",  payout: "Up to ₹806",  icon: Zap },
    ],
    perks: [
      "Fully automatic payouts",
      "Priority fraud review (12hr)",
      "Maximum weekly coverage — 24 hrs",
    ],
  },
};

export default function PolicyManagement() {
  const { userId } = useAuthStore();
  const enrolledAt = usePlanStore(s => s.enrolledAt);
  const [enrollment, setEnrollment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Re-fetch whenever a new plan is enrolled from Plans page
  useEffect(() => {
    if (!userId) return;
    fetchPlan();
  }, [userId, enrolledAt]);

  const fetchPlan = async () => {
    try {
      const res = await apiClient.get(`/api/v1/plans/worker/${userId}`);
      setEnrollment(res.data);
    } catch {
      setEnrollment(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-6 h-6 text-brand-400 animate-spin" />
      </div>
    );
  }

  // No plan enrolled
  if (!enrollment) {
    return (
      <div className="space-y-4">
        <div>
          <h1 className="page-title">My Policy</h1>
          <p className="page-subtitle">Coverage details based on your active plan</p>
        </div>
        <div className="card p-12 text-center space-y-4">
          <Shield className="w-12 h-12 text-slate-700 mx-auto" />
          <p className="font-bold text-slate-400">No Active Plan</p>
          <p className="text-sm text-slate-600">
            You haven't enrolled in a plan yet. Choose one to activate your income protection.
          </p>
          <Link to="/worker/plans" className="btn-primary inline-flex items-center gap-2 mx-auto">
            <LayoutGrid className="w-4 h-4" /> Choose a Plan
          </Link>
        </div>
      </div>
    );
  }

  const planName: string = enrollment.enrollment?.plan_name || "basic";
  const planDef = enrollment.plan;
  const weeklyPremium: number = enrollment.enrollment?.weekly_premium || 0;
  const details = PLAN_DETAILS[planName] || PLAN_DETAILS.basic;
  const PlanIcon = details.icon;
  const eligibleForPayout: boolean = enrollment.enrollment?.eligible_for_payout;
  const waitingEndsAt: string | null = enrollment.enrollment?.waiting_ends_at;
  const thisWeek = enrollment.this_week;

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="page-title">My Policy</h1>
        <p className="page-subtitle">Coverage details based on your active plan</p>
      </div>

      {/* Hero card */}
      <div className={`relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br ${details.gradient}`}>
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "radial-gradient(circle at 80% 20%, white 0%, transparent 60%)" }} />

        <div className="relative z-10 flex items-start justify-between mb-5">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-widest bg-white/20 border border-white/30 text-white px-2 py-0.5 rounded-full">
                Active Policy
              </span>
              <span className="text-[10px] font-bold uppercase tracking-widest bg-white/20 border border-white/30 text-white px-2 py-0.5 rounded-full capitalize">
                {planName} plan
              </span>
            </div>
            <p className="text-4xl font-display font-bold text-white">
              ₹{weeklyPremium.toFixed(0)}
              <span className="text-white/60 text-lg font-medium">/week</span>
            </p>
            {planName === "dynamic" && thisWeek && (
              <p className="text-white/70 text-xs mt-1">
                This week's multiplier: {thisWeek.multiplier_applied}× · {thisWeek.plain_reason}
              </p>
            )}
          </div>
          <div className="w-12 h-12 rounded-2xl bg-white/15 flex items-center justify-center border border-white/20">
            <PlanIcon className="w-6 h-6 text-white" />
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-3 gap-3">
          {[
            { label: "Plan",         value: planName.charAt(0).toUpperCase() + planName.slice(1) },
            { label: "Max Payout",   value: `₹${planDef?.max_payout?.toLocaleString() || "—"}` },
            { label: "Coverage",     value: details.coverageLabel },
          ].map(item => (
            <div key={item.label} className="bg-white/10 rounded-xl px-3 py-2.5 backdrop-blur-sm border border-white/10">
              <p className="text-white/60 text-[10px] font-semibold uppercase tracking-wider">{item.label}</p>
              <p className="text-white text-sm font-bold mt-0.5">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Waiting period notice */}
      {!eligibleForPayout && waitingEndsAt && (
        <div className="card p-4 border border-warning-500/20 bg-warning-500/5 flex items-start gap-3">
          <RefreshCw className="w-4 h-4 text-warning-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-warning-400">28-Day Waiting Period Active</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Payout eligibility begins on{" "}
              <span className="text-slate-300 font-medium">
                {new Date(waitingEndsAt).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* What's covered */}
      <div>
        <p className="section-header">
          What's Covered — {planName.charAt(0).toUpperCase() + planName.slice(1)} Plan
        </p>
        <div className="card divide-y divide-border">
          {details.triggers.map(row => {
            const TrigIcon = row.icon;
            return (
              <div key={row.name} className="flex items-center justify-between px-5 py-4 gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <TrigIcon className={`w-4 h-4 shrink-0 ${details.accentColor}`} />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{row.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{row.condition}</p>
                  </div>
                </div>
                <span className="badge-brand text-[10px] shrink-0">{row.payout}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Plan perks */}
      <div className="card p-5 space-y-3">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Plan Benefits</p>
        <div className="space-y-2">
          {details.perks.map(perk => (
            <div key={perk} className="flex items-center gap-2.5 text-sm text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-success-400 shrink-0" />
              {perk}
            </div>
          ))}
        </div>
      </div>

      {/* Change plan CTA */}
      <div className="card p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-300">Want more coverage?</p>
          <p className="text-xs text-slate-500 mt-0.5">Switch plans any time — effective next Monday</p>
        </div>
        <Link to="/worker/plans" className="btn-primary text-sm shrink-0">
          View Plans
        </Link>
      </div>
    </div>
  );
}
