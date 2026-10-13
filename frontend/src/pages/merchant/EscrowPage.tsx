import React, { useState } from 'react';
import { Lock, Plus, RefreshCw } from 'lucide-react';
import { useGetEscrowContractsQuery } from '../../api/apiSlice';
import { Button } from '../../components/common/Button';
import { EscrowContractCard } from '../../components/escrow/EscrowContractCard';
import { CreateEscrowModal } from '../../components/escrow/CreateEscrowModal';

export const EscrowPage: React.FC = () => {
  const { data: contracts = [], isLoading, refetch } = useGetEscrowContractsQuery();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <Lock className="w-6 h-6 text-brand-400" />
            Escrow Contracts & Gaming Micropayments
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Milestone-based fund reserve locking, conditional deliverable approvals, and automated payout releases.
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
            onClick={() => setIsCreateOpen(true)}
          >
            Create Agreement
          </Button>
        </div>
      </div>

      {/* Contracts Grid */}
      {isLoading ? (
        <div className="py-16 text-center text-slate-400">Loading escrow agreements...</div>
      ) : contracts.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <Lock className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <h3 className="text-base font-bold text-slate-200">No Escrow Contracts Active</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Create milestone-backed contracts for gaming prizes, escrow trades, or contractor deliverables.
          </p>
          <div className="mt-4">
            <Button size="sm" onClick={() => setIsCreateOpen(true)}>
              Create Your First Escrow
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {contracts.map((contract) => (
            <EscrowContractCard key={contract.id} contract={contract} />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateEscrowModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  );
};
