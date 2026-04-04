import React from "react";
import { Check } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface StepperProps {
  currentStep: number;
  totalSteps: number;
  className?: string;
}

export const Stepper: React.FC<StepperProps> = ({ currentStep, totalSteps, className }) => {
  return (
    <div className={cn("w-full py-4", className)}>
      <div className="flex items-center justify-between relative mb-4">
        {/* Progress Line */}
        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-200 -translate-y-1/2 z-0" />
        <div
          className="absolute top-1/2 left-0 h-0.5 bg-primary-600 -translate-y-1/2 z-0 transition-all duration-500"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        />

        {/* Steps */}
        {Array.from({ length: totalSteps }).map((_, i) => {
          const step = i + 1;
          const isCompleted = step < currentStep;
          const isActive = step === currentStep;

          return (
            <div key={step} className="relative z-10 flex flex-col items-center">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 border-2",
                  isCompleted && "bg-primary-600 border-primary-600 text-white",
                  isActive && "bg-white border-primary-600 text-primary-600 scale-110 shadow-lg ring-4 ring-primary-50",
                  !isCompleted && !isActive && "bg-white border-gray-300 text-gray-400"
                )}
              >
                {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : <span className="text-xs font-bold">{step}</span>}
              </div>
            </div>
          );
        })}
      </div>
      <div className="text-center text-[10px] font-bold text-gray-400 uppercase tracking-widest animate-pulse">
        Step {currentStep} of {totalSteps}
      </div>
    </div>
  );
};
