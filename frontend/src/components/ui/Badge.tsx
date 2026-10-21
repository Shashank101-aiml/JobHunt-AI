import React from 'react';

interface BadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<BadgeProps> = ({ status, className = '' }) => {
  const normalized = status.toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';

  if (['submitted', 'active', 'ok', 'offer'].includes(normalized)) {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['ready_for_review', 'interviewing'].includes(normalized)) {
    styles = 'bg-indigo-50 text-indigo-700 border-indigo-200';
  } else if (['requires_manual_action', 'draft'].includes(normalized)) {
    styles = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['rejected', 'failed', 'unhealthy'].includes(normalized)) {
    styles = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['submission_in_progress'].includes(normalized)) {
    styles = 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse';
  }

  const formatText = (text: string) => {
    return text
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles} ${className}`}
    >
      {formatText(status)}
    </span>
  );
};
