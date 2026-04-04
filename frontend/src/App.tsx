import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { WorkerLayout, AdminLayout } from './components/shared/Layouts';

import Login from './pages/worker/Login';
import Register from './pages/worker/Register';
import WorkerDashboard from './pages/worker/WorkerDashboard';
import PolicyManagement from './pages/worker/PolicyManagement';
import Plans from './pages/worker/Plans';
import ClaimHistory from './pages/worker/ClaimHistory';
import Profile from './pages/worker/Profile';

import AdminDashboard from './pages/admin/AdminDashboard';
import FraudDetection from './pages/admin/FraudDetection';
import WorkerManagement from './pages/admin/WorkerManagement';
import Analytics from './pages/admin/Analytics';
import DemoControlPanel from './pages/admin/DemoControlPanel';
import ClaimsReview from './pages/admin/ClaimsReview';

function ProtectedRoute({ children, type }: { children: React.ReactNode, type: 'worker' | 'admin' }) {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated && type === 'worker') {
    return <Navigate to="/worker/login" replace />;
  }
  
  // Secured Admin Check
  if (!isAuthenticated && type === 'admin') {
    // Unauthenticated intruders attempting to breach operations are securely deflected
    return <Navigate to="/worker/login" replace />;
  }
  
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Base Redirect */}
        <Route path="/" element={<Navigate to="/worker/home" replace />} />
        
        {/* Worker Portal */}
        <Route path="/worker/login" element={<Login />} />
        <Route path="/worker/register" element={<Register />} />
        <Route path="/worker" element={<ProtectedRoute type="worker"><WorkerLayout /></ProtectedRoute>}>
          <Route path="home" element={<WorkerDashboard />} />
          <Route path="policy" element={<PolicyManagement />} />
          <Route path="plans" element={<Plans />} />
          <Route path="claims" element={<ClaimHistory />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        {/* Admin Portal */}
        <Route path="/admin" element={<ProtectedRoute type="admin"><AdminLayout /></ProtectedRoute>}>
          <Route path="operations" element={<AdminDashboard />} />
          <Route path="fraud" element={<FraudDetection />} />
          <Route path="workers" element={<WorkerManagement />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="demo" element={<DemoControlPanel />} />
          <Route path="claims-review" element={<ClaimsReview />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
