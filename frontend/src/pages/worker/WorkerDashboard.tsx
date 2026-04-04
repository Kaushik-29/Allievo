import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  MapPin, CloudRain, Wind, Thermometer, RefreshCw,
  ShieldCheck, AlertTriangle,
  CheckCircle2, Wifi
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { usePlanStore } from '../../stores/planStore';
import { ZoneMap } from '../../components/worker/ZoneMap';
import { useRiskStatus } from '../../api/queries';
import apiClient from '../../api/client';

interface WeatherData {
  temperature?: number;
  description?: string;
  rain_1h?: number;
  aqi?: number;
  city?: string;
}

interface PlanData {
  planName?: string;
  weeklyPremium?: number;
  maxPayout?: number;
  coveredHours?: number;
  eligibleForPayout?: boolean;
}

export default function WorkerDashboard() {
  const { userId } = useAuthStore();
  const enrolledAt = usePlanStore(s => s.enrolledAt);
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loadingLoc, setLoadingLoc] = useState(false);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [planData, setPlanData] = useState<PlanData | null>(null);
  const [recentClaims, setRecentClaims] = useState<any[]>([]);
  const [workerName, setWorkerName] = useState('');

  const { data: riskStatus } = useRiskStatus('Hyderabad');

  // Get location
  const getLocation = () => {
    setLoadingLoc(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        pos => { setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }); setLoadingLoc(false); },
        () => { setLocation({ lat: 17.4600, lng: 78.3650 }); setLoadingLoc(false); } // fallback to Kondapur
      );
    } else {
      setLocation({ lat: 17.4600, lng: 78.3650 });
      setLoadingLoc(false);
    }
  };

  // Re-run policy fetch whenever a new plan purchase is made
  useEffect(() => {
    getLocation();
    if (userId) {
      apiClient.get(`/api/v1/workers/${userId}/profile`).then(r => setWorkerName(r.data?.name || '')).catch(() => {});
      // Fetch from the NEW plans system (not old policies)
      apiClient.get(`/api/v1/plans/worker/${userId}`).then(r => {
        const enr = r.data?.enrollment;
        const plan = r.data?.plan;
        if (enr) {
          setPlanData({
            planName: enr.plan_name,
            weeklyPremium: enr.weekly_premium,
            maxPayout: plan?.max_payout,
            coveredHours: plan?.covered_hours,
            eligibleForPayout: enr.eligible_for_payout,
          });
        }
      }).catch(() => {});
      apiClient.get(`/api/v1/claims/${userId}/claims`).then(r => setRecentClaims(r.data?.slice(0, 3) || [])).catch(() => {});
    }
  }, [userId, enrolledAt]);

  useEffect(() => {
    if (location) {
      apiClient.get(`/api/v1/status/weather?lat=${location.lat}&lng=${location.lng}`)
        .then(r => setWeather(r.data))
        .catch(() => setWeather({ temperature: 28, description: 'Partly cloudy', aqi: 85 }));
    }
  }, [location]);

  const civAlert = riskStatus?.civil_risk?.active;
  const civAlertSource = riskStatus?.civil_risk?.source;
  const firstName = workerName.split(' ')[0] || 'Worker';

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Greeting header ── */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-500 text-sm font-medium">{greeting}</p>
          <h1 className="text-2xl font-display font-bold text-slate-100 mt-0.5">
            {firstName} <span className="text-slate-500 font-medium">👋</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">Kondapur Zone · Hyderabad</p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-success-500/8 border border-success-500/20">
          <div className="w-1.5 h-1.5 rounded-full bg-success-500 animate-pulse" />
          <span className="text-xs font-semibold text-success-400">Active Coverage</span>
        </div>
      </div>

      {/* ── Civil Alert Banner ── */}
      {civAlert && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="alert-banner danger"
        >
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">Disruption Alert in Your Zone</p>
            <p className="text-xs mt-0.5 text-danger-400/70">{civAlertSource || 'Civil disruption detected — claim will be auto-triggered if eligible'}</p>
          </div>
        </motion.div>
      )}

      {/* ── Recent payout notification ── */}
      {recentClaims.length > 0 && recentClaims[0].payout_status === 'success' && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="alert-banner success"
        >
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <div>
            <p className="font-semibold text-sm">₹{recentClaims[0].payout_amount?.toFixed(0)} payout processed</p>
            <p className="text-xs mt-0.5 text-success-400/70">{recentClaims[0].trigger_type} trigger · sent to your UPI</p>
          </div>
        </motion.div>
      )}

      {/* ── Policy overview ── */}
      <div className="hero-card">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <p className="text-brand-200 text-xs font-semibold uppercase tracking-widest">Active Policy</p>
            <p className="text-white text-3xl font-display font-bold mt-1">
              {planData ? `₹${planData.weeklyPremium?.toFixed(0)}` : '—'}
              <span className="text-brand-300 text-base font-medium">/week</span>
            </p>
            <p className="text-brand-200 text-sm mt-1 capitalize">
              {planData?.planName ? `${planData.planName} plan` : 'No active plan'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-brand-200 text-xs font-semibold uppercase tracking-widest">Max Payout</p>
            <p className="text-white text-xl font-display font-bold mt-1">
              {planData?.maxPayout ? `₹${planData.maxPayout.toFixed(0)}` : '—'}
            </p>
            {planData?.eligibleForPayout && (
              <div className="flex items-center gap-1 justify-end mt-1">
                <ShieldCheck className="w-3 h-3 text-brand-300" />
                <span className="text-xs text-brand-300">Payout eligible</span>
              </div>
            )}
          </div>
        </div>
        <div className="relative z-10 mt-4 grid grid-cols-3 gap-2">
          {[
            { label: 'Type',     value: 'Parametric' },
            { label: 'Coverage', value: planData?.coveredHours ? `${planData.coveredHours} hrs/wk` : '—' },
            { label: 'Zone',     value: 'Kondapur' },
          ].map(item => (
            <div key={item.label} className="bg-white/10 rounded-lg px-3 py-2 backdrop-blur-sm">
              <p className="text-brand-200 text-[10px] font-semibold uppercase tracking-wider">{item.label}</p>
              <p className="text-white text-sm font-bold mt-0.5">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Weather + Risk row ── */}
      <div className="grid grid-cols-3 gap-2 md:gap-3">
        <div className="card p-4 space-y-2">
          <div className="flex items-center gap-2">
            <Thermometer className="w-4 h-4 text-warning-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Temp</span>
          </div>
          <p className="text-xl font-display font-bold text-slate-100">{weather?.temperature ?? '--'}°C</p>
          <p className="text-xs text-slate-500 capitalize">{weather?.description || 'Loading...'}</p>
        </div>
        <div className="card p-4 space-y-2">
          <div className="flex items-center gap-2">
            <Wind className="w-4 h-4 text-info-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AQI</span>
          </div>
          <p className={`text-xl font-display font-bold ${(weather?.aqi ?? 0) > 300 ? 'text-danger-400' : (weather?.aqi ?? 0) > 150 ? 'text-warning-400' : 'text-success-400'}`}>
            {weather?.aqi ?? '--'}
          </p>
          <p className="text-xs text-slate-500">{(weather?.aqi ?? 0) > 300 ? 'Hazardous' : (weather?.aqi ?? 0) > 150 ? 'Unhealthy' : 'Moderate'}</p>
        </div>
        <div className="card p-4 space-y-2">
          <div className="flex items-center gap-2">
            <CloudRain className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Rain</span>
          </div>
          <p className="text-xl font-display font-bold text-slate-100">{weather?.rain_1h ?? '0'}<span className="text-xs text-slate-500 ml-1">mm/h</span></p>
          <p className="text-xs text-slate-500">{(weather?.rain_1h ?? 0) > 64 ? 'TRIGGER ACTIVE' : 'Below threshold'}</p>
        </div>
      </div>

      {/* ── Zone Map ── */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-brand-400" />
            <span className="text-sm font-semibold text-slate-200">Coverage Zone</span>
          </div>
          <button
            onClick={getLocation}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingLoc ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
        <div className="h-[240px]">
          {location ? (
            <ZoneMap lat={location.lat} lng={location.lng} />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-600 text-sm">
              <Wifi className="w-4 h-4 mr-2 animate-pulse" /> Fetching location...
            </div>
          )}
        </div>
        <div className="px-4 py-2.5 border-t border-border flex items-center justify-between">
          <span className="text-xs text-slate-500 font-mono">
            {location ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : 'Detecting...'}
          </span>
          <span className="badge-success text-[10px]">15km radius</span>
        </div>
      </div>

      {/* ── Recent Claims ── */}
      {recentClaims.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="section-header">Recent Claims</p>
            <a href="/worker/claims" className="text-xs text-brand-400 hover:text-brand-300 font-semibold">View all →</a>
          </div>
          <div className="card divide-y divide-border">
            {recentClaims.map(claim => (
              <div key={claim.id} className="data-row px-4">
                <div>
                  <p className="text-sm font-semibold text-slate-200 capitalize">{claim.trigger_type} trigger</p>
                  <p className="text-xs text-slate-500 mt-0.5">{claim.date}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-slate-100">₹{claim.payout_amount?.toFixed(0) || claim.capped_payout?.toFixed(0)}</p>
                  <span className={`text-[10px] font-bold ${
                    claim.status === 'approved' ? 'text-success-400' :
                    claim.status === 'partial' ? 'text-warning-400' : 'text-slate-500'
                  }`}>{claim.status?.toUpperCase()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
