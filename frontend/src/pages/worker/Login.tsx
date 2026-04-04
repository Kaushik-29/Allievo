import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Lock, ArrowRight, ShieldCheck, AlertCircle, Loader2, Hexagon } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import apiClient from '../../api/client';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setAuth = useAuthStore(s => s.setAuth);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post('/api/v1/auth/login', { username, password });
      setAuth(res.data.worker_id, res.data.access_token);
      navigate('/worker/home');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col lg:flex-row">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col w-[440px] shrink-0 bg-[#0D1220] border-r border-border p-12 justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-glow-sm">
            <Hexagon className="w-5 h-5 text-white fill-white/20" />
          </div>
          <span className="font-display font-bold text-slate-100 text-xl">Allievo</span>
        </div>

        {/* Features */}
        <div className="space-y-8">
          <div>
            <h2 className="text-3xl font-display font-bold text-slate-100 leading-tight">
              Income protection<br />for every delivery.
            </h2>
            <p className="text-slate-400 text-sm mt-3 leading-relaxed">
              Automated parametric insurance that pays out within minutes — no claims, no paperwork. Just protection.
            </p>
          </div>

          <div className="space-y-4">
            {[
              { label: 'Instant payouts', desc: 'Triggered automatically during rain, AQI spikes, curfews' },
              { label: 'Zero-friction', desc: 'No forms. No calls. Straight to your UPI in minutes.' },
              { label: 'Fully personalized', desc: 'Your premium adjusts to your zone risk and tenure.' },
            ].map((f, i) => (
              <div key={i} className="flex gap-3">
                <div className="w-5 h-5 rounded-full bg-brand-500/15 border border-brand-500/30 flex items-center justify-center shrink-0 mt-0.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">{f.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-slate-600">© 2026 Allievo Technologies · DEVTrails Hackathon</p>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-[380px] space-y-7"
        >
          {/* Mobile logo */}
          <div className="flex items-center gap-3 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
              <Hexagon className="w-4 h-4 text-white fill-white/20" />
            </div>
            <span className="font-display font-bold text-slate-100 text-lg">Allievo</span>
          </div>

          <div>
            <h1 className="text-2xl font-display font-bold text-slate-100">Sign in</h1>
            <p className="text-sm text-slate-500 mt-1">Enter your worker credentials to continue</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Username */}
            <div>
              <label className="form-label">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="your_username"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="form-input pl-10"
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="form-label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="form-input pl-10"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="alert-banner danger text-sm"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Submit */}
            <button type="submit" disabled={loading} className="btn-primary w-full py-3 mt-2">
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</>
                : <><span>Sign in</span><ArrowRight className="w-4 h-4" /></>
              }
            </button>
          </form>

          {/* Demo hint */}
          <div className="card p-4 text-center space-y-1">
            <p className="text-xs font-semibold text-slate-400">Demo credentials</p>
            <p className="text-xs font-mono text-slate-300">ravi_kondapur <span className="text-slate-600">·</span> Ravi@1234</p>
          </div>

          <p className="text-sm text-slate-500 text-center">
            New worker?{' '}
            <Link to="/worker/register" className="text-brand-400 font-semibold hover:text-brand-300 transition-colors">
              Create account
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
