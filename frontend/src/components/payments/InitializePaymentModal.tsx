import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RefreshCw, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { RootState } from '../../store/store';
import { useInitializePaymentMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { Currency } from '../../types';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface InitializePaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const InitializePaymentModal: React.FC<InitializePaymentModalProps> = ({
  isOpen,
  onClose,
}) => {
  const dispatch = useDispatch();
  const selectedCurrency = useSelector((state: RootState) => state.auth.selectedCurrency);

  const [amount, setAmount] = useState<string>('2500.00');
  const [currency, setCurrency] = useState<Currency>(selectedCurrency);
  const [customerEmail, setCustomerEmail] = useState<string>('gamer@ab-inbev.com');
  const [customerName, setCustomerName] = useState<string>('Alex Gamer');
  const [paymentMethod, setPaymentMethod] = useState<string>('CARD');
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() =>
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `idem_${Date.now()}`
  );

  const [initializePayment, { isLoading }] = useInitializePaymentMutation();

  const handleGenerateNewKey = () => {
    setIdempotencyKey(
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `idem_${Date.now()}`
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Invalid Amount',
          message: 'Please enter a valid positive payment amount.',
        })
      );
      return;
    }

    // Convert major unit to minor integer unit (e.g. 2,500.00 NGN -> 250,000 kobo)
    const minorAmount = Math.round(numericAmount * 100);

    try {
      const response = await initializePayment({
        amount: minorAmount,
        currency,
        customer_email: customerEmail,
        customer_name: customerName,
        payment_method: paymentMethod,
        idempotency_key: idempotencyKey,
      }).unwrap();

      dispatch(
        addToast({
          type: 'success',
          title: 'Payment Initialized',
          message: `Ref: ${response.reference} (${response.status}) via ${response.provider}`,
        })
      );
      onClose();
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Initialization Failed',
          message: err?.data?.detail || err?.data?.error?.message || 'Payment initiation error.',
        })
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Initialize New Payment"
      subtitle="Creates a payment transaction with distributed idempotency lock."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Idempotency Key Notice */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <ShieldAlert className="w-3.5 h-3.5 text-brand-400" />
              Distributed Idempotency Protection
            </span>
            <button
              type="button"
              onClick={handleGenerateNewKey}
              className="text-brand-400 hover:text-brand-300 flex items-center gap-1 text-[11px]"
            >
              <RefreshCw className="w-3 h-3" />
              Regenerate
            </button>
          </div>
          <div className="font-mono text-[11px] text-slate-400 break-all bg-slate-900 px-2 py-1 rounded border border-slate-800">
            Idempotency-Key: {idempotencyKey}
          </div>
        </div>

        {/* Amount & Currency */}
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Amount ({currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="e.g. 2500.00"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Currency
            </label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="NGN">NGN (₦)</option>
              <option value="GBP">GBP (£)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
            </select>
          </div>
        </div>

        {/* Customer Email & Name */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Customer Email
            </label>
            <input
              type="email"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="gamer@domain.com"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Customer Name
            </label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Alex Gamer"
            />
          </div>
        </div>

        {/* Payment Method */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Payment Rail / Method
          </label>
          <div className="grid grid-cols-3 gap-2">
            {['CARD', 'BANK_TRANSFER', 'VIRTUAL_ACCOUNT'].map((method) => (
              <button
                key={method}
                type="button"
                onClick={() => setPaymentMethod(method)}
                className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-all ${
                  paymentMethod === method
                    ? 'bg-brand-600/20 text-brand-400 border-brand-500/50'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                }`}
              >
                {method.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            size="sm"
            isLoading={isLoading}
            icon={<CheckCircle2 className="w-4 h-4" />}
          >
            Authorize Payment
          </Button>
        </div>
      </form>
    </Modal>
  );
};
