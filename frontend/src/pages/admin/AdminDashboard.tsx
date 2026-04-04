import { useAdminStats } from "../../api/queries";
import { Card } from "../../components/shared/Card";
import { MetricCard } from "../../components/admin/MetricCard";
import { Button } from "../../components/shared/Button";
import { 
  Users, 
  Wallet, 
  Filter,
  BarChart3,
  Flame,
  ServerCrash
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis
} from "recharts";

export default function AdminDashboard() {
  const { data: stats } = useAdminStats();

  if (!stats) return <div className="flex h-screen items-center justify-center animate-pulse text-primary-600 font-bold">LOADING FLEET ANALYTICS...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-8 pb-20 max-w-7xl mx-auto animate-fade-in">
      {/* Admin Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-8 rounded-[3rem] border border-gray-100 shadow-sm">
        <div>
          <h2 className="text-3xl font-black text-gray-900 leading-tight italic uppercase tracking-tighter">Fleet Guardian Console</h2>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">Real-time Risk & Payout Monitoring</p>
        </div>
        <div className="flex gap-2">
           <Button variant="secondary" size="md" className="rounded-2xl border-2 border-gray-100 font-bold text-xs"><Filter className="w-4 h-4 mr-2" /> FILTER</Button>
           <Button 
              variant="primary" 
              size="md" 
              className="rounded-2xl font-bold text-xs shadow-lg shadow-rose-200 bg-rose-600 hover:bg-rose-700"
              onClick={() => alert("🚨 INITIATING SERVER CRASH TRIGGER: Systemically cascading micro-claims to all active Zomato drivers...")}
            >
              <ServerCrash className="w-4 h-4 mr-2" /> TRIGGER AWS OUTAGE
            </Button>
        </div>
      </header>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          label="Active Protections" 
          value={stats.activePolicies.toLocaleString()} 
          trend={{ value: 12.5, isUp: true }}
          icon={<Users className="w-6 h-6 text-primary-600" />}
          description="Total active worker policies"
        />
        <MetricCard 
          label="Total Premiums" 
          value={`₹${stats.totalPremiums.toLocaleString()}`} 
          trend={{ value: 8.2, isUp: true }}
          icon={<Wallet className="w-6 h-6 text-emerald-600" />}
          description="Gross premium written (week)"
        />
        <MetricCard 
          label="Loss Ratio" 
          value={`${stats.lossRatio}%`} 
          trend={{ value: 2.1, isUp: false }}
          icon={<BarChart3 className="w-6 h-6 text-amber-600" />}
          description="Current payout vs premium ratio"
        />
        <MetricCard 
          label="Fraud Ring Alarms" 
          value={stats.ringAlerts.length} 
          trend={{ value: 0, isUp: true }}
          icon={<Flame className="w-6 h-6 text-rose-600" />}
          description="Simulated clustering alerts"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Loss Ratio Trend (Area Chart) */}
        <section className="space-y-4">
           <div className="flex justify-between items-end px-4">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Loss Ratio Momentum</h4>
           </div>
           <Card className="p-8">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats.lossRatioTrend}>
                    <defs>
                      <linearGradient id="colorRatio" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                    <XAxis dataKey="month" axisLine={false} tickLine={false} style={{ fontSize: 10, fontWeight: "bold" }} />
                    <YAxis axisLine={false} tickLine={false} style={{ fontSize: 10, fontWeight: "bold" }} />
                    <Tooltip cursor={{ stroke: "#8b5cf6", strokeWidth: 2 }} contentStyle={{ borderRadius: '20px', border: 'none', boxShadow: '0 10px 40px rgba(0,0,0,0.1)' }} />
                    <Area type="monotone" dataKey="ratio" stroke="#8b5cf6" strokeWidth={4} fillOpacity={1} fill="url(#colorRatio)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
           </Card>
        </section>

        {/* Zone Risk Heatmap (Bubble Chart) */}
        <section className="space-y-4">
           <div className="flex justify-between items-end px-4">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Zone Risk Scatter</h4>
           </div>
           <Card className="p-8">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis type="number" dataKey="x" name="Workers" unit=" " axisLine={false} tickLine={false} hide />
                    <YAxis type="number" dataKey="y" name="Claims" unit=" " axisLine={false} tickLine={false} hide />
                    <ZAxis type="number" dataKey="z" range={[400, 4000]} name="Risk" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter name="Zone Risk" data={[
                      { x: 10, y: 30, z: 200, name: 'Koramangala' },
                      { x: 40, y: 50, z: 400, name: 'HSR' },
                      { x: 30, y: 70, z: 150, name: 'Indiranagar' },
                      { x: 60, y: 20, z: 300, name: 'Whitefield' },
                      { x: 20, y: 80, z: 500, name: 'Electronic City' },
                    ]} fill="#10b981">
                      {/* Bubble colors would vary in real version */}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 flex justify-center gap-4">
                 <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-500" /><span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Healthy</span></div>
                 <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-rose-500" /><span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">High Risk</span></div>
              </div>
           </Card>
        </section>
      </div>

    </div>
  );
}
