import React from 'react';
import { useDispatch } from 'react-redux';
import { AlertOctagon, RotateCcw, Clock, CheckCircle2 } from 'lucide-react';
import { DLQMessage } from '../../types';
import { useReplayDLQMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatDate } from '../../utils/formatters';
import { Button } from '../common/Button';

interface DLQInspectorProps {
  queueUrl?: string;
  totalInspected?: number;
  messages: DLQMessage[];
  isLoading?: boolean;
}

export const DLQInspector: React.FC<DLQInspectorProps> = ({
  queueUrl,
  messages,
  isLoading = false,
}) => {
  const dispatch = useDispatch();
  const [replayMessage, { isLoading: isReplaying }] = useReplayDLQMutation();

  const handleReplay = async (messageId: string) => {
    try {
      await replayMessage({ message_id: messageId }).unwrap();
      dispatch(
        addToast({
          type: 'success',
          title: 'Poison Pill Replayed',
          message: `Message "${messageId}" disisolated and resent to primary payment queue.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Replay Failed',
          message: err?.data?.detail || 'Failed to replay dead-letter queue message.',
        })
      );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            Poison-Pill Isolation Explorer (AWS SQS DLQ)
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
            Queue: {queueUrl || 'localstack:4566/castor-payment-events-dlq'}
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          Messages in DLQ: <span className="text-rose-400 font-bold">{messages.length}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-4">Message ID</th>
              <th className="py-2.5 px-4">Receive Count</th>
              <th className="py-2.5 px-4">Payload & Failure Reason</th>
              <th className="py-2.5 px-4">Sent Time</th>
              <th className="py-2.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400 font-sans">
                  <div className="flex items-center justify-center gap-2">
                    <Clock className="w-4 h-4 animate-spin text-rose-400" />
                    <span>Polling SQS Dead-Letter Queue...</span>
                  </div>
                </td>
              </tr>
            ) : messages.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-10 text-center text-slate-400 font-sans">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-60" />
                  <div className="font-bold text-slate-300">DLQ is Empty & Healthy</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    No failed messages or poison pills isolated.
                  </div>
                </td>
              </tr>
            ) : (
              messages.map((msg) => (
                <tr key={msg.message_id} className="hover:bg-slate-800/30">
                  <td className="py-3 px-4 font-bold text-rose-400">{msg.message_id}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                      {msg.receive_count} Retries Exceeded
                    </span>
                  </td>
                  <td className="py-3 px-4 max-w-md">
                    <pre className="text-[11px] bg-slate-950 p-2 rounded border border-slate-800 text-slate-300 overflow-x-auto max-h-24">
                      {JSON.stringify(msg.body, null, 2)}
                    </pre>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-sans">
                    {msg.sent_timestamp ? formatDate(new Date(parseInt(msg.sent_timestamp) * 1000).toISOString()) : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-right font-sans">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleReplay(msg.message_id)}
                      disabled={isReplaying}
                      icon={<RotateCcw className="w-3.5 h-3.5 text-brand-400" />}
                      className="text-[11px] py-1 px-2.5"
                    >
                      1-Click Replay
                    </Button>
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
