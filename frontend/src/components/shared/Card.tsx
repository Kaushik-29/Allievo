import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: "elevated" | "flat" | "outline" | "glass";
  padding?: "none" | "sm" | "md" | "lg";
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  onClick,
  variant = "elevated",
  padding = "md",
}) => {
  const variants = {
    elevated: "bg-white shadow-[0_10px_40px_-15px_rgba(0,0,0,0.1)] border border-gray-100/50",
    flat: "bg-gray-50 border border-gray-100",
    outline: "border-2 border-gray-100 bg-white",
    glass: "bg-white/70 backdrop-blur-md border border-white/20 shadow-xl",
  };

  const paddings = {
    none: "p-0",
    sm: "p-3",
    md: "p-4 sm:p-6",
    lg: "p-6 sm:p-8",
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "rounded-[2rem] transition-all duration-300",
        variants[variant],
        paddings[padding],
        onClick && "cursor-pointer active:scale-[0.99] hover:shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
};
