import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, ArrowRight, ShieldCheck, CheckCircle2, UserCircle, MapPin } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import apiClient from '../../api/client';

export default function Onboarding() {
  const [contact, setContact] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'request' | 'verify' | 'link_platform'>('request');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contact) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiClient.post('/api/v1/auth/request-otp', { contact });
      setStep('verify');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) return;
    
    setLoading(true);
    setError('');
    
    try {
      const res = await apiClient.post('/api/v1/auth/verify-otp', { 
        contact, otp, name: "Gig Worker", city: "Bengaluru" 
      });
      
      const data = res.data;
      setAuth(data.worker_id, data.access_token);
      setStep('link_platform');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleFinishOnboarding = () => {
    navigate('/worker/home');
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 bg-background">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary-500/20 rounded-full blur-[120px] mix-blend-screen animate-float" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-accent-DEFAULT/20 rounded-full blur-[100px] mix-blend-screen animate-float" style={{ animationDelay: '2s' }} />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="glass-card w-full max-w-md p-8 z-10"
      >
        <div className="flex justify-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-glow">
            <ShieldCheck className="text-white w-8 h-8" />
          </div>
        </div>
        
        <h1 className="font-title text-3xl font-bold text-center text-white mb-2">Allievo</h1>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-sm p-3 rounded-xl mb-6 text-center">
            {error}
          </div>
        )}

        <AnimatePresence mode="wait">
          {step === 'request' && (
            <motion.div key="request" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <p className="text-gray-400 text-center mb-8">Income insurance for delivery partners</p>
              <form onSubmit={handleRequestOtp} className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-300 mb-1 block text-left">Phone or Email</label>
                  <div className="relative">
                    <input 
                      type="text" 
                      value={contact}
                      onChange={(e) => setContact(e.target.value)}
                      placeholder="Enter your registered number/email"
                      className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 pl-11 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                      required 
                    />
                    <Phone className="absolute left-3 top-3.5 w-5 h-5 text-gray-500" />
                  </div>
                </div>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="w-full bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3.5 rounded-xl transition-all shadow-lg shadow-primary-500/30 flex items-center justify-center gap-2 group"
                >
                  {loading ? 'Sending...' : 'Get OTP'}
                  {!loading && <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />}
                </button>
              </form>
            </motion.div>
          )}

          {step === 'verify' && (
            <motion.div key="verify" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div className="text-center mb-6">
                  <div className="text-sm text-gray-400 mb-1">Enter the 6-digit OTP sent to</div>
                  <div className="font-medium text-white">{contact}</div>
                </div>
                
                <div>
                  <input 
                    type="text" 
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="• • • • • •"
                    className="w-full bg-white/5 border border-white/10 rounded-xl py-4 px-4 text-center text-2xl tracking-[1em] text-white focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all font-mono"
                    maxLength={6}
                    required 
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={loading || otp.length !== 6}
                  className="w-full bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:hover:bg-primary-600 text-white font-semibold py-3.5 rounded-xl transition-all shadow-lg shadow-primary-500/30 flex items-center justify-center gap-2"
                >
                  {loading ? 'Verifying...' : 'Verify & Login'}
                  {!loading && <CheckCircle2 className="w-5 h-5" />}
                </button>
                <button 
                  type="button"
                  onClick={() => setStep('request')}
                  className="w-full text-gray-400 text-sm hover:text-white transition-colors py-2"
                >
                  Change contact info
                </button>
              </form>
            </motion.div>
          )}

          {step === 'link_platform' && (
            <motion.div key="link_platform" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Connect Your Fleet</h2>
                <p className="text-sm text-gray-400">Link your active gig platforms so we can automatically sync your shifts, zones, and disruption risk.</p>
              </div>

              <div className="space-y-3">
                <button className="w-full bg-orange-600/10 hover:bg-orange-600/20 border border-orange-600/50 text-orange-500 font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2">
                  <UserCircle className="w-5 h-5" /> Link Swiggy Fleet
                </button>
                <button className="w-full bg-red-600/10 hover:bg-red-600/20 border border-red-600/50 text-red-500 font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2">
                  <UserCircle className="w-5 h-5" /> Link Zomato Rider
                </button>
              </div>

              <div className="pt-4 border-t border-white/10">
                <div className="bg-white/5 rounded-xl p-4 flex items-center gap-3 text-left">
                   <div className="p-2 bg-primary-500/20 rounded-lg"><MapPin className="text-primary-400 w-5 h-5" /></div>
                   <div>
                      <p className="text-sm text-white font-medium">Primary Zone Assigned</p>
                      <p className="text-xs text-gray-400">Koramangala, Bengaluru</p>
                   </div>
                </div>
              </div>

              <button 
                onClick={handleFinishOnboarding}
                className="w-full bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3.5 rounded-xl transition-all shadow-lg shadow-primary-500/30"
              >
                Continue to Dashboard
              </button>
            </motion.div>
          )}

        </AnimatePresence>
      </motion.div>
    </div>
  );
}
