import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Zap, Crown, Check, ChevronRight,
  TrendingUp, Loader2, Info, X, CloudRain, Thermometer, Wind,
  CreditCard, QrCode, CheckCircle2, Lock, ArrowLeft,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { usePlanStore } from '../../stores/planStore';
import apiClient from '../../api/client';

/* ─── Types ─────────────────────────────────────────────────────── */
interface ForecastBars {
  rain_bar: number; temp_bar: number; aqi_bar: number;
  multiplier: number; plain_reason: string; current_premium: number;
}

interface Plan {
  name: string; label: string; badge_color: string;
  days_per_week: number; hours_per_day: number; covered_hours: number;
  plan_value: number; max_payout: number; weekly_premium: number;
  premium_rate: number | null; claim_mode: string; claim_label: string;
  description: string; forecast_bars: ForecastBars | null; popular?: boolean;
}

/* ─── Plan config ─────────────────────────────────────────────── */
const PLAN_CONFIG: Record<string, {
  icon: React.ElementType; gradient: string; ring: string; badge: string; features: string[];
}> = {
  basic: {
    icon: Shield,
    gradient: 'from-blue-600/20 to-blue-800/5',
    ring: 'border-blue-500/30',
    badge: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
    features: ['2 days × 2 hrs coverage','Choose your claim window','Manual or auto-trigger','₹320/week max payout'],
  },
  dynamic: {
    icon: Zap,
    gradient: 'from-brand-600/20 to-brand-900/5',
    ring: 'border-brand-500/40',
    badge: 'bg-brand-500/15 text-brand-400 border-brand-500/20',
    features: ['3 days × 4 hrs coverage','Fully automatic payouts','Premium updates weekly','₹960/week max payout'],
  },
  premium: {
    icon: Crown,
    gradient: 'from-amber-600/20 to-amber-900/5',
    ring: 'border-amber-500/30',
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    features: ['4 days × 6 hrs coverage','Fully automatic payouts','Priority fraud review','₹1,920/week max payout'],
  },
};

/* ─── UPI QR (base64 placeholder that looks like a real QR) ──── */
const MOCK_QR_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" fill="%23111827"/>
  <rect x="10" y="10" width="60" height="60" fill="none" stroke="%236366f1" stroke-width="4"/>
  <rect x="20" y="20" width="40" height="40" fill="%236366f1"/>
  <rect x="130" y="10" width="60" height="60" fill="none" stroke="%236366f1" stroke-width="4"/>
  <rect x="140" y="20" width="40" height="40" fill="%236366f1"/>
  <rect x="10" y="130" width="60" height="60" fill="none" stroke="%236366f1" stroke-width="4"/>
  <rect x="20" y="140" width="40" height="40" fill="%236366f1"/>
  <rect x="85" y="10" width="10" height="10" fill="%236366f1"/>
  <rect x="100" y="10" width="10" height="10" fill="%236366f1"/>
  <rect x="85" y="25" width="20" height="10" fill="%236366f1"/>
  <rect x="85" y="85" width="10" height="10" fill="%236366f1"/>
  <rect x="100" y="85" width="45" height="10" fill="%236366f1"/>
  <rect x="130" y="100" width="15" height="10" fill="%236366f1"/>
  <rect x="150" y="100" width="10" height="10" fill="%236366f1"/>
  <rect x="130" y="115" width="30" height="10" fill="%236366f1"/>
  <rect x="85" y="115" width="30" height="10" fill="%236366f1"/>
  <rect x="100" y="130" width="10" height="40" fill="%236366f1"/>
  <rect x="85" y="150" width="10" height="20" fill="%236366f1"/>
  <rect x="115" y="140" width="20" height="10" fill="%236366f1"/>
  <rect x="140" y="140" width="50" height="10" fill="%236366f1"/>
  <rect x="155" y="155" width="15" height="15" fill="%236366f1"/>
  <rect x="140" y="170" width="50" height="10" fill="%236366f1"/>
