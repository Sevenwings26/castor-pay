import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { CheckCircle2 } from 'lucide-react';
import { RootState } from '../../store/store';
import { useCreateVirtualAccountMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { Currency } from '../../types';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface CreateVirtualAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateVirtualAccountModal: React.FC<CreateVirtualAccountModalProps> = ({
  isOpen,
  onClose,
}) => {
  const dispatch = useDispatch();
  const selectedCurrency = useSelector((state: RootState) => state.auth.selectedCurrency);

  const [currency, setCurrency] = useState<Currency>(selectedCurrency);
  const [customerName, setCustomerName] = useState('Tunde Bakare');
  const [customerEmail, setCustomerEmail] = useState('tunde@test.com');
  const [merchantCustomerId, setMerchantCustomerId] = useState(() => `cust_${Date.now().toString().slice(-6)}`);
  const [bvn, setBvn] = useState('22233344455');

  const [createAccount, { isLoading }] = useCreateVirtualAccountMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await createAccount({
        currency,
        customer_name: customerName,
        customer_email: customerEmail,
        merchant_customer_id: merchantCustomerId,
        bvn: currency === 'NGN' ? bvn : undefined,
      }).unwrap();

      dispatch(
        addToast({
          type: 'success',
          title: 'Virtual Account Created',
          message: `Issued ${res.currency} account ${res.account_number} at ${res.bank_name}`,
        })
      );
      onClose();
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Issuance Failed',
          message: err?.data?.detail || 'Failed to issue dedicated virtual account.',
        })
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Issue Dedicated Virtual Account (DVA)"
      subtitle="Generates dedicated collection bank account in NGN, GBP, or USD."
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Currency & Rail</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { curr: 'NGN', rail: 'NUBAN (Providus)' },
              { curr: 'GBP', rail: 'Sort Code (ClearBank)' },
              { curr: 'USD', rail: 'ACH/Fedwire (Evolve)' },
            ].map(({ curr, rail }) => (
              <button
                key={curr}
                type="button"
                onClick={() => setCurrency(curr as Currency)}
                className={`p-2.5 rounded-lg border text-left transition-all ${
                  currency === curr
                    ? 'bg-brand-600/20 text-brand-300 border-brand-500/50'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                }`}
              >
                <div className="font-bold text-xs">{curr}</div>
                <div className="text-[10px] text-slate-400">{rail}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Customer Full Name</label>
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="e.g. Tunde Bakare"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Customer Email</label>
          <input
            type="email"
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="e.g. tunde@test.com"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Customer Identifier</label>
            <input
              type="text"
              value={merchantCustomerId}
              onChange={(e) => setMerchantCustomerId(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="cust_109283"
            />
          </div>
          {currency === 'NGN' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">BVN (KYC Verification)</label>
              <input
                type="text"
                value={bvn}
                onChange={(e) => setBvn(e.target.value)}
                maxLength={11}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                placeholder="22233344455"
              />
            </div>
          )}
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
            Issue Account
          </Button>
        </div>
      </form>
    </Modal>
  );
};
