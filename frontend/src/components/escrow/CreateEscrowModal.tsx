import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Plus, Trash2, Lock } from 'lucide-react';
import { RootState } from '../../store/store';
import { useCreateEscrowContractMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { Currency } from '../../types';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface CreateEscrowModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MilestoneInput {
  title: string;
  amount: string; // major units
}

export const CreateEscrowModal: React.FC<CreateEscrowModalProps> = ({ isOpen, onClose }) => {
  const dispatch = useDispatch();
  const selectedCurrency = useSelector((state: RootState) => state.auth.selectedCurrency);

  const [title, setTitle] = useState('Gaming Tournament Prize Pool Escrow');
  const [buyerEmail, setBuyerEmail] = useState('sponsor@ab-inbev.com');
  const [sellerEmail, setSellerEmail] = useState('winner_team@esports.ng');
  const [currency, setCurrency] = useState<Currency>(selectedCurrency);
  const [milestones, setMilestones] = useState<MilestoneInput[]>([
    { title: 'Group Stage Deliverable', amount: '1000.00' },
    { title: 'Grand Finals Winner', amount: '1500.00' },
  ]);

  const [createEscrow, { isLoading }] = useCreateEscrowContractMutation();

  const handleAddMilestone = () => {
    setMilestones([...milestones, { title: '', amount: '500.00' }]);
  };

  const handleRemoveMilestone = (index: number) => {
    if (milestones.length <= 1) return;
    setMilestones(milestones.filter((_, i) => i !== index));
  };

  const handleMilestoneChange = (index: number, field: keyof MilestoneInput, value: string) => {
    const updated = [...milestones];
    updated[index][field] = value;
    setMilestones(updated);
  };

  const totalAmountMajor = milestones.reduce((sum, m) => {
    const n = parseFloat(m.amount);
    return sum + (isNaN(n) ? 0 : n);
  }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (milestones.length === 0 || totalAmountMajor <= 0) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Invalid Escrow',
          message: 'Please add at least one milestone with a valid amount.',
        })
      );
      return;
    }

    const minorTotal = Math.round(totalAmountMajor * 100);
    const formattedMilestones = milestones.map((m) => ({
      title: m.title || 'Milestone Deliverable',
      amount: Math.round(parseFloat(m.amount || '0') * 100),
    }));

    try {
      const res = await createEscrow({
        title,
        buyer_email: buyerEmail,
        seller_email: sellerEmail,
        currency,
        total_amount: minorTotal,
        milestones: formattedMilestones,
      }).unwrap();

      dispatch(
        addToast({
          type: 'success',
          title: 'Escrow Agreement Created',
          message: `Created contract ${res.contract_reference} with ${res.milestones.length} milestones.`,
        })
      );
      onClose();
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Escrow Creation Failed',
          message: err?.data?.detail || 'Unable to create escrow agreement.',
        })
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Escrow Agreement"
      subtitle="Conditional micropayments, game tournament pools, or contractor milestones."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Agreement Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="e.g. Esports Championship Escrow"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Buyer / Sponsor Email</label>
            <input
              type="email"
              value={buyerEmail}
              onChange={(e) => setBuyerEmail(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Seller / Payee Email</label>
            <input
              type="email"
              value={sellerEmail}
              onChange={(e) => setSellerEmail(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 items-center">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Currency</label>
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
          <div className="col-span-2 text-right">
            <span className="text-xs text-slate-400 block">Total Escrow Value</span>
            <span className="text-xl font-mono font-bold text-brand-300">
              {currency} {totalAmountMajor.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Milestones dynamic list */}
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Contract Milestones
            </label>
            <button
              type="button"
              onClick={handleAddMilestone}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-semibold"
            >
              <Plus className="w-3.5 h-3.5" /> Add Milestone
            </button>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {milestones.map((m, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  type="text"
                  value={m.title}
                  onChange={(e) => handleMilestoneChange(idx, 'title', e.target.value)}
                  placeholder={`Milestone #${idx + 1}`}
                  required
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={m.amount}
                  onChange={(e) => handleMilestoneChange(idx, 'amount', e.target.value)}
                  placeholder="Amount"
                  required
                  className="w-28 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveMilestone(idx)}
                  disabled={milestones.length <= 1}
                  className="text-slate-500 hover:text-rose-400 p-1.5 disabled:opacity-30"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
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
            icon={<Lock className="w-4 h-4" />}
          >
            Create Agreement
          </Button>
        </div>
      </form>
    </Modal>
  );
};
