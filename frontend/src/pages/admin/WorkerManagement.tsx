import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, Search, CheckCircle2, XCircle, Loader2, CreditCard } from 'lucide-react';
import apiClient from '../../api/client';

const TIER_BADGE: Record<string, string> = {
  basic:    'badge-muted',
  standard: 'badge-brand',
  premium:  'badge-warning',
};

export default function WorkerManagement() {
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    apiClient.get('/api/v1/admin/workers')
      .then(r => setWorkers(r.data))
      .catch(() => setWorkers([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = workers.filter(w =>
    w.name?.toLowerCase().includes(search.toLowerCase()) ||
    w.username?.toLowerCase().includes(search.toLowerCase()) ||
    w.city?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="page-title">Worker Management</h1>
        <p className="page-subtitle">KYC, policy enrollment, and payout readiness</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Workers',     value: workers.length,                                      color: 'text-slate-200' },
          { label: 'KYC Verified',      value: workers.filter(w => w.aadhar_verified).length,        color: 'text-success-400' },
          { label: 'Active Policies',   value: workers.filter(w => w.has_active_policy).length,      color: 'text-brand-400'   },
          { label: 'Payout Ready',      value: workers.filter(w => w.eligible_for_payout).length,    color: 'text-success-400' },
        ].map(kpi => (
          <div key={kpi.label} className="stat-card">
            <p className={`stat-value ${kpi.color}`}>{kpi.value}</p>
            <p className="stat-label">{kpi.label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by name, username, or city..."
          className="form-input pl-10"
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="hidden sm:grid table-header-row grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr]">
          <span>Worker</span>
          <span>Platform</span>
          <span>KYC</span>
          <span>Policy</span>
          <span>Payout</span>
          <span>UPI</span>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16 text-slate-600">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading...
          </div>
        )}

        {!loading && filtered.map((w, i) => (
          <motion.div key={w.id} initial={{ opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="sm:grid table-row grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] flex flex-wrap justify-between gap-y-2"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500/30 to-brand-700/30 flex items-center justify-center font-bold text-brand-400 text-xs">
                {w.name?.[0]}
              </div>
              <div>
                <p className="text-slate-200 font-semibold text-sm">{w.name}</p>
                <p className="text-slate-500 text-[10px]">@{w.username} · {w.city}</p>
              </div>
            </div>
            <span className="capitalize text-slate-400 text-xs font-medium">{w.platform}</span>
            <div className="flex items-center gap-1">
              {w.aadhar_verified ? <CheckCircle2 className="w-3.5 h-3.5 text-success-400" /> : <XCircle className="w-3.5 h-3.5 text-slate-600" />}
              {w.pan_verified ? <CheckCircle2 className="w-3.5 h-3.5 text-success-400" /> : <XCircle className="w-3.5 h-3.5 text-slate-600" />}
            </div>
            <span>
              {w.has_active_policy
                ? <span className={`badge ${TIER_BADGE[w.policy_tier] || 'badge-muted'} text-[10px] capitalize`}>{w.policy_tier}</span>
                : <span className="text-slate-600 text-xs">None</span>
              }
            </span>
            <div>
              {w.eligible_for_payout
                ? <CheckCircle2 className="w-4 h-4 text-success-400" />
                : <XCircle className="w-4 h-4 text-slate-600" />
              }
            </div>
            <div className="flex items-center gap-1 text-slate-500">
              {w.upi_id ? <><CreditCard className="w-3 h-3" /><span className="text-[10px] font-mono truncate max-w-[80px]">{w.upi_id}</span></> : <span className="text-slate-600 text-xs">—</span>}
            </div>
          </motion.div>
        ))}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-600 gap-2">
            <Users className="w-8 h-8 opacity-30" />
            <p className="text-sm">No workers found</p>
          </div>
        )}
      </div>
    </div>
  );
}
