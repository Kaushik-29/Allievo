import React from "react";
import { Award, Star } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface LoyaltyBadgeProps {
  weeks: number;
  className?: string;
}

export const LoyaltyBadge: React.FC<LoyaltyBadgeProps> = ({ weeks, className }) => {
  const getTier = () => {
    if (weeks >= 12) return { label: "Elite Partner", color: "bg-indigo-500", icon: <Award className="w-4 h-4" /> };
    if (weeks >= 4) return { label: "Gold Partner", color: "bg-amber-500", icon: <Star className="w-4 h-4" /> };
    return { label: "Standard Partner", color: "bg-primary-500", icon: null };
  };

  const tier = getTier();

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl shadow-lg border border-white/20 text-white font-bold text-xs transition-all duration-300", tier.color, className)}>
      {tier.icon}
      <span>{weeks} Weeks Active</span>
    </div>
  );
};
