/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { DashboardTab } from "../types";
import { useAppStore } from "../state/store";
import { 
  LayoutDashboard, 
  CreditCard, 
  HeartPulse, 
  Activity, 
  Sparkles, 
  TrendingUp, 
  BarChart3, 
  MonitorPlay, 
  GitBranch, 
  Sliders, 
  Database,
  FileSpreadsheet, 
  Cpu, 
  ShieldCheck, 
  User, 
  LogOut 
} from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { activeTab, setActiveTab, user, setIsAuthenticated } = useAppStore();

  const navigationItems = [
    { tab: DashboardTab.OVERVIEW, label: "Overview", icon: LayoutDashboard, category: "Core" },
    { tab: DashboardTab.CREDIT_SCORING, label: "Credit Scoring", icon: CreditCard, category: "Specialties" },
    { tab: DashboardTab.DISEASE_PREDICTION, label: "Disease Prediction", icon: HeartPulse, category: "Specialties" },
    { tab: DashboardTab.HANDWRITING, label: "Handwriting Recog.", icon: Activity, category: "Specialties" },
    { tab: DashboardTab.COMPARISON, label: "Model Comparison", icon: TrendingUp, category: "Analytics" },
    { tab: DashboardTab.LEADERBOARD, label: "Leaderboard", icon: BarChart3, category: "Analytics" },
    { tab: DashboardTab.DATASET_ANALYTICS, label: "Dataset Analytics", icon: Database, category: "Data" },
    { tab: DashboardTab.TRAINING_MONITOR, label: "Training Monitor", icon: MonitorPlay, category: "MLOps" },
    { tab: DashboardTab.MLFLOW, label: "MLflow Tracking", icon: GitBranch, category: "MLOps" },
    { tab: DashboardTab.OPTUNA, label: "Optuna Trials", icon: Sliders, category: "MLOps" },
    { tab: DashboardTab.MODEL_REGISTRY, label: "Model Registry", icon: Cpu, category: "Core" },
    { tab: DashboardTab.REPORTS, label: "Reports & Assets", icon: FileSpreadsheet, category: "Core" },
    { tab: DashboardTab.AI_ASSISTANT, label: "AI Copilot", icon: Sparkles, category: "Specialties" },
    { tab: DashboardTab.DIGITAL_TWIN, label: "Digital Twin", icon: Cpu, category: "Analytics" },
    { tab: DashboardTab.SECURITY, label: "Security & Auditing", icon: ShieldCheck, category: "Core" },
  ];

  const categories = ["Core", "Specialties", "Analytics", "Data", "MLOps"];

  const handleSelect = (tab: DashboardTab) => {
    setActiveTab(tab);
    if (onClose) onClose();
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  return (
    <aside id="app-sidebar" className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/10 bg-white/[0.015] backdrop-blur-2xl transition-transform duration-300 pointer-events-auto md:sticky md:transform-none ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
      {/* Title / Logo Header */}
      <div className="flex h-16 items-center border-b border-white/10 px-6 justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-indigo-600 font-sans text-sm font-bold text-white shadow-lg shadow-cyan-500/20">
            T
          </div>
          <div>
            <h1 className="font-sans text-sm font-bold tracking-tight text-white uppercase">
              TriVerse ML
            </h1>
            <span className="font-mono text-[9px] text-cyan-400 font-semibold tracking-widest uppercase">
              MLOPs Platform
            </span>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-white/10 hover:text-white md:hidden">
            ✕
          </button>
        )}
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {categories.map((category) => {
          const items = navigationItems.filter((i) => i.category === category);
          return (
            <div key={category} className="space-y-1">
              <h3 className="px-2 font-sans text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2 ml-1">
                {category}
              </h3>
              <div className="space-y-[2px]">
                {items.map((item) => {
                  const IconComponent = item.icon;
                  const isActive = activeTab === item.tab;
                  return (
                    <button
                      key={item.tab}
                      onClick={() => handleSelect(item.tab)}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all ${isActive ? "bg-white/10 text-white border border-white/5 shadow-sm" : "text-slate-400 hover:bg-white/5 hover:text-white border border-transparent"}`}
                    >
                      <IconComponent className={`h-4 w-4 shrink-0 transition-transform ${isActive ? "text-cyan-400 scale-105" : "text-slate-500"}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* User Section */}
      <div className="border-t border-white/10 p-4 bg-black/10 backdrop-blur-md">
        <button
          onClick={() => handleSelect(DashboardTab.PROFILE)}
          className={`flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors ${activeTab === DashboardTab.PROFILE ? "bg-white/10 text-white" : "hover:bg-white/5 text-slate-300"}`}
        >
          <img
            src={user.avatarUrl}
            alt={user.name}
            className="h-9 w-9 rounded-full object-cover ring-2 ring-white/10"
          />
          <div className="min-w-0 flex-1">
            <h4 className="truncate text-xs font-semibold text-white">
              {user.name}
            </h4>
            <p className="truncate text-[10px] text-slate-400">
              {user.role}
            </p>
          </div>
        </button>

        <button
          onClick={handleLogout}
          className="mt-3 flex w-full items-center gap-2 rounded-lg bg-white/5 border border-white/5 px-3 py-2 text-[11px] font-medium text-slate-350 hover:bg-red-500/20 hover:text-red-400 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span>Exit Secure Session</span>
        </button>
      </div>
    </aside>
  );
}
