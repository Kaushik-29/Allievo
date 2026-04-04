import React from "react";
import { TrendingUp, Info } from "lucide-react";
import { Card } from "../shared/Card";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface PredictionCardProps {
  amount: number;
  confidence: number;
  className?: string;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ amount, confidence, className }) => {
  return (
    <Card
      variant="glass"
      className={cn("bg-indigo-600 border-none text-white overflow-hidden relative group", className)}
    >
      <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:scale-110 transition-transform">
        <TrendingUp className="w-24 h-24 stroke-[1.5]" />
      </div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold text-indigo-100 uppercase tracking-widest leading-none">
            Expected Payout
          </h4>
          <Info className="w-4 h-4 text-indigo-200 opacity-60" />
        </div>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-black italic">₹{amount}</span>
          <span className="text-xs font-bold text-indigo-200">/ event</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-white/20 rounded-full overflow-hidden">
            <div
              className={cn("h-full bg-emerald-400 transition-all duration-1000", `w-[${confidence}%]`)}
              style={{ width: `${confidence}%` }}
            />
          </div>
          <span className="text-[10px] font-black uppercase text-emerald-300">
            {confidence}% Confidence
          </span>
        </div>
      </div>
    </Card>
  );
};
