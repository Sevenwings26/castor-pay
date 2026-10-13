import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Wallet,
  Lock,
  ArrowUpRight,
  Plus,
  Building2,
  ArrowLeftRight,
  CreditCard,
} from 'lucide-react';
import { RootState } from '../../store/store';
import { useGetBalancesQuery, useGetTransactionsQuery } from '../../api/apiSlice';
import { setActiveModal } from '../../store/slices/uiSlice';
import { formatMinorUnits } from '../../utils/formatters';
import { Currency } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { Button } from '../../components/common/Button';
import { TransactionTable } from '../../components/payments/TransactionTable';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const dispatch = useDispatch();
  const selectedCurrency = useSelector((state: RootState) => state.auth.selectedCurrency);

  const { data: balancesData, isLoading: isBalancesLoading } = useGetBalancesQuery();
  const { data: transactions = [], isLoading: isTxLoading } = useGetTransactionsQuery();

  const currentBal = balancesData?.balances?.[selectedCurrency] || { available: 0, escrow: 0 };

  const currencies: Currency[] = ['NGN', 'GBP', 'USD', 'EUR'];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">
            Treasury & Ledger Overview
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-currency double-entry ledger wallets and transaction velocity.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => dispatch(setActiveModal('NEW_PAYMENT'))}
          >
            New Payment
          </Button>
          <Button
            size="sm"
            variant="secondary"
            icon={<Building2 className="w-4 h-4 text-brand-400" />}
            onClick={() => dispatch(setActiveModal('CREATE_VA'))}
          >
            Issue DVA
          </Button>
          <Button
            size="sm"
            variant="secondary"
            icon={<ArrowLeftRight className="w-4 h-4 text-brand-400" />}
            onClick={() => onNavigate('fx')}
          >
            FX Swap
          </Button>
        </div>
      </div>

      {/* Multi-Currency Balances Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {currencies.map((curr) => {
          const bal = balancesData?.balances?.[curr] || { available: 0, escrow: 0 };
          const isSelected = selectedCurrency === curr;
          return (
            <div
              key={curr}
              className={`rounded-xl border p-5 transition-all ${
                isSelected
                  ? 'bg-slate-900 border-brand-500/50 shadow-md ring-1 ring-brand-500/20'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold font-mono text-slate-400">{curr} Wallet</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                    isSelected
                      ? 'bg-brand-500/20 text-brand-300'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {curr}
                </span>
              </div>

              <div className="text-2xl font-black font-mono tracking-tight text-slate-100">
                {isBalancesLoading ? '...' : formatMinorUnits(bal.available, curr)}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 text-[11px]">
                  <Lock className="w-3 h-3 text-amber-400" /> Escrow Locked:
                </span>
                <span className="font-mono text-slate-300 font-semibold text-[11px]">
                  {formatMinorUnits(bal.escrow, curr)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Processed Transactions"
          value={transactions.length}
          subtitle="Processed via pluggable provider rails"
          icon={<CreditCard className="w-4 h-4" />}
          trend="+12% today"
        />
        <StatCard
          title="Available Spendable Float"
          value={formatMinorUnits(currentBal.available, selectedCurrency)}
          subtitle={`Cleared in primary ${selectedCurrency} ledger`}
          icon={<Wallet className="w-4 h-4" />}
        />
        <StatCard
          title="Escrow Reserve Collateral"
          value={formatMinorUnits(currentBal.escrow, selectedCurrency)}
          subtitle="Awaiting milestone release"
          icon={<Lock className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Recent Transactions Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-bold text-slate-100">Recent Transactions</h3>
            <p className="text-xs text-slate-400">
              Live double-entry postings with distributed idempotency validation.
            </p>
          </div>
          <button
            onClick={() => onNavigate('transactions')}
            className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-semibold"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <TransactionTable
          transactions={transactions.slice(0, 5)}
          isLoading={isTxLoading}
        />
      </div>
    </div>
  );
};
