import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { ArrowLeftRight, Clock, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { Currency, FXQuote } from '../../types';
import { useCreateFXQuoteMutation, useExecuteFXQuoteMutation } from '../../api/apiSlice';
import { addToast } from '../../store/slices/uiSlice';
import { formatMinorUnits } from '../../utils/formatters';
import { Button } from '../common/Button';

export const FXQuoteWidget: React.FC = () => {
  const dispatch = useDispatch();

  const [sourceCurrency, setSourceCurrency] = useState<Currency>('GBP');
  const [targetCurrency, setTargetCurrency] = useState<Currency>('NGN');
  const [sourceAmount, setSourceAmount] = useState<string>('100.00'); // major units
  const [activeQuote, setActiveQuote] = useState<FXQuote | null>(null);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  const [createQuote, { isLoading: isCreatingQuote }] = useCreateFXQuoteMutation();
  const [executeQuote, { isLoading: isExecuting }] = useExecuteFXQuoteMutation();

  // Active countdown timer effect for activeQuote
  useEffect(() => {
    if (!activeQuote || activeQuote.is_executed) return;

    const interval = setInterval(() => {
      const expiresAtMs = new Date(activeQuote.expires_at).getTime();
      const nowMs = Date.now();
      const diffSec = Math.max(0, Math.floor((expiresAtMs - nowMs) / 1000));
      setSecondsRemaining(diffSec);

      if (diffSec <= 0) {
        clearInterval(interval);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [activeQuote]);

  const handleSwapCurrencies = () => {
    const prevSource = sourceCurrency;
    setSourceCurrency(targetCurrency);
    setTargetCurrency(prevSource);
    setActiveQuote(null);
  };

  const handleRequestQuote = async (e: React.FormEvent) => {
    e.preventDefault();
    const numericSource = parseFloat(sourceAmount);
    if (isNaN(numericSource) || numericSource <= 0) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Invalid Amount',
          message: 'Please enter a positive amount to convert.',
        })
      );
      return;
    }

    if (sourceCurrency === targetCurrency) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Identical Currencies',
          message: 'Source and target currencies must be distinct.',
        })
      );
      return;
    }

    const minorAmount = Math.round(numericSource * 100);

    try {
      const quote = await createQuote({
        source_currency: sourceCurrency,
        target_currency: targetCurrency,
        source_amount: minorAmount,
      }).unwrap();

      setActiveQuote(quote);
      const expiresAtMs = new Date(quote.expires_at).getTime();
      setSecondsRemaining(Math.max(0, Math.floor((expiresAtMs - Date.now()) / 1000)));

      dispatch(
        addToast({
          type: 'info',
          title: 'Guaranteed Quote Locked',
          message: `Rate guaranteed for 60 seconds. Reference: ${quote.quote_reference}`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Quote Generation Failed',
          message: err?.data?.detail || 'Unable to generate FX rate lock.',
        })
      );
    }
  };

  const handleExecuteSwap = async () => {
    if (!activeQuote) return;

    try {
      const executed = await executeQuote({
        quote_reference: activeQuote.quote_reference,
      }).unwrap();

      setActiveQuote({ ...activeQuote, is_executed: true });
      dispatch(
        addToast({
          type: 'success',
          title: 'FX Conversion Executed!',
          message: `Converted ${formatMinorUnits(executed.source_amount, executed.source_currency)} to ${formatMinorUnits(executed.target_amount, executed.target_currency)}. Wallets updated.`,
        })
      );
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: 'Execution Failed',
          message: err?.data?.detail || 'FX quote expired or insufficient wallet balance.',
        })
      );
    }
  };

  const isExpired = activeQuote !== null && secondsRemaining <= 0 && !activeQuote.is_executed;
  const progressPercent = Math.min(100, Math.max(0, (secondsRemaining / 60) * 100));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-brand-400" />
            Cross-Border FX Conversion & Rate Lock
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Institutional-grade 60-second rate guarantee with double-entry wallet settlement.
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono text-brand-400 bg-brand-500/10 px-2.5 py-1 rounded-full border border-brand-500/20">
          <ShieldCheck className="w-4 h-4" />
          <span>60s Lock Protocol</span>
        </div>
      </div>

      <form onSubmit={handleRequestQuote} className="space-y-4">
        {/* Currency Pair & Amount Input */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-center">
          {/* Source Currency */}
          <div className="md:col-span-3 bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 mb-1">
              <span>You Pay</span>
              <select
                value={sourceCurrency}
                onChange={(e) => {
                  setSourceCurrency(e.target.value as Currency);
                  setActiveQuote(null);
                }}
                className="bg-slate-800 text-slate-200 rounded px-2 py-0.5 border border-slate-700 font-mono text-xs focus:outline-none"
              >
                <option value="GBP">GBP (£)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="NGN">NGN (₦)</option>
              </select>
            </div>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={sourceAmount}
              onChange={(e) => {
                setSourceAmount(e.target.value);
                setActiveQuote(null);
              }}
              className="w-full bg-transparent text-xl font-mono font-bold text-slate-100 focus:outline-none"
              placeholder="100.00"
            />
          </div>

          {/* Swap Button */}
          <div className="md:col-span-1 flex justify-center">
            <button
              type="button"
              onClick={handleSwapCurrencies}
              className="p-2.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors shadow-sm"
              title="Invert currency pair"
            >
              <ArrowLeftRight className="w-4 h-4" />
            </button>
          </div>

          {/* Target Currency */}
          <div className="md:col-span-3 bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 mb-1">
              <span>You Receive (Estimated / Locked)</span>
              <select
                value={targetCurrency}
                onChange={(e) => {
                  setTargetCurrency(e.target.value as Currency);
                  setActiveQuote(null);
                }}
                className="bg-slate-800 text-slate-200 rounded px-2 py-0.5 border border-slate-700 font-mono text-xs focus:outline-none"
              >
                <option value="NGN">NGN (₦)</option>
                <option value="GBP">GBP (£)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>
            <div className="text-xl font-mono font-bold text-brand-300 truncate">
              {activeQuote
                ? formatMinorUnits(activeQuote.target_amount, activeQuote.target_currency)
                : '—'}
            </div>
          </div>
        </div>

        {/* Generate / Renew Quote Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            variant="secondary"
            size="sm"
            isLoading={isCreatingQuote}
            icon={<Clock className="w-4 h-4 text-brand-400" />}
          >
            {activeQuote ? 'Refresh Rate Quote' : 'Lock 60s Guaranteed Rate'}
          </Button>
        </div>
      </form>

      {/* Active Quote Locked Display & Countdown */}
      {activeQuote && (
        <div className="mt-5 pt-5 border-t border-slate-800 animate-in fade-in duration-200">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            {/* Header: Quote details */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
              <div>
                <div className="text-xs font-mono font-bold text-slate-200 flex items-center gap-2">
                  <span>Quote: {activeQuote.quote_reference}</span>
                  {activeQuote.is_executed ? (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">
                      EXECUTED
                    </span>
                  ) : isExpired ? (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono">
                      EXPIRED
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono animate-pulse">
                      RATE LOCKED
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-400 font-mono mt-1">
                  1 {activeQuote.source_currency} = {activeQuote.exchange_rate.toFixed(4)} {activeQuote.target_currency} (Spread: {activeQuote.spread_bps} bps)
                </div>
              </div>

              {!activeQuote.is_executed && (
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-[10px] uppercase font-semibold text-slate-400">Time Remaining</div>
                    <div
                      className={`text-lg font-mono font-bold ${
                        secondsRemaining < 10 ? 'text-rose-400 animate-pulse' : 'text-amber-300'
                      }`}
                    >
                      {secondsRemaining}s
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Live Visual Countdown Progress Bar */}
            {!activeQuote.is_executed && (
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden my-3">
                <div
                  className={`h-full transition-all duration-500 ${
                    secondsRemaining < 10
                      ? 'bg-rose-500'
                      : secondsRemaining < 25
                      ? 'bg-amber-400'
                      : 'bg-brand-500'
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            )}

            {/* Execution Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
              <div className="text-xs text-slate-400">
                {activeQuote.is_executed ? (
                  <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    Funds settled to double-entry ledger.
                  </span>
                ) : isExpired ? (
                  <span className="text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Rate guarantee window lapsed. Please request a new quote.
                  </span>
                ) : (
                  <span>Rate guaranteed until expiry. Zero slippage guarantee.</span>
                )}
              </div>

              {!activeQuote.is_executed && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleExecuteSwap}
                  disabled={isExpired || isExecuting}
                  isLoading={isExecuting}
                  icon={<ArrowRight className="w-4 h-4" />}
                  className="w-full sm:w-auto"
                >
                  Execute Guaranteed Swap
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
