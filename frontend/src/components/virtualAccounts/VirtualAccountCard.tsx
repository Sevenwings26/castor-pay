import React, { useState } from 'react';
import { Copy, Check, Building2, User, Hash } from 'lucide-react';
import { VirtualAccount } from '../../types';
import { Badge, getStatusBadgeVariant } from '../common/Badge';

interface VirtualAccountCardProps {
  account: VirtualAccount;
  onSimulateDeposit?: (account: VirtualAccount) => void;
}

export const VirtualAccountCard: React.FC<VirtualAccountCardProps> = ({
  account,
  onSimulateDeposit,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(account.account_number);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currencyGradients: Record<string, string> = {
    NGN: 'from-emerald-950/40 to-slate-900 border-emerald-900/40',
    GBP: 'from-blue-950/40 to-slate-900 border-blue-900/40',
    USD: 'from-indigo-950/40 to-slate-900 border-indigo-900/40',
    EUR: 'from-amber-950/40 to-slate-900 border-amber-900/40',
  };

  const gradient = currencyGradients[account.currency] || 'from-slate-900 to-slate-950 border-slate-800';

  return (
    <div
      className={`bg-gradient-to-br ${gradient} border rounded-xl p-5 shadow-lg relative flex flex-col justify-between`}
    >
      <div>
        {/* Card Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-brand-400">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100">{account.bank_name}</div>
              <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
                Dedicated Virtual Account
              </div>
            </div>
          </div>
          <Badge variant={getStatusBadgeVariant(account.status)}>
            {account.currency}
          </Badge>
        </div>

        {/* Account Number with 1-Click Copy */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 my-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1 flex items-center justify-between">
            <span>Account Number</span>
            {account.routing_code && (
              <span className="font-mono text-slate-400">
                Code: {account.routing_code}
              </span>
            )}
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xl font-bold tracking-wider text-brand-300">
              {account.account_number}
            </span>
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Copy account number"
            >
              {copied ? (
                <Check className="w-4 h-4 text-emerald-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Account Details */}
        <div className="space-y-1.5 text-xs text-slate-300 pt-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" /> Beneficiary:
            </span>
            <span className="font-medium text-slate-200">{account.account_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5" /> Customer ID:
            </span>
            <span className="font-mono text-[11px] text-slate-400">{account.merchant_customer_id}</span>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      {onSimulateDeposit && (
        <div className="mt-4 pt-3 border-t border-slate-800/80">
          <button
            onClick={() => onSimulateDeposit(account)}
            className="w-full py-1.5 px-3 rounded-lg text-xs font-semibold bg-brand-600/15 hover:bg-brand-600/25 text-brand-400 border border-brand-500/30 transition-colors"
          >
            ⚡ Simulate Inbound Bank Transfer
          </button>
        </div>
      )}
    </div>
  );
};
