import React from "react";
import { AlertCircle, CloudRain, ShieldCheck, Zap } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type AlertType = "rain" | "heat" | "aqi" | "outage" | "info";

interface AlertBannerProps {
  type?: AlertType;
  title: string;
  description: string;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ type = "info", title, description, className }) => {
  const styles = {
    rain: "bg-blue-50 border-blue-100 text-blue-800",
    heat: "bg-orange-50 border-orange-100 text-orange-800",
    aqi: "bg-amber-50 border-amber-100 text-amber-800",
    outage: "bg-rose-50 border-rose-100 text-rose-800",
    info: "bg-emerald-50 border-emerald-100 text-emerald-800",
  };

  const icons = {
    rain: <CloudRain className="w-5 h-5 text-blue-500" />,
    heat: <AlertCircle className="w-5 h-5 text-orange-500" />,
    aqi: <AlertCircle className="w-5 h-5 text-amber-500" />,
    outage: <Zap className="w-5 h-5 text-rose-500" />,
    info: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
  };

  return (
    <div className={cn("flex gap-4 p-4 rounded-2xl border animate-fade-in", styles[type], className)}>
      <div className="flex-shrink-0 animate-pulse-slow">{icons[type]}</div>
      <div className="flex-1">
        <h4 className="font-bold text-sm leading-tight mb-1">{title}</h4>
        <p className="text-xs opacity-90 leading-relaxed font-medium">{description}</p>
      </div>
    </div>
  );
};
