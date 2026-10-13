import React, { useState } from 'react';
import { Building2, Plus, Zap, RefreshCw } from 'lucide-react';
import { VirtualAccount } from '../../types';
import { useGetVirtualAccountsQuery } from '../../api/apiSlice';
import { Button } from '../../components/common/Button';
import { VirtualAccountCard } from '../../components/virtualAccounts/VirtualAccountCard';
import { CreateVirtualAccountModal } from '../../components/virtualAccounts/CreateVirtualAccountModal';
import { SimulateDepositModal } from '../../components/virtualAccounts/SimulateDepositModal';

export const VirtualAccountsPage: React.FC = () => {
  const { data: accounts = [], isLoading, refetch } = useGetVirtualAccountsQuery();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<VirtualAccount | null>(null);

  const handleOpenSimulate = (acc: VirtualAccount) => {
    setSelectedAccount(acc);
    setIsDepositOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <Building2 className="w-6 h-6 text-brand-400" />
            Dedicated Virtual Accounts (DVA)
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated collections via dedicated bank accounts in NGN (NUBAN), GBP (Sort Code), and USD (Fedwire).
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
            variant="secondary"
            icon={<Zap className="w-4 h-4 text-amber-400" />}
            onClick={() => {
              setSelectedAccount(accounts[0] || null);
              setIsDepositOpen(true);
            }}
          >
            Simulate Deposit
          </Button>
          <Button
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setIsCreateOpen(true)}
          >
            Issue New DVA
          </Button>
        </div>
      </div>

      {/* Account Cards Grid */}
      {isLoading ? (
        <div className="py-16 text-center text-slate-400">
          Loading virtual accounts from banking rails...
        </div>
      ) : accounts.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <Building2 className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <h3 className="text-base font-bold text-slate-200">No Virtual Accounts Issued Yet</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Issue dedicated collection bank accounts in NGN, GBP, or USD to automate pay-ins.
          </p>
          <div className="mt-4">
            <Button size="sm" onClick={() => setIsCreateOpen(true)}>
              Issue Your First DVA
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {accounts.map((acc) => (
            <VirtualAccountCard
              key={acc.id}
              account={acc}
              onSimulateDeposit={handleOpenSimulate}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateVirtualAccountModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />
      <SimulateDepositModal
        isOpen={isDepositOpen}
        onClose={() => setIsDepositOpen(false)}
        targetAccount={selectedAccount}
      />
    </div>
  );
};
