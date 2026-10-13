import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { useGetDLQQuery } from '../../api/apiSlice';
import { Button } from '../../components/common/Button';
import { DLQInspector } from '../../components/admin/DLQInspector';

export const DLQMonitorPage: React.FC = () => {
  const { data, isLoading, refetch } = useGetDLQQuery();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <AlertOctagon className="w-6 h-6 text-rose-400" />
            Dead-Letter Queue (DLQ) Inspector & Replay
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Poison-pill message isolation after 3 failed delivery retries with 1-click replay trigger.
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          onClick={() => refetch()}
        >
          Poll DLQ
        </Button>
      </div>

      {/* DLQ Inspector Table */}
      <DLQInspector
        queueUrl={data?.dlq_queue_url}
        totalInspected={data?.total_messages_inspected}
        messages={data?.messages || []}
        isLoading={isLoading}
      />
    </div>
  );
};
