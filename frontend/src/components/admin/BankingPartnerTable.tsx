import React from 'react';
import { Landmark, Activity } from 'lucide-react';
import { BankingPartner } from '../../types';
import { Badge, getStatusBadgeVariant } from '../common/Badge';

interface BankingPartnerTableProps {
  partners: BankingPartner[];
  isLoading?: boolean;
}

export const BankingPartnerTable: React.FC<BankingPartnerTableProps> = ({
  partners,
  isLoading = false,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-brand-400" />
            Banking Partner Rails & Gateway Latency
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Real-time ping, routing availability, and clearing house health metrics.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-4">Banking Partner</th>
              <th className="py-2.5 px-4">Payment Rail / Network</th>
              <th className="py-2.5 px-4">Operational Status</th>
              <th className="py-2.5 px-4 text-right">Gateway Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="py-6 text-center text-slate-400 font-sans">
                  Inspecting banking partner telemetry...
                </td>
              </tr>
            ) : (
              partners.map((partner) => (
                <tr key={partner.partner} className="hover:bg-slate-800/30">
                  <td className="py-3 px-4 font-sans font-medium text-slate-200">
                    <div className="flex items-center gap-2">
                      <Landmark className="w-4 h-4 text-slate-500" />
                      <span>{partner.partner}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-slate-300 font-sans">{partner.rail}</td>
                  <td className="py-3 px-4">
                    <Badge variant={getStatusBadgeVariant(partner.status)}>
                      {partner.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-right font-mono">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        partner.latency_ms < 60
                          ? 'text-emerald-400 bg-emerald-500/10'
                          : partner.latency_ms < 100
                          ? 'text-amber-400 bg-amber-500/10'
                          : 'text-rose-400 bg-rose-500/10'
                      }`}
                    >
                      {partner.latency_ms} ms
                    </span>
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
