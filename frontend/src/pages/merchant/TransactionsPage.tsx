import React from 'react';
import { useDispatch } from 'react-redux';
import { Plus, CreditCard, RefreshCw } from 'lucide-react';
import { useGetTransactionsQuery } from '../../api/apiSlice';
import { setActiveModal } from '../../store/slices/uiSlice';
import { Button } from '../../components/common/Button';
import { TransactionTable } from '../../components/payments/TransactionTable';

export const TransactionsPage: React.FC = () => {
  const dispatch = useDispatch();
  const { data: transactions = [], isLoading, refetch } = useGetTransactionsQuery();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <CreditCard className="w-6 h-6 text-brand-400" />
            Payments & General Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete audit trail of processed charges, card checkouts, and sandbox settlement triggers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => dispatch(setActiveModal('NEW_PAYMENT'))}
          >
            Initialize Payment
          </Button>
        </div>
      </div>

      {/* Transaction Table */}
      <TransactionTable transactions={transactions} isLoading={isLoading} />
    </div>
  );
};
