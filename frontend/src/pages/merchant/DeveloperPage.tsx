import React from 'react';
import { Terminal } from 'lucide-react';
import { ApiKeyManager } from '../../components/developer/ApiKeyManager';
import { WebhookSimulator } from '../../components/developer/WebhookSimulator';

export const DeveloperPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
          <Terminal className="w-6 h-6 text-brand-400" />
          Developer API Keys & Webhooks
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Server-to-server credentials, HMAC-SHA256 signature verification, and event dispatch simulation.
        </p>
      </div>

      {/* Secret API Keys Section */}
      <ApiKeyManager />

      {/* Outbound Webhook Tester */}
      <WebhookSimulator />
    </div>
  );
};
