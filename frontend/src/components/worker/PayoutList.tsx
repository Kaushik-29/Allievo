import React from "react";
import { Badge, type BadgeVariant } from "../shared/Badge";
import { Card } from "../shared/Card";
import { ChevronRight } from "lucide-react";
import type { Claim } from "../../types";

interface PayoutListProps {
  payouts: Claim[];
  onClaimClick?: (claim: Claim) => void;
}

export const PayoutList: React.FC<PayoutListProps> = ({ payouts, onClaimClick }) => {
  const getStatusVariant = (status: Claim["status"]): BadgeVariant => {
    switch (status) {
      case "approved":
        return "success";
      case "partial":
        return "warning";
      case "held":
        return "warning";
      case "blocked":
      case "rejected":
        return "error";
      default:
        return "neutral";
    }
  };

  const getLabel = (status: Claim["status"]) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="space-y-4">
      {payouts.map((payout) => (
        <Card
          key={payout.id}
          padding="sm"
          variant="outline"
          onClick={onClaimClick ? () => onClaimClick(payout) : undefined}
          className="flex items-center justify-between hover:border-primary-200 transition-colors"
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-bold text-gray-900">₹{payout.cappedAmount}</h4>
              <Badge variant={getStatusVariant(payout.status)} dot>
                {getLabel(payout.status)}
              </Badge>
            </div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              {payout.triggerType.replace("_", " ")} • {payout.triggerDate}
            </p>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-300" />
        </Card>
      ))}
    </div>
  );
};
