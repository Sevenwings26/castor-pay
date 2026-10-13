import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  LayoutDashboard,
  CreditCard,
  Building2,
  ArrowLeftRight,
  Lock,
  Terminal,
  Landmark,
  AlertOctagon,
  Scale,
  LogOut,
  Zap,
  Repeat,
} from 'lucide-react';
import { RootState } from '../../store/store';
import { logout, setActivePortal } from '../../store/slices/authSlice';

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const dispatch = useDispatch();
  const { activePortal } = useSelector((state: RootState) => state.auth);

  const merchantNavItems = [
    { id: 'overview', label: 'Wallet & Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'transactions', label: 'Payments & Ledger', icon: <CreditCard className="w-4 h-4" /> },
    { id: 'virtual-accounts', label: 'Virtual Accounts (DVA)', icon: <Building2 className="w-4 h-4" /> },
    { id: 'fx', label: 'FX Treasury & Swaps', icon: <ArrowLeftRight className="w-4 h-4" /> },
    { id: 'escrow', label: 'Escrow Contracts', icon: <Lock className="w-4 h-4" /> },
    { id: 'developer', label: 'Developer API & Webhooks', icon: <Terminal className="w-4 h-4" /> },
  ];

  const adminNavItems = [
    { id: 'admin-treasury', label: 'Treasury & Float', icon: <Landmark className="w-4 h-4" /> },
    { id: 'admin-dlq', label: 'Dead-Letter Queue (DLQ)', icon: <AlertOctagon className="w-4 h-4" /> },
    { id: 'admin-recon', label: '3-Way Reconciliation', icon: <Scale className="w-4 h-4" /> },
  ];

  const navItems = activePortal === 'MERCHANT' ? merchantNavItems : adminNavItems;

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center text-white shadow-md shadow-brand-900/40">
            <Zap className="w-5 h-5 fill-white" />
          </div>
          <div>
            <div className="font-extrabold text-base tracking-tight text-white flex items-center gap-1.5">
              Castor<span className="text-brand-400">Pay</span>
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
              Embedded Finance
            </div>
          </div>
        </div>

        {/* Portal Switcher Banner */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/40">
          <div className="text-[11px] font-semibold uppercase text-slate-400 mb-2 flex items-center justify-between">
            <span>Active Platform Role</span>
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                activePortal === 'ADMIN'
                  ? 'bg-purple-500/20 text-purple-300'
                  : 'bg-brand-500/20 text-brand-300'
              }`}
            >
              {activePortal}
            </span>
          </div>
          <button
            onClick={() => {
              const nextPortal = activePortal === 'MERCHANT' ? 'ADMIN' : 'MERCHANT';
              dispatch(setActivePortal(nextPortal));
              onTabChange(nextPortal === 'MERCHANT' ? 'overview' : 'admin-treasury');
            }}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 transition-colors"
          >
            <Repeat className="w-3.5 h-3.5 text-brand-400" />
            Switch to {activePortal === 'MERCHANT' ? 'Admin Treasury' : 'Merchant Portal'}
          </button>
        </div>

        {/* Navigation Section */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            {activePortal === 'MERCHANT' ? 'Merchant Operations' : 'Platform Operations'}
          </div>
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600/15 text-brand-400 border border-brand-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <span className={isActive ? 'text-brand-400' : 'text-slate-400'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="p-4 border-t border-slate-800 space-y-2">
        <button
          onClick={() => dispatch(logout())}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
        >
          <LogOut className="w-4 h-4 text-slate-400" />
          <span>Sign Out Session</span>
        </button>
        <div className="text-[10px] text-slate-400 text-center font-mono">
          v1.0.0 • Docker LocalStack
        </div>
      </div>
    </aside>
  );
};
