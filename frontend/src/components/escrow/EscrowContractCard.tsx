import React from 'react';
import { useDispatch } from 'react-redux';
import { Lock } from 'lucide-react';
import { EscrowContract } from '../../types';
import { useFundEscrowContractMutation, useReleaseMilestoneMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatMinorUnits, formatDate } from '../../utils/formatters';
import { Badge, getStatusBadgeVariant } from '../common/Badge';
import { Button } from '../common/Button';

interface EscrowContractCardProps {
  contract: EscrowContract;
}

export const EscrowContractCard: React.FC<EscrowContractCardProps> = ({ contract }) => {
  const dispatch = useDispatch();

  const [fundContract, { isLoading: isFunding }] = useFundEscrowContractMutation();
  const [releaseMilestone, { isLoading: isReleasing }] = useReleaseMilestoneMutation();

  const handleFund = async () => {
    try {
      await fundContract({ contract_reference: contract.contract_reference }).unwrap();
      dispatch(
        addToast({
          type: 'success',
          title: 'Escrow Funded',
          message: `Funds locked into escrow liability reserve for ${contract.contract_reference}.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Funding Error',
          message: err?.data?.detail || 'Failed to fund escrow contract.',
        })
      );
    }
  };

  const handleRelease = async (milestoneId: string, title: string) => {
    try {
      await releaseMilestone({
        contract_reference: contract.contract_reference,
        milestone_id: milestoneId,
      }).unwrap();
      dispatch(
        addToast({
          type: 'success',
          title: 'Milestone Disbursed',
          message: `Released funds for "${title}" to seller wallet.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Release Failed',
          message: err?.data?.detail || 'Failed to release milestone.',
        })
      );
    }
  };

  const totalMilestones = contract.milestones?.length || 0;
  const completedMilestones =
    contract.milestones?.filter((m) => m.status === 'RELEASED' || m.status === 'COMPLETED').length || 0;
  const progressPercent = totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-brand-400 font-bold">
                {contract.contract_reference}
              </span>
              <Badge variant={getStatusBadgeVariant(contract.status)}>
                {contract.status}
              </Badge>
            </div>
            <h4 className="text-base font-bold text-slate-100 mt-1">{contract.title}</h4>
          </div>
          <div className="text-right">
            <div className="text-lg font-mono font-extrabold text-slate-100">
              {formatMinorUnits(contract.total_amount, contract.currency)}
            </div>
            <div className="text-[10px] text-slate-400 font-mono">
              Created {formatDate(contract.created_at)}
            </div>
          </div>
        </div>

        {/* Parties */}
        <div className="grid grid-cols-2 gap-2 bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 text-xs my-3">
          <div>
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Buyer</span>
            <span className="font-mono text-slate-200 truncate block">{contract.buyer_email}</span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Seller / Payee</span>
            <span className="font-mono text-slate-200 truncate block">{contract.seller_email}</span>
          </div>
        </div>

        {/* Milestone Progress Bar */}
        <div className="my-3">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span>Milestone Completion</span>
            <span className="font-mono font-semibold text-slate-200">
              {completedMilestones} / {totalMilestones} ({Math.round(progressPercent)}%)
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-brand-500 h-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Milestones List */}
        <div className="space-y-2 mt-3 pt-3 border-t border-slate-800">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Milestones Breakdown
          </div>
          {contract.milestones?.map((m) => (
            <div
              key={m.id}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800 text-xs"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    m.status === 'RELEASED' ? 'bg-emerald-400' : 'bg-amber-400'
                  }`}
                />
                <span className="font-medium text-slate-200">{m.title}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono font-semibold text-slate-300">
                  {formatMinorUnits(m.amount, contract.currency)}
                </span>
                {m.status !== 'RELEASED' &&
                  (contract.status === 'FUNDED' || contract.status === 'IN_INSPECTION') && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleRelease(m.id, m.title)}
                      disabled={isReleasing}
                      className="text-[10px] py-0.5 px-2 bg-emerald-600 hover:bg-emerald-500"
                    >
                      Release
                    </Button>
                  )}
                {m.status === 'RELEASED' && (
                  <span className="text-[10px] text-emerald-400 font-mono font-semibold">
                    Released
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Contract Actions Footer */}
      {contract.status === 'CREATED' && (
        <div className="mt-4 pt-3 border-t border-slate-800">
          <Button
            size="sm"
            variant="primary"
            onClick={handleFund}
            disabled={isFunding}
            isLoading={isFunding}
            icon={<Lock className="w-3.5 h-3.5" />}
            className="w-full"
          >
            Fund & Lock Escrow Reserve
          </Button>
        </div>
      )}
    </div>
  );
};
