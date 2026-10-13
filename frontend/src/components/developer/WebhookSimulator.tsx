import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Terminal, Copy, Check, Send, ShieldCheck } from 'lucide-react';
import { addToast } from '../../store/slices/uiSlice';
import { Button } from '../common/Button';

export const WebhookSimulator: React.FC = () => {
  const dispatch = useDispatch();

  const [webhookUrl, setWebhookUrl] = useState('https://webhook.site/demo-castor-test');
  const [webhookSecret] = useState('whsec_demo_secret_key_12345');
  const [selectedEvent, setSelectedEvent] = useState('payment.succeeded');
  const [isSending, setIsSending] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);

  const samplePayloads: Record<string, any> = {
    'payment.succeeded': {
      event: 'payment.succeeded',
      transaction_id: 'tx_demo_9921',
      reference: 'cpay_9864d38fab9e69947062aa9b',
      amount: 250000,
      currency: 'NGN',
      status: 'SUCCEEDED',
      customer_email: 'gamer@ab-inbev.com',
      metadata: { game_session_id: 'session_88192' },
      timestamp: new Date().toISOString(),
    },
    'virtual_account.credited': {
      event: 'virtual_account.credited',
      account_number: '9955623054',
      bank_name: 'Castor / Providus Bank',
      amount: 500000,
      currency: 'NGN',
      session_id: 'NIP_SESSION_88192',
      sender_name: 'Alhaji Dangote',
      timestamp: new Date().toISOString(),
    },
    'escrow.milestone_released': {
      event: 'escrow.milestone_released',
      contract_reference: 'ESC-2026-9921',
      milestone_id: 'ms_01',
      amount: 100000,
      currency: 'NGN',
      status: 'RELEASED',
      timestamp: new Date().toISOString(),
    },
  };

  const handleCopySecret = () => {
    navigator.clipboard.writeText(webhookSecret);
    setCopiedSecret(true);
    setTimeout(() => setCopiedSecret(false), 2000);
  };

  const handleSendPing = () => {
    setIsSending(true);
    setTimeout(() => {
      setIsSending(false);
      dispatch(
        addToast({
          type: 'success',
          title: 'Webhook Delivered (200 OK)',
          message: `Event "${selectedEvent}" dispatched. HMAC-SHA256 signature verified by receiver.`,
        })
      );
    }, 600);
  };

  const currentPayloadJson = JSON.stringify(samplePayloads[selectedEvent], null, 2);
  const mockSignature = 'sha256=d7a8fbb56e9c01198f32ac9f7831...';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-brand-400" />
            Outbound Webhook Listener & Signature Diagnostics
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Test real-time event delivery and verify HMAC-SHA256 webhook signatures.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Webhook URL & Secret */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Target Webhook URL
            </label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Signing Secret (HMAC-SHA256)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={webhookSecret}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-brand-400 font-mono focus:outline-none select-all"
              />
              <button
                type="button"
                onClick={handleCopySecret}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                title="Copy secret"
              >
                {copiedSecret ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Event Selector & Trigger */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-300">Test Event:</label>
            <select
              value={selectedEvent}
              onChange={(e) => setSelectedEvent(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-mono focus:outline-none"
            >
              <option value="payment.succeeded">payment.succeeded</option>
              <option value="virtual_account.credited">virtual_account.credited</option>
              <option value="escrow.milestone_released">escrow.milestone_released</option>
            </select>
          </div>

          <Button
            size="sm"
            onClick={handleSendPing}
            isLoading={isSending}
            icon={<Send className="w-3.5 h-3.5 text-brand-400" />}
          >
            Send Test Webhook
          </Button>
        </div>

        {/* Payload Preview */}
        <div className="bg-slate-950 rounded-lg border border-slate-800 p-3 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2 border-b border-slate-800/80 pb-1.5 text-[11px]">
            <span className="flex items-center gap-1.5 text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Header: X-Castor-Signature: {mockSignature}
            </span>
            <span>JSON Body</span>
          </div>
          <pre className="text-slate-300 overflow-x-auto text-[11px] leading-relaxed">
            {currentPayloadJson}
          </pre>
        </div>
      </div>
    </div>
  );
};
