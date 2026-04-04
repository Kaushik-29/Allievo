import React from "react";
import { ArrowUpRight, ArrowDownRight, Info } from "lucide-react";
import { Card } from "../shared/Card";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: {
    value: number;
    isUp: boolean;
  };
  icon?: React.ReactNode;
  description?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  trend,
  icon,
  description,
  className,
}) => {
  return (
    <Card className={cn("relative group transition-all duration-300", className)}>
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-gray-50 rounded-2xl group-hover:bg-primary-50 transition-colors">
          {icon}
        </div>
        {trend && (
          <div
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold font-mono",
              trend.isUp ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
            )}
          >
            {trend.isUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {trend.value}%
          </div>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest leading-none">
          {label}
        </p>
        <h3 className="text-3xl font-black text-gray-900 leading-none">{value}</h3>
      </div>

      {description && (
        <div className="mt-4 pt-4 border-t border-gray-50 flex items-center gap-2 opacity-60">
          <Info className="w-3 h-3" />
          <p className="text-[10px] font-bold text-gray-400">{description}</p>
        </div>
      )}
    </Card>
  );
};
