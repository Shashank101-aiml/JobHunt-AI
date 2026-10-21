import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  Sparkles,
  Wand2,
  ClipboardList,
  Settings,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { resumeApi } from '../../services/resumeApi';
import { Resume } from '../../types';

interface SidebarProps {
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onCloseMobile }) => {
  const [activeResume, setActiveResume] = useState<Resume | null>(null);

  useEffect(() => {
    resumeApi
      .getActiveResume()
      .then((res) => setActiveResume(res))
      .catch(() => setActiveResume(null));
  }, []);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/resumes', label: 'Resume Manager', icon: FileText },
    { to: '/jobs', label: 'Job Discovery', icon: Briefcase },
    { to: '/match', label: 'Match & ATS Analysis', icon: Sparkles },
    { to: '/tailor', label: 'Resume Tailoring', icon: Wand2 },
    { to: '/applications', label: 'Applications', icon: ClipboardList },
    { to: '/settings', label: 'Settings & Health', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-indigo-100">
          <Briefcase className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-slate-900 text-base leading-none block">Job Hunt</span>
          <span className="text-[11px] font-medium text-indigo-600 tracking-wide uppercase">AI Platform</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onCloseMobile}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-50 text-indigo-600 font-semibold shadow-sm shadow-indigo-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Active Resume Status Card */}
      <div className="p-3 border-t border-slate-100 m-3 bg-slate-50 rounded-xl">
        <div className="flex items-center gap-2 mb-1.5">
          {activeResume ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />
          )}
          <span className="text-xs font-semibold text-slate-700">Active Resume</span>
        </div>
        {activeResume ? (
          <div>
            <p className="text-xs font-medium text-slate-900 truncate" title={activeResume.filename}>
              {activeResume.filename}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {activeResume.structured_profile?.contact_info?.name || 'Parsed Profile'}
            </p>
          </div>
        ) : (
          <p className="text-[11px] text-slate-500">No active resume. Upload in Resume Manager.</p>
        )}
      </div>
    </aside>
  );
};
