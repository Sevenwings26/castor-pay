import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Key, Plus, Copy, Check, ShieldAlert, Clock } from 'lucide-react';
import { useGetApiKeysQuery, useCreateApiKeyMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatDate } from '../../utils/formatters';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';

export const ApiKeyManager: React.FC = () => {
  const dispatch = useDispatch();
  const { data: apiKeys, isLoading } = useGetApiKeysQuery();
  const [createApiKey, { isLoading: isCreating }] = useCreateApiKeyMutation();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [keyName, setKeyName] = useState('Server Backend Integration Key');
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await createApiKey({ name: keyName }).unwrap();
      setRevealedKey(res.raw_key);
      dispatch(
        addToast({
          type: 'success',
          title: 'API Key Created',
          message: `Created secret key "${res.name}".`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Key Generation Failed',
          message: err?.data?.detail || 'Unable to create API key.',
        })
      );
    }
  };

  const handleCopyRevealed = () => {
    if (revealedKey) {
      navigator.clipboard.writeText(revealedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Key className="w-4 h-4 text-brand-400" />
            Merchant Secret API Keys
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Authenticate server-to-server requests and gaming micropayment ingestion.
          </p>
        </div>
        <Button
          size="sm"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setRevealedKey(null);
            setIsModalOpen(true);
          }}
        >
          Generate New Key
        </Button>
      </div>

      {/* Keys List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Key Name</th>
              <th className="py-2.5 px-3">Token Hash (Masked)</th>
              <th className="py-2.5 px-3">Environment</th>
              <th className="py-2.5 px-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="py-6 text-center text-slate-400">
                  <div className="flex items-center justify-center gap-2">
                    <Clock className="w-4 h-4 animate-spin text-brand-400" />
                    <span>Loading API keys...</span>
                  </div>
                </td>
              </tr>
            ) : apiKeys?.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-6 text-center text-slate-500 font-sans">
                  No custom API keys generated yet.
                </td>
              </tr>
            ) : (
              apiKeys?.map((k) => (
                <tr key={k.id} className="hover:bg-slate-800/30">
                  <td className="py-3 px-3 font-sans font-medium text-slate-200">{k.name}</td>
                  <td className="py-3 px-3 text-slate-400">
                    <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800 text-brand-400 font-mono">
                      {k.raw_key}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-sans">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                      SANDBOX / LIVE
                    </span>
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-400">{formatDate(k.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal for Creating / Revealing Key */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={revealedKey ? 'API Key Generated' : 'Create New API Key'}
        subtitle="Server-to-server integration credential."
      >
        {revealedKey ? (
          <div className="space-y-4">
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300 flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400" />
              <div>
                <span className="font-bold">Store this key safely!</span>
                <p className="mt-0.5 text-slate-300">
                  For security, this secret key will never be displayed again. If lost, you will need to generate a new key.
                </p>
              </div>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between">
              <span className="font-mono text-sm text-brand-300 break-all select-all">
                {revealedKey}
              </span>
              <button
                onClick={handleCopyRevealed}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 ml-2"
                title="Copy Key"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            <div className="pt-2 flex justify-end">
              <Button size="sm" onClick={() => setIsModalOpen(false)}>
                Done
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Key Name / Purpose
              </label>
              <input
                type="text"
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="e.g. Production Game Engine Client"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" isLoading={isCreating}>
                Generate Key
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
