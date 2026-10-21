import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 text-xs',
    md: 'w-6 h-6 text-sm',
    lg: 'w-10 h-10 text-base',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 space-y-3 ${className}`}>
      <Loader2 className={`${sizeClasses[size].split(' ')[0]} ${sizeClasses[size].split(' ')[1]} animate-spin text-indigo-600`} />
      {message && <p className={`text-slate-500 font-medium ${sizeClasses[size].split(' ')[2]}`}>{message}</p>}
    </div>
  );
};