</svg>`;

/* ─── Main Component ─────────────────────────────────────────── */
export default function Plans() {
  const { userId } = useAuthStore();
  const setCurrentPlan = usePlanStore(s => s.setCurrentPlan);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPlan, setLocalPlan] = useState<string | null>(null);
  const [showModal, setShowModal] = useState<Plan | null>(null);
  const [enrolled, setEnrolled] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => { fetchPlans(); fetchCurrentPlan(); }, []);

  const fetchPlans = async () => {
    try {
      const res = await apiClient.get('/api/v1/plans');
      setPlans(res.data.plans || []);
    } catch { setError('Failed to load plans.'); }
    finally { setLoading(false); }
  };

  const fetchCurrentPlan = async () => {
    if (!userId) return;
    try {
      const res = await apiClient.get(`/api/v1/plans/worker/${userId}`);
      const name = res.data.enrollment?.plan_name || null;
      setLocalPlan(name);
      if (name) setCurrentPlan(name); // sync store on load too
    } catch { /* no enrollment */ }
  };

  const handleEnroll = async (planName: string) => {
    if (!userId) return;
    try {
      await apiClient.post('/api/v1/plans/enroll', { worker_id: userId, plan_name: planName });
      setCurrentPlan(planName);   // ← global store — Dashboard & Policy react instantly
      setLocalPlan(planName);     // ← local card highlight
      setEnrolled(planName);
      setShowModal(null);
      fetchPlans();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Enrollment failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title">Choose Your Plan</h1>
        <p className="page-subtitle">Select coverage that fits your work pattern. Switch any time — effective next Monday.</p>
      </div>

      {/* Baseline */}
      <div className="card p-4 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-500/15 flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Your Baseline</p>
            <p className="text-sm font-semibold text-slate-200">₹80/hr · 8 hrs/day · 6 days/wk = ₹3,840/wk</p>
          </div>
        </div>
        <p className="ml-auto text-xs text-slate-500 hidden sm:block">Premiums calculated on your hourly rate</p>
      </div>

      {/* Success banner */}
      <AnimatePresence>
        {enrolled && (
          <motion.div initial={{ opacity:0, y:-8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0, y:-8 }}
            className="alert-banner success">
            <Check className="w-4 h-4 shrink-0" />
            <span className="font-semibold">Enrolled in {enrolled.charAt(0).toUpperCase()+enrolled.slice(1)} plan! Check My Policy for coverage details.</span>
            <button onClick={() => setEnrolled(null)} className="ml-auto"><X className="w-4 h-4" /></button>
          </motion.div>
        )}
      </AnimatePresence>

      {error && <div className="alert-banner danger text-sm"><span>{error}</span></div>}

      {/* Plan Cards */}
      {loading ? (
        <div className="flex items-center justify-center h-48 text-slate-600">
          <Loader2 className="w-6 h-6 animate-spin mr-2" /><span className="text-sm">Loading plans...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map((plan, i) => {
            const cfg = PLAN_CONFIG[plan.name];
            const Icon = cfg.icon;
            const isCurrentPlan = currentPlan === plan.name;

            return (
              <motion.div key={plan.name} initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }}
                transition={{ delay: i * 0.1 }}
                className={`relative card p-5 flex flex-col border bg-gradient-to-br ${cfg.gradient} ${
                  isCurrentPlan ? cfg.ring+' border-2' : 'border-border'}`}>

                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                    <span className="badge-brand text-[10px] font-bold px-3 py-1 shadow-glow-sm">MOST POPULAR</span>
                  </div>
                )}
                {isCurrentPlan && (
                  <div className="absolute top-4 right-4">
                    <span className="badge-success text-[10px] font-bold">Active</span>
                  </div>
                )}

                {/* Plan header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${cfg.badge}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-slate-100 text-base">{plan.label}</h3>
                    <p className="text-[11px] text-slate-500 capitalize">{plan.claim_label}</p>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {[['Days', plan.days_per_week], ['Hrs/day', plan.hours_per_day], ['Total', `${plan.covered_hours}h`]].map(([l, v]) => (
                    <div key={l} className="bg-surface-2 rounded-lg p-2 text-center">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide">{l}</p>
                      <p className="text-lg font-bold text-slate-200">{v}</p>
                    </div>
                  ))}
                </div>

                {/* Dynamic forecast bars */}
                {plan.name === 'dynamic' && plan.forecast_bars && (
                  <div className="mb-4 space-y-2 bg-surface-2 rounded-xl p-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Week Forecast</p>
                      <span className="text-[11px] font-bold text-brand-400">{plan.forecast_bars.multiplier.toFixed(2)}× this week</span>
                    </div>
                    <ForecastBar icon={CloudRain}   label="Rain" value={plan.forecast_bars.rain_bar} color="bg-blue-500" />
                    <ForecastBar icon={Thermometer} label="Heat" value={plan.forecast_bars.temp_bar} color="bg-orange-500" />
                    <ForecastBar icon={Wind}        label="AQI"  value={plan.forecast_bars.aqi_bar}  color="bg-purple-500" />
                    {plan.forecast_bars.plain_reason && (
                      <p className="text-[10px] text-slate-500 mt-1">{plan.forecast_bars.plain_reason}</p>
                    )}
                  </div>
                )}

                {/* Premium & payout */}
                <div className="mb-4">
                  <div className="flex items-baseline justify-between">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Weekly Premium</p>
                      <div className="flex items-baseline gap-1 mt-0.5">
                        <span className="text-2xl font-display font-bold text-slate-100">₹{plan.weekly_premium.toFixed(0)}</span>
                        <span className="text-xs text-slate-500">/week</span>
                        {plan.name === 'dynamic' && <span className="text-[10px] text-brand-400 ml-1">• varies</span>}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Max Payout</p>
                      <p className="text-lg font-bold text-success-400 mt-0.5">₹{plan.max_payout.toFixed(0)}</p>
                    </div>
                  </div>
                </div>

                {/* Features */}
                <ul className="space-y-1.5 mb-5 flex-1">
                  {cfg.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-xs text-slate-400">
                      <Check className="w-3.5 h-3.5 text-success-400 shrink-0" />{f}
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <button
                  onClick={() => isCurrentPlan ? null : setShowModal(plan)}
                  disabled={isCurrentPlan}
                  className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    isCurrentPlan
                      ? 'bg-success-500/10 text-success-400 cursor-default border border-success-500/20'
                      : 'btn-primary'
                  }`}
                >
                  {isCurrentPlan ? <><Check className="w-4 h-4" /> Current Plan</> : <>Choose {plan.label} <ChevronRight className="w-4 h-4" /></>}
                </button>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Comparison table */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h2 className="text-sm font-bold text-slate-300">Plan Comparison</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-[11px] font-bold uppercase tracking-widest text-slate-500">Feature</th>
                <th className="text-center py-3 px-4 text-[11px] font-bold uppercase tracking-widest text-blue-400">Basic</th>
                <th className="text-center py-3 px-4 text-[11px] font-bold uppercase tracking-widest text-brand-400">Dynamic</th>
                <th className="text-center py-3 px-4 text-[11px] font-bold uppercase tracking-widest text-amber-400">Premium</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {[
                ['Covered Hours/Week','4 hrs','12 hrs','24 hrs'],
                ['Max Weekly Payout','₹320','₹960','₹1,920'],
                ['Weekly Premium','₹48 (fixed)','Weather-based','₹576 (fixed)'],
                ['Claim Mode','Manual/Auto','Automatic','Automatic'],
                ['Waiting Period','28 days','28 days','28 days'],
                ['Fraud Review','Standard','Standard','Priority'],
              ].map(row => (
                <tr key={row[0]} className="hover:bg-white/2">
                  <td className="py-3 px-4 text-slate-400 font-medium">{row[0]}</td>
                  <td className="py-3 px-4 text-center text-slate-300">{row[1]}</td>
                  <td className="py-3 px-4 text-center text-slate-300">{row[2]}</td>
                  <td className="py-3 px-4 text-center text-slate-300">{row[3]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dynamic pricing explainer */}
      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-brand-400 shrink-0" />
          <h3 className="text-sm font-bold text-slate-200">How Dynamic Pricing Works</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-400">
          {[
            ['Every Sunday at 11 PM','We fetch a 7-day weather forecast for your zone using OpenWeatherMap.'],
            ['Risk Calculation','Rain (50%) + Temperature (30%) + AQI (20%) → Week risk score (0.05–0.95)'],
            ['Multiplier: 1.05×–2.00×','Applied to ₹48 base. Always at least 5% above Basic. Capped at ₹240.'],
          ].map(([title, desc]) => (
            <div key={title} className="bg-surface-2 rounded-xl p-3">
              <p className="font-bold text-slate-300 mb-1">{title}</p>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Modal */}
      <AnimatePresence>
        {showModal && (
          <PaymentModal
            plan={showModal}
            onClose={() => setShowModal(null)}
            onSuccess={() => handleEnroll(showModal.name)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Payment Modal ───────────────────────────────────────────── */
type PayStep = 'select' | 'qr' | 'card' | 'success';

function PaymentModal({ plan, onClose, onSuccess }: {
  plan: Plan; onClose: () => void; onSuccess: () => void;
}) {
  const cfg = PLAN_CONFIG[plan.name];
  const PlanIcon = cfg.icon;
  const [step, setStep] = useState<PayStep>('select');
  const [processing, setProcessing] = useState(false);
  const [card, setCard] = useState({ number: '', expiry: '', cvv: '', name: '' });

  const simulatePay = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      setStep('success');
      setTimeout(() => onSuccess(), 1800);
    }, 2200);
  };

  const formatCardNumber = (v: string) =>
    v.replace(/\D/g,'').slice(0,16).replace(/(.{4})/g,'$1 ').trim();

  const formatExpiry = (v: string) => {
    const d = v.replace(/\D/g,'').slice(0,4);
    return d.length > 2 ? d.slice(0,2)+'/'+d.slice(2) : d;
  };

  return (
    <>
      <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
        className="fixed inset-0 bg-black/70 z-50" onClick={onClose} />
      <motion.div
        initial={{ opacity:0, scale:0.97, y:10 }}
        animate={{ opacity:1, scale:1, y:0 }}
        exit={{ opacity:0, scale:0.97, y:10 }}
        transition={{ type: 'spring', stiffness: 320, damping: 30 }}
        transformTemplate={(_t, generated) => `translate(-50%, -50%) ${generated}`}
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          width: 'min(calc(100vw - 24px), 460px)',
          maxHeight: '86vh',
          zIndex: 9999,
        }}
        className="bg-[#111827] border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden">

        {/* Header — back arrow LEFT, title CENTER-LEFT, close RIGHT */}
        <div className="flex items-center gap-3 p-4 border-b border-border shrink-0">
          {/* Left slot: back arrow (sub-steps) or plan icon (select step) */}
          {step !== 'select' && step !== 'success' ? (
            <button onClick={() => setStep('select')}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-colors shrink-0">
              <ArrowLeft className="w-4 h-4" />
            </button>
          ) : (
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center border shrink-0 ${cfg.badge}`}>
              <PlanIcon className="w-4 h-4" />
            </div>
          )}

          {/* Title */}
          <div className="flex-1 min-w-0">
            <p className="font-display font-bold text-slate-100 text-sm leading-tight">
              {step === 'select' ? `Subscribe · ${plan.label} Plan` :
               step === 'qr'     ? 'Pay via UPI / QR Code' :
               step === 'card'   ? 'Pay via Debit / Credit Card' : ''}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              ₹{plan.weekly_premium.toFixed(0)}/week · {plan.covered_hours} hrs covered
            </p>
          </div>

          {/* Right slot: close (always visible except success) */}
          {step !== 'success' && (
            <button onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors shrink-0">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">

          {/* ── Step 1: Select payment method ── */}
          {step === 'select' && (
            <div className="p-5 space-y-4">
              {/* Plan summary */}
              <div className="bg-surface-2 rounded-xl p-4 space-y-2">
                <div className="data-row text-sm">
                  <span className="text-slate-500">Plan</span>
                  <span className="font-bold text-slate-200 capitalize">{plan.name}</span>
                </div>
                <div className="data-row text-sm">
                  <span className="text-slate-500">Coverage</span>
                  <span className="font-bold text-slate-200">{plan.covered_hours} hrs/week</span>
                </div>
                <div className="data-row text-sm">
                  <span className="text-slate-500">Max Payout</span>
                  <span className="font-bold text-success-400">₹{plan.max_payout.toFixed(0)}</span>
                </div>
                <div className="data-row text-sm border-t border-border pt-2">
                  <span className="text-slate-400 font-semibold">Weekly Premium</span>
                  <span className="text-xl font-display font-bold text-slate-100">₹{plan.weekly_premium.toFixed(0)}</span>
                </div>
              </div>

              <p className="text-xs text-slate-500 text-center">Choose your payment method</p>

              {/* Payment method buttons */}
              <button onClick={() => setStep('qr')}
                className="w-full flex items-center gap-4 p-4 rounded-xl border border-border bg-surface-2 hover:border-brand-500/40 hover:bg-brand-500/5 transition-all group">
                <div className="w-11 h-11 rounded-xl bg-brand-500/15 border border-brand-500/20 flex items-center justify-center shrink-0">
                  <QrCode className="w-5 h-5 text-brand-400" />
                </div>
                <div className="text-left flex-1">
                  <p className="font-semibold text-slate-200 text-sm">UPI / QR Code</p>
                  <p className="text-xs text-slate-500 mt-0.5">Scan with any UPI app — GPay, PhonePe, Paytm</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-brand-400 transition-colors" />
              </button>

              <button onClick={() => setStep('card')}
                className="w-full flex items-center gap-4 p-4 rounded-xl border border-border bg-surface-2 hover:border-brand-500/40 hover:bg-brand-500/5 transition-all group">
                <div className="w-11 h-11 rounded-xl bg-blue-500/15 border border-blue-500/20 flex items-center justify-center shrink-0">
                  <CreditCard className="w-5 h-5 text-blue-400" />
                </div>
                <div className="text-left flex-1">
                  <p className="font-semibold text-slate-200 text-sm">Debit / Credit Card</p>
                  <p className="text-xs text-slate-500 mt-0.5">Visa, Mastercard, RuPay accepted</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-brand-400 transition-colors" />
              </button>

              <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-600 pt-1">
                <Lock className="w-3 h-3" />
                <span>256-bit SSL encrypted · Powered by Razorpay</span>
              </div>
            </div>
          )}

          {/* ── Step 2a: QR Code ── */}
          {step === 'qr' && (
            <div className="p-5 space-y-4">
              <div className="bg-surface-2 rounded-2xl p-5 flex flex-col items-center gap-3">
                <img src={MOCK_QR_SVG} alt="UPI QR Code" className="w-44 h-44 rounded-xl border border-border" />
                <div className="text-center">
                  <p className="text-xs text-slate-400">Scan with <span className="text-slate-200 font-semibold">GPay, PhonePe, or Paytm</span></p>
                  <p className="text-lg font-display font-bold text-slate-100 mt-1">₹{plan.weekly_premium.toFixed(0)}</p>
                  <p className="text-[10px] text-slate-500 font-mono mt-0.5">allievo@razorpay</p>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                {[
                  'Open your UPI app and tap "Scan QR"',
                  `Enter amount ₹${plan.weekly_premium.toFixed(0)} if not auto-filled`,
                  'Confirm payment with your UPI PIN',
                  'Come back here and click "I\'ve Paid"',
                ].map((step, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-slate-400">
                    <span className="w-4 h-4 rounded-full bg-brand-500/20 text-brand-400 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">{i+1}</span>
                    {step}
                  </div>
                ))}
              </div>

              <button onClick={simulatePay} disabled={processing}
                className="btn-primary w-full mt-2">
                {processing ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Verifying Payment...</> : "✓ I've Paid"}
              </button>
            </div>
          )}

          {/* ── Step 2b: Card ── */}
          {step === 'card' && (
            <div className="p-5 space-y-4">
              {/* Card preview */}
              <div className={`rounded-2xl p-5 bg-gradient-to-br ${PLAN_CONFIG[plan.name].gradient} border border-white/10 relative overflow-hidden`}>
                <div className="absolute inset-0 opacity-20" style={{ backgroundImage:"radial-gradient(circle at 80% 20%, white, transparent 60%)" }} />
                <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest relative z-10">Card Number</p>
                <p className="text-slate-200 font-mono text-lg mt-1 relative z-10 tracking-widest">
                  {card.number || '•••• •••• •••• ••••'}
                </p>
                <div className="flex justify-between mt-3 relative z-10">
                  <div>
                    <p className="text-slate-500 text-[10px]">Cardholder</p>
                    <p className="text-slate-300 text-xs font-semibold">{card.name || 'YOUR NAME'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-500 text-[10px]">Expires</p>
                    <p className="text-slate-300 text-xs font-semibold">{card.expiry || 'MM/YY'}</p>
                  </div>
                </div>
              </div>

              {/* Form */}
              <div className="space-y-3">
                <div>
                  <label className="form-label">Cardholder Name</label>
                  <input className="form-input mt-1 w-full" placeholder="As printed on card"
                    value={card.name} onChange={e => setCard(c => ({...c, name: e.target.value.toUpperCase()}))} />
                </div>
                <div>
                  <label className="form-label">Card Number</label>
                  <input className="form-input mt-1 w-full font-mono tracking-widest" placeholder="1234 5678 9012 3456"
                    maxLength={19} value={card.number}
                    onChange={e => setCard(c => ({...c, number: formatCardNumber(e.target.value)}))} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="form-label">Expiry</label>
                    <input className="form-input mt-1 w-full font-mono" placeholder="MM/YY"
                      maxLength={5} value={card.expiry}
                      onChange={e => setCard(c => ({...c, expiry: formatExpiry(e.target.value)}))} />
                  </div>
                  <div>
                    <label className="form-label">CVV</label>
                    <input className="form-input mt-1 w-full font-mono" placeholder="•••" type="password"
                      maxLength={3} value={card.cvv}
                      onChange={e => setCard(c => ({...c, cvv: e.target.value.replace(/\D/g,'').slice(0,3)}))} />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-600">
                <Lock className="w-3 h-3" />
                <span>Your card details are encrypted and never stored</span>
              </div>

              <button
                onClick={simulatePay}
                disabled={processing || !card.number || !card.expiry || !card.cvv || !card.name}
                className="btn-primary w-full">
                {processing ? (
                  <><Loader2 className="w-4 h-4 animate-spin mr-2" />Processing...</>
                ) : (
                  <>Pay ₹{plan.weekly_premium.toFixed(0)} &amp; Subscribe</>
                )}
              </button>
            </div>
          )}

          {/* ── Step 3: Success ── */}
          {step === 'success' && (
            <div className="p-8 flex flex-col items-center justify-center gap-4 text-center min-h-[280px]">
              <motion.div initial={{ scale:0 }} animate={{ scale:1 }} transition={{ type:'spring', stiffness:200 }}
                className="w-20 h-20 rounded-full bg-success-500/15 border-2 border-success-500/30 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-success-400" />
              </motion.div>
              <div>
                <p className="text-xl font-display font-bold text-slate-100">Payment Successful!</p>
                <p className="text-sm text-slate-400 mt-1">
                  You're now enrolled in the <span className="text-slate-200 font-semibold capitalize">{plan.name}</span> plan
                </p>
              </div>
              <p className="text-xs text-slate-500">Activating your coverage...</p>
              <Loader2 className="w-5 h-5 text-brand-400 animate-spin" />
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}

/* ─── Forecast Bar ──────────────────────────────────────────── */
function ForecastBar({ icon: Icon, label, value, color }: {
  icon: React.ElementType; label: string; value: number; color: string;
}) {
  const pct = Math.round(value * 100);
  const lvl = pct < 30 ? 'Low' : pct < 70 ? 'Moderate' : 'High';
  const cls = pct < 30 ? 'text-success-400' : pct < 70 ? 'text-warning-400' : 'text-danger-400';
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
      <span className="text-[11px] text-slate-500 w-8 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
        <motion.div initial={{ width:0 }} animate={{ width:`${pct}%` }}
          transition={{ delay:0.3, duration:0.6, ease:'easeOut' }}
          className={`h-full rounded-full ${color}`} />
      </div>
      <span className={`text-[10px] font-bold w-12 text-right shrink-0 ${cls}`}>{lvl}</span>
    </div>
  );
}
