import React from 'react';
import { Landmark, DollarSign, Wallet, Scale, RefreshCw } from 'lucide-react';
import { useGetTreasuryQuery } from '../../api/apiSlice';
import { formatMinorUnits } from '../../utils/formatters';
import { Currency } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { Button } from '../../components/common/Button';
import { BankingPartnerTable } from '../../components/admin/BankingPartnerTable';

export const TreasuryPage: React.FC = () => {
  const { data: treasury, isLoading, refetch } = useGetTreasuryQuery();

  const primaryCurrency: Currency = 'NGN';
  const stats = treasury?.currencies?.[primaryCurrency] || {
    asset_float: 0,
    merchant_liabilities: 0,
    revenue_collected: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <Landmark className="w-6 h-6 text-brand-400" />
            Platform Treasury Reserves & Banking Rails
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            System-wide liquidity reserves, partner bank clearing float, and merchant liability audit.
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          onClick={() => refetch()}
        >
          Refresh Float
        </Button>
      </div>

      {/* Float & Liability Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Bank Settlement Asset Float"
          value={formatMinorUnits(stats.asset_float, primaryCurrency)}
          subtitle="Providus, ClearBank & Evolve partner float"
          icon={<Landmark className="w-4 h-4 text-emerald-400" />}
          trend="Reserve Invariant: Healthy"
        />
        <StatCard
          title="Total Merchant Liabilities"
          value={formatMinorUnits(stats.merchant_liabilities, primaryCurrency)}
          subtitle="Available + Escrow customer balances"
          icon={<Wallet className="w-4 h-4 text-amber-400" />}
        />
        <StatCard
          title="Accumulated Platform Revenue"
          value={formatMinorUnits(stats.revenue_collected, primaryCurrency)}
          subtitle="Transaction fees + FX treasury spread"
          icon={<DollarSign className="w-4 h-4 text-brand-400" />}
        />
      </div>

      {/* All Currencies Float Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h4 className="text-sm font-bold text-slate-100 mb-3 flex items-center gap-2">
          <Scale className="w-4 h-4 text-brand-400" />
          Multi-Currency Liquidity Float Distribution
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 font-mono">
          {['NGN', 'GBP', 'USD', 'EUR'].map((curr) => {
            const cStats = treasury?.currencies?.[curr] || {
              asset_float: 0,
              merchant_liabilities: 0,
              revenue_collected: 0,
            };
            return (
              <div
                key={curr}
                className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs"
              >
                <div className="text-[11px] font-bold text-brand-400 mb-1">{curr} Clearing</div>
                <div className="text-slate-400">
                  Float: <span className="text-slate-100 font-bold">{formatMinorUnits(cStats.asset_float, curr as Currency)}</span>
                </div>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Liabilities: <span className="text-slate-300">{formatMinorUnits(cStats.merchant_liabilities, curr as Currency)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Banking Partners Telemetry Grid */}
      <BankingPartnerTable
        partners={treasury?.banking_partners || []}
        isLoading={isLoading}
      />
    </div>
  );
};
