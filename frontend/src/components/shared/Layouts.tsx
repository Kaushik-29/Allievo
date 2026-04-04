import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home, Shield, FileText, Settings, LogOut,
  Activity, Users, BarChart3, PlayCircle,
  ShieldCheck, Hexagon, Menu, X, LayoutGrid,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

/* ─────────────────────────────────────────────
   WORKER LAYOUT
   Desktop: fixed left sidebar
   Mobile: top header + bottom tab bar
──────────────────────────────────────────────*/
export function WorkerLayout() {
  const location = useLocation();
  const { logout } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/worker/home',    icon: Home,        label: 'Dashboard' },
    { path: '/worker/policy',  icon: Shield,      label: 'Policy'    },
    { path: '/worker/plans',   icon: LayoutGrid,  label: 'Plans'     },
    { path: '/worker/claims',  icon: FileText,    label: 'Claims'    },
    { path: '/worker/profile', icon: Settings,    label: 'Profile'   },
  ];

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-background text-slate-300 flex">

      {/* ────────── DESKTOP SIDEBAR ────────── */}
      <aside className="hidden md:flex flex-col w-[232px] shrink-0 bg-[#0D1220] border-r border-border fixed top-0 left-0 h-screen z-40 overflow-y-auto">
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-glow-sm">
              <Hexagon className="w-4 h-4 text-white fill-white/20" />
            </div>
            <div>
              <p className="font-display font-bold text-slate-100 text-[15px] leading-none">Allievo</p>
              <p className="text-[10px] text-slate-500 font-medium mt-0.5 uppercase tracking-widest">Worker Portal</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest px-2 py-2">Navigation</p>
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive(item.path)
                  ? 'bg-brand-500/12 text-brand-400 font-semibold'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              <item.icon className={`w-4 h-4 ${isActive(item.path) ? 'text-brand-500' : 'text-slate-600'}`} />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-border">
          <button
            onClick={logout}
            className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:text-danger-400 hover:bg-danger-500/5 transition-all w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ────────── MOBILE TOP BAR ────────── */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[#0D1220] border-b border-border flex items-center px-4 z-40">
        <div className="flex items-center gap-2.5 flex-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Hexagon className="w-3.5 h-3.5 text-white fill-white/20" />
          </div>
          <span className="font-display font-bold text-slate-100 text-base">Allievo</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(v => !v)}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/5"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* ────────── MOBILE SLIDE-DOWN MENU ────────── */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 bg-black/50 z-30"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ y: -8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -8, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="md:hidden fixed top-14 left-0 right-0 bg-[#0D1220] border-b border-border z-40 p-3 space-y-1"
            >
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(item.path)
                      ? 'bg-brand-500/12 text-brand-400'
                      : 'text-slate-400 hover:bg-white/5'
                  }`}
                >
                  <item.icon className={`w-4 h-4 ${isActive(item.path) ? 'text-brand-400' : 'text-slate-600'}`} />
                  {item.label}
                </Link>
              ))}
              <div className="border-t border-border pt-2">
                <button
                  onClick={() => { setMobileMenuOpen(false); logout(); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-500 hover:text-danger-400 hover:bg-danger-500/5 w-full"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ────────── MAIN CONTENT ────────── */}
      <main className="flex-1 md:ml-[232px] min-h-screen">
        <div className="max-w-3xl mx-auto px-4 md:px-8 pt-[72px] md:pt-8 pb-24 md:pb-8">
          <Outlet />
        </div>
      </main>

      {/* ────────── MOBILE BOTTOM TAB BAR ────────── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#0D1220] border-t border-border z-40 flex">
        {navItems.map(item => {
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex-1 flex flex-col items-center gap-1 py-3 transition-colors"
            >
              <item.icon className={`w-5 h-5 ${active ? 'text-brand-400' : 'text-slate-600'}`} />
              <span className={`text-[10px] font-semibold ${active ? 'text-brand-400' : 'text-slate-600'}`}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

/* ─────────────────────────────────────────────
   ADMIN LAYOUT
   Desktop: fixed left sidebar
   Mobile: top header + hamburger
──────────────────────────────────────────────*/
export function AdminLayout() {
  const location = useLocation();
  const { logout } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/admin/operations',    icon: Activity,    label: 'Operations'      },
    { path: '/admin/fraud',         icon: ShieldCheck, label: 'Fraud'           },
    { path: '/admin/workers',       icon: Users,       label: 'Workers'         },
    { path: '/admin/claims-review', icon: FileText,    label: 'Claims Review'   },
    { path: '/admin/analytics',     icon: BarChart3,   label: 'Analytics'       },
    { path: '/admin/demo',          icon: PlayCircle,  label: 'Demo Panel', badge: 'LIVE' },
  ];

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-background text-slate-300 flex">

      {/* ────────── DESKTOP SIDEBAR ────────── */}
      <aside className="hidden md:flex flex-col w-[232px] shrink-0 bg-[#0D1220] border-r border-border fixed top-0 left-0 h-screen z-40 overflow-y-auto">
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-glow-sm">
              <Hexagon className="w-4 h-4 text-white fill-white/20" />
            </div>
            <div>
              <p className="font-display font-bold text-slate-100 text-[15px] leading-none">Allievo</p>
              <p className="text-[10px] text-slate-500 font-medium mt-0.5 uppercase tracking-widest">Admin Console</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest px-2 py-2">Modules</p>
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive(item.path)
                  ? 'bg-brand-500/12 text-brand-400 font-semibold'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              <item.icon className={`w-4 h-4 shrink-0 ${isActive(item.path) ? 'text-brand-500' : 'text-slate-600'}`} />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-brand-500/15 text-brand-400 border border-brand-500/20">
                  {item.badge}
                </span>
              )}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-border">
          <button
            onClick={logout}
            className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:text-danger-400 hover:bg-danger-500/5 transition-all w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ────────── MOBILE TOP BAR ────────── */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[#0D1220] border-b border-border flex items-center px-4 z-40">
        <div className="flex items-center gap-2.5 flex-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Hexagon className="w-3.5 h-3.5 text-white fill-white/20" />
          </div>
          <div>
            <span className="font-display font-bold text-slate-100 text-base">Allievo</span>
            <span className="text-[10px] text-slate-500 ml-1.5">Admin</span>
          </div>
        </div>
        <button
          onClick={() => setMobileMenuOpen(v => !v)}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/5"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* ────────── MOBILE MENU ────────── */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 bg-black/50 z-30"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ y: -8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -8, opacity: 0 }}
              className="md:hidden fixed top-14 left-0 right-0 bg-[#0D1220] border-b border-border z-40 p-3 space-y-1"
            >
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(item.path) ? 'bg-brand-500/12 text-brand-400' : 'text-slate-400 hover:bg-white/5'
                  }`}
                >
                  <item.icon className={`w-4 h-4 ${isActive(item.path) ? 'text-brand-400' : 'text-slate-600'}`} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-brand-500/15 text-brand-400 border border-brand-500/20">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
              <div className="border-t border-border pt-2">
                <button
                  onClick={() => { setMobileMenuOpen(false); logout(); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-500 hover:text-danger-400 w-full"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ────────── MAIN CONTENT ────────── */}
      <main className="flex-1 md:ml-[232px] min-h-screen">
        <div className="px-4 md:px-8 pt-[72px] md:pt-8 pb-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
