import { BarChart3, TrendingDown, TrendingUp, AlertTriangle } from "lucide-react";
import { Card } from "../../components/shared/Card";

export default function Analytics() {
  return (
    <div className="p-8 space-y-8 animate-fade-in max-w-7xl mx-auto">
      <header className="mb-8">
        <h2 className="text-3xl font-black text-gray-900 leading-tight italic uppercase tracking-tighter">Deep Analytics</h2>
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">Loss ratios and zone risk chronological trends</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
         <Card className="p-6 bg-gradient-to-br from-indigo-500 to-indigo-700 text-white">
            <TrendingDown className="w-8 h-8 text-indigo-200 mb-4" />
            <h3 className="text-3xl font-black italic">68.4%</h3>
            <p className="text-xs font-bold text-indigo-200 uppercase tracking-widest mt-1">Global Loss Ratio</p>
         </Card>
         <Card className="p-6 bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
            <TrendingUp className="w-8 h-8 text-emerald-200 mb-4" />
            <h3 className="text-3xl font-black italic">₹1.2M</h3>
            <p className="text-xs font-bold text-emerald-200 uppercase tracking-widest mt-1">Net Premium Earned (MTD)</p>
         </Card>
         <Card className="p-6 bg-gradient-to-br from-rose-500 to-rose-700 text-white">
            <AlertTriangle className="w-8 h-8 text-rose-200 mb-4" />
            <h3 className="text-3xl font-black italic">14%</h3>
            <p className="text-xs font-bold text-rose-200 uppercase tracking-widest mt-1">Fraud Rejection Rate</p>
         </Card>
      </div>

      <Card className="p-8 mt-6">
         <div className="text-center py-20 opacity-50">
            <BarChart3 className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="font-bold text-gray-500">Detailed Cohort Analysis</h3>
            <p className="text-sm text-gray-400 mt-2">Connect to Snowflake/BigQuery warehouse to view comprehensive cohort retention and risk charts.</p>
         </div>
      </Card>
    </div>
  );
}
