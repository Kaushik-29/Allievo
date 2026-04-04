import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudRain, Wind, Thermometer, AlertTriangle, Zap, PlayCircle,
  Shield, Loader2, TrendingDown, Activity, Cpu, MapPin, CreditCard,
  CheckCircle2, XCircle
} from 'lucide-react';
import apiClient from '../../api/client';

const TRIGGERS = [
  { type: 'rainfall', label: 'Monsoon Rainfall', icon: CloudRain, badge: '72mm/hr', color: 'info' },
  { type: 'aqi',      label: 'AQI Crisis',        icon: Wind,      badge: 'AQI 420', color: 'brand' },
  { type: 'curfew',   label: 'Section 144',       icon: AlertTriangle, badge: '80% drop', color: 'warning' },
  { type: 'outage',   label: 'Platform Outage',   icon: Zap,       badge: '60min',    color: 'danger' },
];

const BAND_CONFIG: Record<string, { label: string; cls: string }> = {
  auto_approve: { label: 'Auto-Approve',  cls: 'badge-success' },
  partial:      { label: 'Partial Pay',   cls: 'badge-warning' },
  hold:         { label: 'Hard Hold',     cls: 'badge-danger'  },
  block:        { label: 'Blocked',       cls: 'badge-danger'  },
};

const FRAUD_CHECKS = [
  { key: 'gps',      label: 'GPS Trajectory',    icon: MapPin,    desc: 'Road-following, natural drift detected' },
  { key: 'tower',    label: 'Cell Tower Match',  icon: Cpu,       desc: 'Within 500m of GPS coords' },
  { key: 'activity', label: 'Platform Activity', icon: Activity,  desc: 'Active order 12min before trigger' },
  { key: 'device',   label: 'Device Fingerprint',icon: Shield,    desc: 'Matches onboarding hardware hash' },
  { key: 'zone',     label: 'Zone Presence 30d', icon: TrendingDown, desc: 'ZPS=0.87 — 87/90 active days' },
];

