import React from "react";
import { Check, Sparkles } from "lucide-react";
import { Card } from "../shared/Card";
import { Button } from "../shared/Button";
import type { Tier } from "../../types";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TierCardProps {
  tier: Tier;
  name: string;
  premium: number;
  maxPayout: number;
  features: string[];
  recommended?: boolean;
  selected?: boolean;
  onSelect?: (tier: Tier) => void;
  ctaText?: string;
  className?: string;
}

export const TierCard: React.FC<TierCardProps> = ({
  tier,
  name,
  premium,
  maxPayout,
  features,
  recommended,
  selected,
  onSelect,
  ctaText = "Select Plan",
  className,
}) => {
  return (
    <Card
      onClick={() => onSelect?.(tier)}
      variant={selected ? "elevated" : "outline"}
      className={cn(
        "relative transition-all duration-300 border-2 overflow-hidden group",
        selected ? "border-primary-600 ring-4 ring-primary-50" : "border-gray-100 hover:border-primary-200",
        className
      )}
    >
      {recommended && (
        <div className="absolute top-0 right-0 bg-amber-400 text-amber-900 px-3 py-1 rounded-bl-2xl flex items-center gap-1.5 font-bold text-[10px] uppercase tracking-wider shadow-sm z-10">
          <Sparkles className="w-3 h-3" /> Recommended
        </div>
      )}

      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{name}</h3>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-2xl font-bold text-primary-600">₹{premium}</span>
            <span className="text-xs font-semibold text-gray-400">/ week</span>
          </div>
        </div>
        <div className="text-right bg-primary-50 px-3 py-2 rounded-2xl border border-primary-100">
          <p className="text-[10px] font-bold text-primary-600 uppercase tracking-widest leading-none mb-1">
            Max Payout
          </p>
          <p className="text-lg font-bold text-primary-700">₹{maxPayout}</p>
        </div>
      </div>

      <div className="space-y-3 mb-8">
        {features.map((feat, i) => (
          <div key={i} className="flex items-center gap-3 text-sm font-medium text-gray-600">
            <div className="w-5 h-5 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0">
              <Check className="w-3 h-3 text-emerald-600 stroke-[3]" />
            </div>
            {feat}
          </div>
        ))}
      </div>

      <Button
        variant={selected ? "primary" : "secondary"}
        className="w-full font-bold py-3.5 group-hover:bg-primary-600 group-hover:text-white transition-all"
        onClick={(e) => {
          e.stopPropagation();
          onSelect?.(tier);
        }}
      >
        {selected && <Check className="w-4 h-4 mr-2 stroke-[3]" />}
        {selected ? "Subscribed" : ctaText}
      </Button>
    </Card>
  );
};
