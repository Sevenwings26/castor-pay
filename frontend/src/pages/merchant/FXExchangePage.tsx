import React from 'react';
import { ArrowLeftRight } from 'lucide-react';
import { BenchmarkRatesTicker } from '../../components/fx/BenchmarkRatesTicker';
import { FXQuoteWidget } from '../../components/fx/FXQuoteWidget';

export const FXExchangePage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
          <ArrowLeftRight className="w-6 h-6 text-brand-400" />
          Cross-Border FX & Rate Lock Protocol
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Lock exchange rates with zero slippage for 60 seconds and settle balances across multi-currency ledger accounts.
        </p>
      </div>

      {/* Live Benchmark Rates Banner */}
      <BenchmarkRatesTicker />

      {/* Interactive 60s Rate Lock & Swap Calculator */}
      <FXQuoteWidget />
    </div>
  );
};
