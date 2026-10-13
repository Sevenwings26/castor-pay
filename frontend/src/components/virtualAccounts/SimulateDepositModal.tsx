import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Zap } from 'lucide-react';
import { VirtualAccount } from '../../types';
import { useSimulateDepositMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface SimulateDepositModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetAccount?: VirtualAccount | null;
}

export const SimulateDepositModal: React.FC<SimulateDepositModalProps> = ({
  isOpen,
  onClose,
  targetAccount,
}) => {
  const dispatch = useDispatch();

  const [accountNumber, setAccountNumber] = useState(targetAccount?.account_number || '');
  const [amount, setAmount] = useState('2500.00');
  const [senderName, setSenderName] = useState('Alhaji Dangote');
  const [senderBank, setSenderBank] = useState('Access Bank Plc');

  // Keep state in sync if targetAccount changes
  React.useEffect(() => {
    if (targetAccount) {
      setAccountNumber(targetAccount.account_number);
    }
  }, [targetAccount]);

  const [simulateDeposit, { isLoading }] = useSimulateDepositMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Invalid Amount',
          message: 'Please provide a valid deposit amount.',
        })
      );
      return;
    }

    const minorAmount = Math.round(numericAmount * 100);
    const sessionId = `NIP_SIM_${Date.now()}_${Math.floor(Math.random() * 10000)}`;

    try {
      const res = await simulateDeposit({
        account_number: accountNumber,
        amount: minorAmount,
        session_id: sessionId,
        sender_name: senderName,
        sender_bank: senderBank,
      }).unwrap();

      dispatch(
        addToast({
          type: 'success',
          title: 'Bank Deposit Credited!',
          message: `Received ${amount} ${res.currency || 'NGN'} from ${senderName}. Ledger wallet updated instantly.`,
        })
      );
      onClose();
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Deposit Simulation Failed',
          message: err?.data?.detail || 'Inbound deposit simulation failed.',
        })
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Simulate Inbound Bank Deposit"
      subtitle="Emulates an interbank transfer (NIP/Faster Payments) into the virtual account."
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Destination Account Number
          </label>
          <input
            type="text"
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="e.g. 9955623054"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Deposit Amount (Major Units)
          </label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="2500.00"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Sender Name</label>
            <input
              type="text"
              value={senderName}
              onChange={(e) => setSenderName(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Sender Bank</label>
            <input
              type="text"
              value={senderBank}
              onChange={(e) => setSenderBank(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
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
            icon={<Zap className="w-4 h-4 text-amber-400" />}
            className="bg-brand-600 hover:bg-brand-500"
          >
            Trigger Inbound Transfer
          </Button>
        </div>
      </form>
    </Modal>
  );
};
