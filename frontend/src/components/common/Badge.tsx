import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | 'success'
    | 'warning'
    | 'danger'
    | 'info'
    | 'neutral'
    | 'purple';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold',
  };

  const variantStyles = {
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
    info: 'bg-sky-500/10 text-sky-400 border border-sky-500/30',
    neutral: 'bg-slate-800 text-slate-300 border border-slate-700',
    purple: 'bg-purple-500/10 text-purple-400 border border-purple-500/30',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full uppercase tracking-wider ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

export function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple' {
  const s = status.toUpperCase();
  if (['SUCCEEDED', 'OPERATIONAL', 'BALANCED', 'ACTIVE', 'RELEASED', 'CREDITED'].includes(s)) {
    return 'success';
  }
  if (['PROCESSING', 'FUNDED', 'IN_PROGRESS', 'IN_INSPECTION'].includes(s)) {
    return 'warning';
  }
  if (['FAILED', 'DOWN', 'DISCREPANCIES_FOUND', 'DISPUTED'].includes(s)) {
    return 'danger';
  }
  if (['REFUNDED', 'DEGRADED'].includes(s)) {
    return 'purple';
  }
  if (['PENDING', 'CREATED'].includes(s)) {
    return 'info';
  }
  return 'neutral';
}
