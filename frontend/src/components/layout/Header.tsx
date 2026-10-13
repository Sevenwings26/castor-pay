import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ShieldCheck, Plus, Activity } from 'lucide-react';
import { RootState } from '../../store/store';
import { setSelectedCurrency } from '../../store/slices/authSlice';
import { setActiveModal } from '../../store/slices/uiSlice';
import { Currency } from '../../types';
import { Button } from '../common/Button';

export const Header: React.FC = () => {
  const dispatch = useDispatch();
  const { activePortal, selectedCurrency, email, role } = useSelector(
    (state: RootState) => state.auth
  );

  const currencies: Currency[] = ['NGN', 'GBP', 'USD', 'EUR'];

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left side: Portal Context Title */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="font-bold text-base text-slate-100">
            {activePortal === 'MERCHANT' ? 'Merchant Payment Suite' : 'Platform Treasury & Rails'}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
            Live Sandbox
          </span>
        </div>
      </div>

      {/* Right side: Currency Selector & Actions */}
      <div className="flex items-center gap-4">
        {/* Currency Switcher */}
        {activePortal === 'MERCHANT' && (
          <div className="flex items-center bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/80">
            {currencies.map((curr) => (
              <button
                key={curr}
                onClick={() => dispatch(setSelectedCurrency(curr))}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                  selectedCurrency === curr
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {curr}
              </button>
            ))}
          </div>
        )}

        {/* Quick Action Button */}
        {activePortal === 'MERCHANT' ? (
          <Button
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => dispatch(setActiveModal('NEW_PAYMENT'))}
          >
            New Payment
          </Button>
        ) : (
          <Button
            size="sm"
            variant="secondary"
            icon={<Activity className="w-4 h-4 text-brand-400" />}
            onClick={() => dispatch(setActiveModal('SIMULATE_RECON'))}
          >
            Run 3-Way Recon
          </Button>
        )}

        {/* User Pill */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800 text-xs">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-brand-400 uppercase">
            {email ? email.substring(0, 2) : 'CP'}
          </div>
          <div className="hidden sm:block text-left">
            <div className="font-semibold text-slate-200 truncate max-w-[130px]">{email}</div>
            <div className="text-[10px] text-slate-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-brand-400" />
              {role || 'MERCHANT_ADMIN'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
