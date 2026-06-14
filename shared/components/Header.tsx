/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from "react";
import { useAppStore } from "../state/store";
import { DashboardTab } from "../types";
import { Search, Bell, Menu, ShieldAlert, Cpu, Sparkles, Clock, LogOut } from "lucide-react";

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const { activeTab, searchQuery, setSearchQuery, user, setIsAuthenticated, setActiveTab } = useAppStore();
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 1, text: "Model 'CreditGuard-ResNet18' successfully promoted to Production", time: "10m ago", icon: Cpu, color: "text-emerald-400" },
    { id: 2, text: "Anomaly detected: SSH connection attempt blocked", time: "1h ago", icon: ShieldAlert, color: "text-amber-400" },
    { id: 3, text: "Optuna hyperparameter study completed: best score 93.8%", time: "2h ago", icon: Sparkles, color: "text-teal-400" }
  ]);

  const [localTime, setLocalTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLocalTime(now.toISOString().replace("T", " ").substring(0, 19) + " UTC");
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getBreadcrumbName = (tab: DashboardTab) => {
    switch(tab) {
      case DashboardTab.OVERVIEW: return "Platform Overview";
      case DashboardTab.CREDIT_SCORING: return "Credit Scoring Benchmark";
      case DashboardTab.DISEASE_PREDICTION: return "Clinical Disease Prediction";
      case DashboardTab.HANDWRITING: return "Handwritten Character Canvas";
      case DashboardTab.COMPARISON: return "Advanced Model Comparison";
      case DashboardTab.LEADERBOARD: return "Model Leaderboard";
      case DashboardTab.DATASET_ANALYTICS: return "Dataset Analytics Engine";
      case DashboardTab.TRAINING_MONITOR: return "Live MLOps Training Monitor";
      case DashboardTab.MLFLOW: return "MLflow Experiment Tracking";
      case DashboardTab.OPTUNA: return "Optuna Hyperparameter Studies";
      case DashboardTab.MODEL_REGISTRY: return "Model Registry";
      case DashboardTab.REPORTS: return "Reports & Exported Assets";
      case DashboardTab.AI_ASSISTANT: return "Qwen Coder AI Assistant";
      case DashboardTab.DIGITAL_TWIN: return "AI Pipeline Digital Twin";
      case DashboardTab.SECURITY: return "MFA & Operations Security Audit";
      case DashboardTab.PROFILE: return "User Preference Profile";
      default: return "Dashboard";
    }
  };

  const handleClearNotify = (id: number) => {
    setNotifications(notifications.filter(n => n.id !== id));
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/10 bg-black/10 px-6 backdrop-blur-md">
      {/* Left side: Burger toggle & breadcrumb */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="rounded p-1 text-slate-450 hover:bg-white/10 hover:text-white md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500 font-medium font-bold">TRIVERSE ML</span>
          <span className="text-white/20 font-mono text-xs">/</span>
          <h2 className="font-sans text-xs font-semibold text-white tracking-wide uppercase">
            {getBreadcrumbName(activeTab)}
          </h2>
        </div>
      </div>

      {/* Right side: Search, Live clock, Notify, Profile */}
      <div className="flex items-center gap-4">
        {/* Search Input */}
        <div className="relative hidden max-w-xs md:block">
          <Search className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search experiments, metrics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 w-60 rounded-full border border-white/10 bg-white/5 pl-10 pr-4 text-xs text-slate-200 placeholder-slate-400 outline-none hover:border-white/20 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 focus:bg-white/10 transition-all"
          />
        </div>

        {/* Live System Time */}
        <div className="hidden lg:flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 font-mono text-[10px] text-slate-300 font-medium">
          <Clock className="h-3 w-3 text-cyan-400" />
          <span>{localTime}</span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 hover:bg-white/10 hover:text-white transition-all"
          >
            <Bell className="h-4 w-4" />
            {notifications.length > 0 && (
              <span className="absolute top-1 right-1 flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-500"></span>
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-white/10 bg-slate-950/95 p-4 shadow-2xl backdrop-blur-xl ring-1 ring-black/55 z-50">
              <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
                <span className="text-xs font-semibold text-white font-sans">System Alerts</span>
                <span className="text-[10px] text-slate-400 font-mono">{notifications.length} Info</span>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-[11px] text-slate-400 text-center py-4">No new system alerts.</p>
                ) : (
                  notifications.map((item) => {
                    const AlertIcon = item.icon;
                    return (
                      <div key={item.id} className="group relative flex gap-3 rounded-lg bg-white/5 p-2.5 border border-white/5 hover:border-white/10 hover:bg-white/10 transition-colors text-[11px]">
                        <AlertIcon className={`h-4.5 w-4.5 shrink-0 mt-0.5 ${item.color}`} />
                        <div className="flex-1 pr-4">
                          <p className="text-slate-200 leading-relaxed font-sans">{item.text}</p>
                          <span className="text-[9px] text-slate-450 font-mono inline-block mt-1">{item.time}</span>
                        </div>
                        <button 
                          onClick={() => handleClearNotify(item.id)}
                          className="absolute right-2 top-2 text-[10px] text-slate-400 hover:text-white"
                        >
                          ✕
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar Quicklink */}
        <button
          onClick={() => setActiveTab(DashboardTab.PROFILE)}
          className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 p-1 pr-3 text-xs font-medium text-slate-200 hover:border-white/20 transition-all active:scale-95"
        >
          <img
            src={user.avatarUrl}
            alt={user.name}
            className="h-6 w-6 rounded-full object-cover ring-1 ring-white/10"
          />
          <span className="hidden sm:inline font-sans text-[11px] max-w-[80px] truncate">{user.name.split(" ")[0]}</span>
        </button>
      </div>
    </header>
  );
}
