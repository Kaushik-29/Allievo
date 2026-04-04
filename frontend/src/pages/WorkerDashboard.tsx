import { useDashboard, useProfile, useCurrentPolicy, useClaims } from "../api/queries";
import { Card } from "../components/shared/Card";
import { AlertBanner } from "../components/shared/AlertBanner";
import { RiskTrendChart } from "../components/charts/RiskTrendChart";
import { EarningsChart } from "../components/charts/EarningsChart";
import { PayoutList } from "../components/worker/PayoutList";
import { LoyaltyBadge } from "../components/worker/LoyaltyBadge";
import { PredictionCard } from "../components/worker/PredictionCard";
import { Button } from "../components/shared/Button";
import { useNavigate } from "react-router-dom";
import { Shield, TrendingUp, AlertCircle, ArrowUpRight, HelpCircle } from "lucide-react";

export default function WorkerDashboard() {
  const { data: profile } = useProfile();
  const { data: dashboard } = useDashboard();
  const { data: policy } = useCurrentPolicy();
  const { data: claims } = useClaims();
  const navigate = useNavigate();

  if (!dashboard || !profile || !policy || !claims) {
    return <div className="flex h-96 items-center justify-center animate-pulse text-gray-400 font-bold">FEEDS UPDATING...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* Welcome Header */}
      <div className="flex justify-between items-center bg-white p-6 rounded-[2.5rem] shadow-sm border border-gray-100">
        <div>
          <h2 className="text-2xl font-black text-gray-900 leading-tight">Hi, {profile.name}</h2>
          <div className="flex items-center gap-2 mt-1">
             <LoyaltyBadge weeks={profile.weeksActive} />
          </div>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Status</p>
          <div className="flex items-center gap-1.5 text-emerald-600 font-black italic text-lg">
            <Shield className="w-5 h-5" />
            COVERED
          </div>
        </div>
      </div>

      {/* Disruption Alert */}
      {dashboard.activeDisruptions.map((alert, i) => (
        <AlertBanner 
          key={i}
          type={alert.type as any}
          title={alert.type.toUpperCase() + " ALERT"}
          description={alert.description}
        />
      ))}

      {/* Primary Analytics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PredictionCard amount={dashboard.predictedPayout} confidence={92} />
        
        <Card variant="outline" className="flex flex-col justify-center border-2 border-primary-50 hover:border-primary-100 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Active Coverage</p>
            <TrendingUp className="w-4 h-4 text-primary-500" />
          </div>
          <h3 className="text-3xl font-black text-gray-900 leading-none mb-1 capitalize">{policy.tier} Tier</h3>
          <p className="text-xs font-bold text-gray-400 italic">Protects up to ₹{policy.maxPayout} / week</p>
          <Button 
            variant="ghost" 
            size="sm" 
            className="mt-4 w-fit px-0 text-primary-600 font-black hover:bg-transparent"
            onClick={() => navigate("/policy")}
          >
            MANAGE POLICY <ArrowUpRight className="ml-1 w-4 h-4" />
          </Button>
        </Card>
      </div>

      {/* Earnings Breakdown */}
      <section>
        <div className="flex justify-between items-end mb-4 px-2">
           <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Revenue Sync</h4>
           <div className="text-right">
              <p className="text-[8px] font-black text-gray-300 uppercase">Total Life Earnings</p>
              <p className="text-sm font-black text-gray-900 leading-none">₹{dashboard.totalEarnings.toLocaleString()}</p>
           </div>
        </div>
        <Card>
          <EarningsChart data={[
            { platform: "Zomato", amount: 4850 },
            { platform: "Swiggy", amount: 3620 },
            { platform: "Other", amount: 1450 }
          ]} />
        </Card>
      </section>

      {/* "Where is my payout?" Helper Card */}
      <Card variant="elevated" className="bg-gradient-to-br from-gray-900 to-gray-800 text-white border-none relative overflow-hidden group">
         <div className="absolute -right-4 -top-4 opacity-10 group-hover:rotate-12 transition-transform">
            <HelpCircle size={100} />
         </div>
         <div className="relative z-10">
            <h4 className="flex items-center gap-2 text-sm font-bold mb-3">
               <AlertCircle className="w-4 h-4 text-amber-400" />
               Missing Payout?
            </h4>
            <p className="text-xs text-gray-400 leading-relaxed font-medium mb-4">
               If you worked during a disruption but don't see a claim, it might be due to <strong>low GPS confidence</strong> or <strong>insufficient work hours</strong>.
            </p>
            <div className="flex gap-2">
               <Button size="sm" variant="secondary" className="bg-white/10 hover:bg-white/20 text-white border-none py-2 text-[10px]" onClick={() => navigate("/support")}>HOW IT WORKS</Button>
               <Button size="sm" variant="secondary" className="bg-white/10 hover:bg-white/20 text-white border-none py-2 text-[10px]" onClick={() => navigate("/support")}>RAISE TICKET</Button>
            </div>
         </div>
      </Card>

      {/* Risk Trend */}
      <section>
        <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 px-2">Zone Risk Momentum</h4>
        <Card>
          <RiskTrendChart data={dashboard.riskTrend} />
        </Card>
      </section>

      {/* Recent Payouts */}
      <section>
        <div className="flex justify-between items-center mb-4 px-2">
          <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Recent Activity</h4>
          <Button variant="ghost" size="sm" className="text-[10px] p-0" onClick={() => navigate("/claims")}>VIEW ALL</Button>
        </div>
        <PayoutList 
          payouts={claims.slice(0, 3)} 
          onClaimClick={() => navigate("/claims")} 
        />
      </section>
    </div>
  );
}
