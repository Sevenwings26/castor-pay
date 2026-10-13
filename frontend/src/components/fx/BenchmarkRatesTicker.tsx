import React from 'react';
import { TrendingUp, RefreshCw, Clock } from 'lucide-react';
import { useGetLiveRatesQuery } from '../../api/apiSlice';

export const BenchmarkRatesTicker: React.FC = () => {
  const { data, isLoading, refetch } = useGetLiveRatesQuery(undefined, {
    pollingInterval: 30000, // auto-refresh every 30s
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Real-Time Benchmark Exchange Rates
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1 font-mono">
            <Clock className="w-3 h-3 text-brand-400" />
            60s Rate Lock Guarantee
          </span>
        </div>
        <button
          onClick={() => refetch()}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-slate-800 transition-colors"
          title="Refresh rates"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {data?.benchmark_pairs?.map((pair) => (
          <div
            key={pair.pair}
            className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 flex items-center justify-between"
          >
            <div>
              <div className="text-[11px] font-bold text-slate-400 font-mono">{pair.pair}</div>
              <div className="text-sm font-extrabold text-slate-100 font-mono mt-0.5">
                {pair.rate > 10 ? pair.rate.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : pair.rate.toFixed(4)}
              </div>
            </div>
            <div className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
              Spread: {data.spread_bps} bps
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
