import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, ChevronRight, ChevronLeft, 
  CreditCard, Briefcase, FileCheck, CheckCircle2 
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { Button } from '../../components/shared/Button';

export default function Register() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    phone: '',
    email: '',
    city: 'Bengaluru',
    aadhar_no: '',
    pan_no: '',
    primary_platform: 'zomato',
    work_location: '',
    current_location: '',
    working_proof: 'App screenshot verified'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await apiClient.post('/api/v1/auth/register', formData);
      navigate('/worker/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 flex flex-col items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-xl glass-card p-8 border-primary-500/20"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white">Join the Shield</h1>
          <p className="text-sm text-gray-400 font-medium">Protect your gig earnings with Allievo</p>
          
          {/* Progress Bar */}
          <div className="flex justify-center gap-2 mt-6">
            {[1, 2, 3].map((s) => (
              <div 
                key={s}
                className={`h-1.5 w-12 rounded-full transition-all duration-500 ${s <= step ? 'bg-primary-500 shadow-[0_0_10px_rgba(139,92,246,0.5)]' : 'bg-white/10'}`}
              />
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div 
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><User className="text-primary-400 w-5 h-5" /> Account Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Full Name</label>
                    <input name="name" value={formData.name} onChange={handleChange} placeholder="John Doe" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Username</label>
                    <input name="username" value={formData.username} onChange={handleChange} placeholder="john_shield" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Email Address</label>
                    <input type="email" name="email" value={formData.email} onChange={handleChange} placeholder="john@example.com" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Password</label>
                    <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="••••••••" className="register-input" required />
                  </div>
                </div>
                <div className="flex justify-end pt-4">
                  <Button type="button" onClick={nextStep} variant="primary" className="rounded-2xl px-8 font-black text-xs">NEXT <ChevronRight className="ml-2 w-4 h-4" /></Button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div 
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><CreditCard className="text-primary-400 w-5 h-5" /> KYC Verification</h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Aadhar Card Number</label>
                    <input name="aadhar_no" value={formData.aadhar_no} onChange={handleChange} placeholder="1234 5678 9012" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">PAN Card Number</label>
                    <input name="pan_no" value={formData.pan_no} onChange={handleChange} placeholder="ABCDE1234F" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Phone Number</label>
                    <input name="phone" value={formData.phone} onChange={handleChange} placeholder="9876543210" className="register-input" required />
                  </div>
                </div>
                <div className="flex justify-between pt-4">
                  <Button type="button" onClick={prevStep} variant="secondary" className="rounded-2xl font-black text-xs border border-white/10"><ChevronLeft className="mr-2 w-4 h-4" /> PREV</Button>
                  <Button type="button" onClick={nextStep} variant="primary" className="rounded-2xl px-8 font-black text-xs">NEXT <ChevronRight className="ml-2 w-4 h-4" /></Button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div 
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><Briefcase className="text-primary-400 w-5 h-5" /> Platform Logistics</h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Platform</label>
                        <select name="primary_platform" value={formData.primary_platform} onChange={handleChange} className="register-input appearance-none bg-white/5">
                            <option value="zomato" className="bg-slate-900">Zomato</option>
                            <option value="swiggy" className="bg-slate-900">Swiggy</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Work City</label>
                        <input name="city" value={formData.city} onChange={handleChange} className="register-input" required />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Primary Work Location (Zone)</label>
                    <input name="work_location" value={formData.work_location} onChange={handleChange} placeholder="HSR Layout, Bengaluru" className="register-input" required />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 font-bold">Current Address</label>
                    <input name="current_location" value={formData.current_location} onChange={handleChange} placeholder="Building 123, Sector 4..." className="register-input" required />
                  </div>
                  <div className="mt-4 p-4 rounded-xl bg-primary-500/5 border border-primary-500/20 flex items-center gap-3">
                    <FileCheck className="w-8 h-8 text-primary-400 shrink-0" />
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-primary-400">Platform Proof</p>
                        <p className="text-xs text-gray-400 leading-tight">By submitting, you authorize Allievo to verify your credentials against platform internal APIs.</p>
                    </div>
                  </div>
                </div>

                {error && <p className="text-rose-500 text-xs font-bold bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">{error}</p>}

                <div className="flex justify-between pt-4">
                  <Button type="button" onClick={prevStep} variant="secondary" className="rounded-2xl animate-fade-in font-black text-xs border border-white/10"><ChevronLeft className="mr-2 w-4 h-4" /> PREV</Button>
                  <Button type="submit" disabled={loading} variant="primary" className="rounded-2xl px-12 font-black text-sm shadow-xl shadow-primary-500/30">
                    {loading ? 'Processing...' : 'COMPLETE REGISTRATION'} <CheckCircle2 className="ml-2 w-4 h-4" />
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>

        <div className="text-center pt-8 border-t border-white/5 mt-8">
            <p className="text-xs text-gray-500">
                Already protected? {' '}
                <Link to="/worker/login" className="text-primary-400 font-black uppercase tracking-widest hover:text-primary-300">Login</Link>
            </p>
        </div>
      </motion.div>
    </div>
  );
}
