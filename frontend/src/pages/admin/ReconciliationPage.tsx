import React from 'react';
import { Scale, RefreshCw } from 'lucide-react';
import { useGetReconBatchesQuery } from '../../api/apiSlice';
import { Button } from '../../components/common/Button';
import { ReconciliationTable } from '../../components/admin/ReconciliationTable';

export const ReconciliationPage: React.FC = () => {
  const { data: batches = [], isLoading, refetch } = useGetReconBatchesQuery();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <Scale className="w-6 h-6 text-brand-400" />
            3-Way Automated Reconciliation Audit
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated settlement verification: Ledger Record ↔ Gateway Transaction Log ↔ Bank Statement.
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          onClick={() => refetch()}
        >
          Refresh Batches
        </Button>
      </div>

      {/* Reconciliation Batches & Discrepancies Table */}
      <ReconciliationTable batches={batches} isLoading={isLoading} />
    </div>
  );
};
