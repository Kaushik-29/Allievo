import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, CreditCard, MapPin, User,
  CheckCircle2, Edit3, X, Lock,
  Phone, Mail, Loader2, AlertCircle, Smartphone
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useProfile } from '../../api/queries';
import apiClient from '../../api/client';

export default function Profile() {
  const { userId } = useAuthStore();
  const { data: profile, isLoading, refetch } = useProfile(userId);

  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [otp, setOtp] = useState('');
  const [otpStep, setOtpStep] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [upiValue, setUpiValue] = useState('');
  const [editingUpi, setEditingUpi] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-6 h-6 text-brand-400 animate-spin" />
      </div>
    );
  }

  const requestOtp = async (field: 'phone' | 'email', value: string) => {
    setLoading(true);
    setError('');
    try {
      await apiClient.post('/api/v1/workers/profile/request-otp', { field, value });
      setOtpStep(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'OTP request failed');
    } finally {
      setLoading(false);
    }
  };

  const verifyAndUpdate = async () => {
    if (!editingField) return;
    setLoading(true);
    setError('');
    try {
      await apiClient.post('/api/v1/workers/profile/verify-otp', {
        field: editingField, value: editValue, otp_code: otp
      });
      setSuccess(`${editingField === 'phone' ? 'Phone' : 'Email'} updated successfully`);
      setEditingField(null);
      setOtpStep(false);
      setOtp('');
      refetch();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const saveUpi = async () => {
    setLoading(true);
    setError('');
    try {
      await apiClient.patch('/api/v1/workers/profile', { upi_id: upiValue });
      setSuccess('UPI ID saved');
      setEditingUpi(false);
      refetch();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to save UPI');
    } finally {
      setLoading(false);
    }
  };

  const startOtpEdit = (field: 'phone' | 'email') => {
    setEditingField(field);
    setEditValue(field === 'phone' ? profile?.phone || '' : profile?.email || '');
    setOtpStep(false);
    setOtp('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">Manage your identity, payout, and contact details</p>
      </div>

      {/* Worker identity header */}
      <div className="card p-5 flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center font-display font-bold text-white text-lg">
          {profile?.name?.[0] || 'W'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-display font-bold text-slate-100 text-lg">{profile?.name || '—'}</p>
          <p className="text-sm text-slate-500">@{profile?.username}</p>
        </div>
        <div>
          <span className="badge-success">KYC Verified</span>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="alert-banner success">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="text-sm font-medium">{success}</span>
          <button onClick={() => setSuccess('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}
      {error && (
        <div className="alert-banner danger">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span className="text-sm font-medium">{error}</span>
          <button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* ── Identity & KYC ── */}
      <section>
        <p className="section-header">Identity & KYC</p>
        <div className="card divide-y divide-border">
          {[
            { label: 'Full Name', value: profile?.name, icon: User },
            { label: 'Aadhar Number', value: profile?.aadhar_no ? `XXXX XXXX ${profile.aadhar_no.slice(-4)}` : '—', icon: Shield },
            { label: 'PAN Number', value: profile?.pan_no || '—', icon: Lock },
          ].map(row => (
            <div key={row.label} className="data-row px-5">
              <div className="flex items-center gap-2.5">
                <row.icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <span className="data-row-label">{row.label}</span>
              </div>
              <span className="data-row-value font-mono">{row.value}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Security & Contact ── */}
      <section>
        <p className="section-header">Security & Contact</p>
        <div className="card divide-y divide-border">
          {/* Phone */}
          <div className="data-row px-5">
            <div className="flex items-center gap-2.5">
              <Phone className="w-3.5 h-3.5 text-slate-500" />
              <span className="data-row-label">Phone</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="data-row-value">{profile?.phone || '—'}</span>
              <button
                onClick={() => startOtpEdit('phone')}
                className="p-1.5 rounded-lg hover:bg-surface-2 transition-colors text-slate-500 hover:text-brand-400"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Email */}
          <div className="data-row px-5">
            <div className="flex items-center gap-2.5">
              <Mail className="w-3.5 h-3.5 text-slate-500" />
              <span className="data-row-label">Email</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="data-row-value">{profile?.email || '—'}</span>
              <button
                onClick={() => startOtpEdit('email')}
                className="p-1.5 rounded-lg hover:bg-surface-2 transition-colors text-slate-500 hover:text-brand-400"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── OTP Modal ── */}
      <AnimatePresence>
        {editingField && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.96, y: 16 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.96 }}
              className="card p-6 w-full max-w-sm space-y-5"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display font-bold text-slate-100">
                    Update {editingField === 'phone' ? 'Phone' : 'Email'}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">OTP verification required</p>
                </div>
                <button onClick={() => { setEditingField(null); setOtpStep(false); }} className="p-1.5 hover:bg-surface-2 rounded-lg transition-colors">
                  <X className="w-4 h-4 text-slate-500" />
                </button>
              </div>

              {!otpStep ? (
                <div className="space-y-4">
                  <div>
                    <label className="form-label">New {editingField === 'phone' ? 'Phone Number' : 'Email Address'}</label>
                    <input
                      type={editingField === 'phone' ? 'tel' : 'email'}
                      value={editValue}
                      onChange={e => setEditValue(e.target.value)}
                      className="form-input"
                      placeholder={editingField === 'phone' ? '9876543210' : 'you@email.com'}
                    />
                  </div>
                  <button
                    onClick={() => requestOtp(editingField as 'phone' | 'email', editValue)}
                    disabled={loading || !editValue}
                    className="btn-primary w-full"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                    Send OTP
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="alert-banner info text-xs">
                    <Smartphone className="w-3.5 h-3.5 shrink-0" />
                    <span>OTP sent to {editValue}. (Dev: check backend console)</span>
                  </div>
                  <div>
                    <label className="form-label">Enter 6-digit OTP</label>
                    <input
                      type="text"
                      value={otp}
                      onChange={e => setOtp(e.target.value)}
                      className="form-input font-mono text-center tracking-widest text-lg"
                      placeholder="000000"
                      maxLength={6}
                    />
                  </div>
                  <button
                    onClick={verifyAndUpdate}
                    disabled={loading || otp.length !== 6}
                    className="btn-primary w-full"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                    Verify & Update
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Logistics ── */}
      <section>
        <p className="section-header">Logistics</p>
        <div className="card divide-y divide-border">
          {[
            { label: 'Platform', value: profile?.primary_platform ? profile.primary_platform.charAt(0).toUpperCase() + profile.primary_platform.slice(1) : '—', icon: Smartphone },
            { label: 'Work Zone', value: profile?.work_location || '—', icon: MapPin },
            { label: 'Current Address', value: profile?.current_location || '—', icon: MapPin },
          ].map(row => (
            <div key={row.label} className="data-row px-5">
              <div className="flex items-center gap-2.5">
                <row.icon className="w-3.5 h-3.5 text-slate-500" />
                <span className="data-row-label">{row.label}</span>
              </div>
              <span className="data-row-value">{row.value}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Payments ── */}
      <section>
        <p className="section-header">Payout Destination</p>
        <div className="card p-5 space-y-4">
          <div className="data-row">
            <div className="flex items-center gap-2.5">
              <CreditCard className="w-3.5 h-3.5 text-slate-500" />
              <span className="data-row-label">UPI ID</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="data-row-value font-mono text-sm">{profile?.upi_id || 'Not set'}</span>
              <button
                onClick={() => { setEditingUpi(true); setUpiValue(profile?.upi_id || ''); }}
                className="p-1.5 rounded-lg hover:bg-surface-2 transition-colors text-slate-500 hover:text-brand-400"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <AnimatePresence>
            {editingUpi && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="space-y-3 pt-3 border-t border-border"
              >
                <div>
                  <label className="form-label">UPI ID (e.g. yourname@okaxis)</label>
                  <input
                    value={upiValue}
                    onChange={e => setUpiValue(e.target.value)}
                    className="form-input font-mono"
                    placeholder="name@upi"
                  />
                </div>
                <div className="flex gap-2">
                  <button onClick={saveUpi} disabled={loading || !upiValue} className="btn-primary flex-1">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                    Save UPI ID
                  </button>
                  <button onClick={() => setEditingUpi(false)} className="btn-secondary">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {profile?.upi_id && (
            <div className="text-xs text-slate-500 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-success-400" />
              All payouts will be sent to this UPI address automatically
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
