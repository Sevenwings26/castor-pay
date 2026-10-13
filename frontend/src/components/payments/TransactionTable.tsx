import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Search, CheckCircle, ArrowDownLeft, Clock } from 'lucide-react';
import { PaymentTransaction } from '../../types';
import { useSettlePaymentMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatMinorUnits, formatDate } from '../../utils/formatters';
import { Badge, getStatusBadgeVariant } from '../common/Badge';
import { Button } from '../common/Button';

interface TransactionTableProps {
  transactions: PaymentTransaction[];
  isLoading?: boolean;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  transactions,
  isLoading = false,
}) => {
  const dispatch = useDispatch();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const [settlePayment, { isLoading: isSettling }] = useSettlePaymentMutation();

  const handleSettle = async (transactionId: string, reference: string) => {
    try {
      await settlePayment({ transaction_id: transactionId }).unwrap();
      dispatch(
        addToast({
          type: 'success',
          title: 'Payment Settled',
          message: `Transaction ${reference} settled. Balanced journal entries posted to ledger.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Settlement Failed',
          message: err?.data?.detail || 'Unable to settle transaction.',
        })
      );
    }
  };

  const filtered = transactions.filter((tx) => {
    const matchesSearch =
      tx.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.customer_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tx.customer_name && tx.customer_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'ALL' || tx.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Table Filters Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search reference, email..."
            className="w-full bg-slate-800/80 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {['ALL', 'SUCCEEDED', 'PROCESSING', 'PENDING', 'FAILED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all ${
                statusFilter === st
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Transaction Ref</th>
              <th className="py-3 px-4">Customer</th>
              <th className="py-3 px-4">Amount</th>
              <th className="py-3 px-4">Rail / Provider</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4 text-right">Sandbox Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400">
                  <div className="flex items-center justify-center gap-2">
                    <Clock className="w-4 h-4 animate-spin text-brand-400" />
                    <span>Loading payment transactions from ledger...</span>
                  </div>
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-500">
                  <ArrowDownLeft className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <div className="font-semibold text-slate-400">No transactions found</div>
                  <div className="text-[11px] mt-0.5">
                    Initialize a payment or simulate an inbound virtual account transfer.
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                    <div className="flex items-center gap-1.5">
                      <span className="text-brand-400">{tx.reference}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-sans truncate max-w-[140px]">
                      ID: {tx.id}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-medium text-slate-200">{tx.customer_name || 'Guest'}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{tx.customer_email}</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <div className="font-bold text-slate-100">
                      {formatMinorUnits(tx.amount, tx.currency)}
                    </div>
                    {tx.fee > 0 && (
                      <div className="text-[10px] text-slate-500">
                        Fee: {formatMinorUnits(tx.fee, tx.currency)}
                      </div>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[11px] text-slate-300">
                      {tx.provider || 'MOCK_BANK'}
                    </span>
                    <div className="text-[10px] text-slate-400 mt-0.5 uppercase">
                      {tx.payment_method}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={getStatusBadgeVariant(tx.status)}>
                      {tx.status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                    {formatDate(tx.created_at)}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {tx.status === 'PROCESSING' || tx.status === 'PENDING' ? (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleSettle(tx.id, tx.reference)}
                        disabled={isSettling}
                        icon={<CheckCircle className="w-3.5 h-3.5" />}
                        className="text-[11px] py-1 px-2.5 bg-emerald-600 hover:bg-emerald-500"
                      >
                        1-Click Settle
                      </Button>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-mono">Settled</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
