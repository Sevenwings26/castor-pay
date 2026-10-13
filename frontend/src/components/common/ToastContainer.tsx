import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { RootState } from '../../store/store';
import { removeToast, Toast } from '../../store/slices/uiSlice';

const ToastItem: React.FC<{ toast: Toast }> = ({ toast }) => {
  const dispatch = useDispatch();

  useEffect(() => {
    const timer = setTimeout(() => {
      dispatch(removeToast(toast.id));
    }, 4500);
    return () => clearTimeout(timer);
  }, [dispatch, toast.id]);

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />,
    info: <Info className="w-5 h-5 text-sky-400 shrink-0" />,
  };

  const borders = {
    success: 'border-emerald-500/30 bg-slate-900/95',
    warning: 'border-amber-500/30 bg-slate-900/95',
    error: 'border-rose-500/30 bg-slate-900/95',
    info: 'border-sky-500/30 bg-slate-900/95',
  };

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-xl border shadow-xl ${borders[toast.type]} min-w-[320px] max-w-md animate-in slide-in-from-right-5 fade-in duration-200`}
    >
      {icons[toast.type]}
      <div className="flex-1 text-sm">
        {toast.title && <div className="font-semibold text-slate-100">{toast.title}</div>}
        <div className="text-slate-300 text-xs mt-0.5 leading-relaxed">{toast.message}</div>
      </div>
      <button
        onClick={() => dispatch(removeToast(toast.id))}
        className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-slate-800 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const toasts = useSelector((state: RootState) => state.ui.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 pointer-events-auto">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
};