export default function DemoControlPanel() {
  const [selectedTrigger, setSelectedTrigger] = useState('rainfall');
  const [zone, setZone] = useState('Kondapur');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleFire = async () => {
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const res = await apiClient.post(
        `/api/v1/admin/demo/fire-trigger?trigger_type=${selectedTrigger}&zone_name=${encodeURIComponent(zone)}`
      );
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fire trigger. Check backend logs.');
    } finally {
      setLoading(false);
    }
  };

  const w = result?.results?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <h1 className="page-title">Demo Control Panel</h1>
          <span className="badge-brand text-[10px] font-bold px-2 py-0.5">DEVTrails 2026</span>
        </div>
        <p className="page-subtitle">Fire live parametric triggers and observe the full payout pipeline</p>
      </div>

      {/* Persona card */}
      <div className="card p-4 sm:p-5 flex flex-wrap items-center gap-4 sm:gap-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center font-display font-bold text-white">R</div>
          <div>
            <p className="font-semibold text-slate-200">Ravi Kumar</p>
            <p className="text-xs text-slate-500">Kondapur · Zomato · Standard Policy</p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-4 w-full sm:w-auto">
          {[
            { k: 'Combined DAE', v: '₹1,000/day' },
            { k: 'Active Days', v: '87 / 90' },
            { k: 'UPI', v: 'ravi.kumar@okaxis' },
            { k: 'Payout Cap', v: '₹700/wk' },
          ].map(kv => (
            <div key={kv.k}>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{kv.k}</p>
              <p className="text-sm font-semibold text-slate-200 mt-0.5">{kv.v}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Left — Trigger selector */}
        <div className="card p-6 space-y-5">
          <p className="section-header">1 — Select Trigger</p>

          <div className="space-y-2">
            {TRIGGERS.map(t => (
              <button
                key={t.type}
                onClick={() => setSelectedTrigger(t.type)}
                className={`w-full flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all ${
                  selectedTrigger === t.type
                    ? 'border-brand-500/40 bg-brand-500/8 text-slate-200'
                    : 'border-border bg-surface hover:border-border-2 text-slate-400'
                }`}
              >
                <t.icon className={`w-4 h-4 shrink-0 ${selectedTrigger === t.type ? 'text-brand-400' : 'text-slate-600'}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold">{t.label}</p>
                </div>
                <span className={`badge ${selectedTrigger === t.type ? 'badge-brand' : 'badge-muted'}`}>{t.badge}</span>
                {selectedTrigger === t.type && <div className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />}
              </button>
            ))}
          </div>

          <div>
            <label className="form-label">Target Zone</label>
            <input
              value={zone}
              onChange={e => setZone(e.target.value)}
              className="form-input"
              placeholder="e.g. Kondapur"
            />
          </div>

          <button
            onClick={handleFire}
            disabled={loading}
            className="btn-primary w-full py-3"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Running pipeline...</>
              : <><PlayCircle className="w-4 h-4" /> Fire Trigger & Run Pipeline</>
            }
          </button>

          {error && (
            <div className="alert-banner danger text-sm">
              <XCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Right — Pipeline Result */}
        <div className="card p-6 space-y-5">
          <p className="section-header">2 — Pipeline Result</p>

          {!result && !loading && (
            <div className="flex flex-col items-center justify-center h-56 text-slate-700 space-y-3">
              <Activity className="w-10 h-10 opacity-30" />
              <p className="text-xs font-semibold uppercase tracking-widest">Waiting for trigger</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-56 text-brand-400 space-y-3">
              <Loader2 className="w-10 h-10 animate-spin" />
              <p className="text-xs font-semibold uppercase tracking-widest animate-pulse">Running 5-gate fraud check...</p>
            </div>
          )}

          {result && w && (
            <AnimatePresence>
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {/* Trigger badge */}
                <div className="flex items-center gap-2">
                  <span className="badge-brand capitalize">{result.trigger_type}</span>
                  <span className="badge-success">{result.severity}</span>
                  <span className="text-[10px] text-slate-500 ml-auto">{result.timestamp?.slice(0, 19).replace('T', ' ')} UTC</span>
                </div>

                {/* Formula */}
                <div className="bg-surface-2 rounded-xl p-4 border border-border space-y-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Payout Calculation</p>
                  <p className="text-xs font-mono text-slate-400">{w.payout_formula}</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500">Gross</p>
                      <p className="text-lg font-display font-bold text-slate-300">₹{w.gross_payout?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500">After Cap (₹700)</p>
                      <p className="text-2xl font-display font-bold text-brand-400">₹{w.capped_payout}</p>
                    </div>
                  </div>
                </div>

                {/* Fraud gate checks */}
                <div className="space-y-2">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">5-Signal Fraud Gate</p>
                  {FRAUD_CHECKS.map(fc => (
                    <div key={fc.key} className="flex items-center gap-2.5 text-xs">
                      <CheckCircle2 className="w-3.5 h-3.5 text-success-400 shrink-0" />
                      <fc.icon className="w-3 h-3 text-slate-600 shrink-0" />
                      <span className="text-slate-400 font-medium w-32 shrink-0">{fc.label}</span>
                      <span className="text-slate-600 text-[11px] truncate">{fc.desc}</span>
                    </div>
                  ))}
                </div>

                {/* Fraud score */}
                <div className="flex items-center justify-between p-3 bg-surface-2 rounded-xl border border-border">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Composite Score</p>
                    <p className="text-2xl font-display font-bold text-slate-100">{w.fraud_score?.toFixed(4)}</p>
                  </div>
                  <span className={`badge ${BAND_CONFIG[w.fraud_band]?.cls || 'badge-muted'} text-xs`}>
                    {BAND_CONFIG[w.fraud_band]?.label || w.fraud_band}
                  </span>
                </div>

                {/* Payout result */}
                {w.first_transfer > 0 && (
                  <div className="alert-banner success">
                    <CreditCard className="w-4 h-4 shrink-0" />
                    <div>
                      <p className="font-semibold text-sm">₹{w.first_transfer} sent to {w.upi_vpa}</p>
                      {w.razorpay_ref && <p className="text-[11px] mt-0.5 opacity-60 font-mono">Ref: {w.razorpay_ref}</p>}
                      {w.hold_amount > 0 && <p className="text-[11px] mt-0.5 text-warning-400">+₹{w.hold_amount} releasing in 24hrs</p>}
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
}
