import React from 'react';
import { useDispatch } from 'react-redux';
import { Scale, AlertTriangle, Play, Clock } from 'lucide-react';
import { ReconBatch } from '../../types';
import { useSimulateDailyReconMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatMinorUnits, formatDate } from '../../utils/formatters';
import { Badge, getStatusBadgeVariant } from '../common/Badge';
import { Button } from '../common/Button';

interface ReconciliationTableProps {
  batches: ReconBatch[];
  isLoading?: boolean;
}

export const ReconciliationTable: React.FC<ReconciliationTableProps> = ({
  batches,
  isLoading = false,
}) => {
  const dispatch = useDispatch();
  const [simulateDailyRecon, { isLoading: isRunningSim }] = useSimulateDailyReconMutation();

  const handleRunRecon = async () => {
    try {
      const res = await simulateDailyRecon().unwrap();
      dispatch(
        addToast({
          type: res.status === 'BALANCED' ? 'success' : 'warning',
          title: '3-Way Recon Finished',
          message: `Batch ${res.batch_reference}: ${res.matched_records} matched, ${res.unmatched_records} variances identified.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Reconciliation Failed',
          message: err?.data?.detail || 'Reconciliation run error.',
        })
      );
    }
  };

  return (
    <div className="space-y-4">
      {/* Batch Header & Simulator Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div>
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Scale className="w-4 h-4 text-brand-400" />
            Automated 3-Way Reconciliation Engine
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Internal Ledger ↔ Gateway Transaction Logs ↔ Bank Settlement Statements.
          </p>
        </div>

        <Button
          size="sm"
          onClick={handleRunRecon}
          isLoading={isRunningSim}
          icon={<Play className="w-3.5 h-3.5 fill-current" />}
        >
          Simulate Daily Bank Recon Run
        </Button>
      </div>

      {/* Batches & Discrepancies Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Batch Reference</th>
                <th className="py-2.5 px-4">Provider / Rail</th>
                <th className="py-2.5 px-4">Records</th>
                <th className="py-2.5 px-4">Matched</th>
                <th className="py-2.5 px-4">Variances</th>
                <th className="py-2.5 px-4">Audit Status</th>
                <th className="py-2.5 px-4">Statement Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400 font-sans">
                    <div className="flex items-center justify-center gap-2">
                      <Clock className="w-4 h-4 animate-spin text-brand-400" />
                      <span>Loading reconciliation audit batches...</span>
                    </div>
                  </td>
                </tr>
              ) : batches.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-400 font-sans">
                    <Scale className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
                    <div className="font-bold text-slate-300">No Reconciliation Batches Processed</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Click "Simulate Daily Bank Recon Run" to ingest settlement files and perform 3-way matching.
                    </div>
                  </td>
                </tr>
              ) : (
                batches.map((batch) => (
                  <React.Fragment key={batch.id}>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-brand-400">{batch.batch_reference}</td>
                      <td className="py-3 px-4 font-sans text-slate-200">{batch.provider}</td>
                      <td className="py-3 px-4 font-bold text-slate-100">{batch.total_records}</td>
                      <td className="py-3 px-4 text-emerald-400 font-bold">{batch.matched_records}</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{batch.unmatched_records}</td>
                      <td className="py-3 px-4 font-sans">
                        <Badge variant={getStatusBadgeVariant(batch.status)}>
                          {batch.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans">
                        {formatDate(batch.statement_date)}
                      </td>
                    </tr>

                    {/* Expand discrepancies if any */}
                    {batch.discrepancies && batch.discrepancies.length > 0 && (
                      <tr className="bg-slate-950/40">
                        <td colSpan={7} className="p-3 pl-8">
                          <div className="border-l-2 border-amber-500/50 pl-3 space-y-1.5 font-sans">
                            <div className="text-[11px] font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                              Identified Audit Variances ({batch.discrepancies.length}):
                            </div>
                            {batch.discrepancies.map((disc) => (
                              <div
                                key={disc.id}
                                className="flex items-center justify-between text-xs font-mono bg-slate-900/80 p-2 rounded border border-slate-800"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                                    {disc.discrepancy_type}
                                  </span>
                                  <span className="text-slate-300">
                                    Bank Ref: {disc.external_reference || 'N/A'} ↔ Ledger: {disc.internal_reference || 'N/A'}
                                  </span>
                                </div>
                                <div className="text-right">
                                  <span className="text-rose-400 font-bold">
                                    Variance: {formatMinorUnits(disc.variance_amount, 'NGN')}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
