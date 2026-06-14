/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useAppStore } from "../state/store";
import { DashboardTab } from "../types";
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { 
  Layers, Cpu, Trophy, Database, Target, Clock, ArrowUpRight, CheckCircle, AlertCircle, RefreshCw
} from "lucide-react";

export default function OverviewTab() {
  const { experiments, models, setActiveTab, searchQuery } = useAppStore();
  const [filterStatus, setFilterStatus] = useState<string>("All");

  // KPI calculations
  const totalExps = experiments.length;
  const totalModels = models.length;
  
  const completedExps = experiments.filter(e => e.status === "Completed").length;
  const bestAccuracy = totalModels > 0 ? Math.max(...models.map(m => m.accuracy)) * 100 : 0;
  const bestModelName = totalModels > 0 ? models.reduce((prev, current) => (prev.accuracy > current.accuracy) ? prev : current).name : "No Models Trained";
  const latestExp = experiments[0];

  // Map charts data
  const trendData = [
    { name: "Mon", CreditGuard: 0.88, CardioScan: 0.82, HandScribe: 0.91 },
    { name: "Tue", CreditGuard: 0.89, CardioScan: 0.84, HandScribe: 0.93 },
    { name: "Wed", CreditGuard: 0.91, CardioScan: 0.85, HandScribe: 0.95 },
    { name: "Thu", CreditGuard: 0.92, CardioScan: 0.87, HandScribe: 0.96 },
    { name: "Fri", CreditGuard: 0.94, CardioScan: 0.89, HandScribe: 0.97 },
    { name: "Sat", CreditGuard: 0.94, CardioScan: 0.90, HandScribe: 0.97 },
    { name: "Sun", CreditGuard: 0.941, CardioScan: 0.898, HandScribe: 0.978 },
  ];

  const resourceData = [
    { name: "CreditGuard-ResNet18", CPU: 65, RAM: 45, GPU: 85 },
    { name: "CardioScan-XGBoost", CPU: 12, RAM: 15, GPU: 0 },
    { name: "HandScribe-CNN", CPU: 40, RAM: 30, GPU: 65 },
    { name: "Credit-LightGBM", CPU: 22, RAM: 18, GPU: 0 },
  ];

  const filteredExperiments = experiments.filter(e => {
    const matchesSearch = e.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          e.modelType.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === "All" || e.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* KPI Cards section */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Total Experiments</span>
            <Layers className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-semibold tracking-tight text-white">{totalExps}</span>
            <span className="text-[10px] text-cyan-450 font-mono font-medium">+{completedExps} done</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Trained Models</span>
            <Cpu className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-semibold tracking-tight text-white">{totalModels}</span>
            <span className="text-[10px] text-slate-400 font-mono">4 active production</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Best Peak Accuracy</span>
            <Trophy className="h-4 w-4 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-semibold tracking-tight text-white">{bestAccuracy.toFixed(1)}%</span>
            <span className="text-[10px] text-slate-400 font-mono">HandScribe</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Active Catalog</span>
            <Database className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-sm font-semibold tracking-tight text-slate-200 truncate">FICO, MIMIC-IV</span>
            <span className="text-[9px] text-cyan-400 font-mono font-medium">3 sets</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Champion Model</span>
            <Target className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-3">
            <span className="text-[11px] font-semibold tracking-tight text-slate-300 block truncate">{bestModelName}</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold">Latest Pipeline Run</span>
            <Clock className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-xs font-semibold tracking-tight text-white truncate">{latestExp?.name}</span>
            <span className="text-[9px] text-slate-400 font-mono uppercase mt-0.5">{latestExp?.status}</span>
          </div>
        </div>
      </div>

      {/* Main Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Chart 1: Global Accuracy Trend */}
        <div className="glass-panel p-5 shadow-lg">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-200">Global Accuracy Progression Trend</h3>
              <p className="text-[10px] text-slate-400">Validation score progress over weekly checkpoint cohorts</p>
            </div>
            <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[9px] font-mono text-cyan-400 font-semibold uppercase">Daily Runs</span>
          </div>
          <div className="h-72 w-full min-w-0">
            <ResponsiveContainer width="100%" height={288} minWidth={0}>
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCredit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorHand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} domain={[0.7, 1.0]} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "rgba(255,255,255,0.1)", fontSize: "11px", borderRadius: "8px" }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                <Area type="monotone" dataKey="CreditGuard" name="CreditGuard ResNet" stroke="#2dd4bf" strokeWidth={2} fillOpacity={1} fill="url(#colorCredit)" />
                <Area type="monotone" dataKey="HandScribe" name="HandScribe CNN" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorHand)" />
                <Line type="monotone" dataKey="CardioScan" name="CardioScan XGB" stroke="#e11d48" strokeWidth={2.5} dot={{ r: 3 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Resource Footprint */}
        <div className="glass-panel p-5 shadow-lg">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-200">Device Hardware Resource Allocation Footprint</h3>
              <p className="text-[10px] text-slate-400">Utilization percentage across key model architectures</p>
            </div>
            <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[9px] font-mono text-cyan-400 font-semibold uppercase">Cluster Core</span>
          </div>
          <div className="h-72 w-full min-w-0">
            <ResponsiveContainer width="100%" height={288} minWidth={0}>
              <BarChart data={resourceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={9} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "rgba(255,255,255,0.1)", fontSize: "11px", borderRadius: "8px" }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                <Bar dataKey="CPU" fill="#2dd4bf" radius={[4, 4, 0, 0]} barSize={12} />
                <Bar dataKey="RAM" fill="#a1a1aa" radius={[4, 4, 0, 0]} barSize={12} />
                <Bar dataKey="GPU" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Structured Recent Experiments Table */}
      <div className="glass-panel p-5 shadow-lg">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xs font-semibold text-white">Recent Experiments Pipeline Execution</h3>
            <p className="text-[10px] text-slate-400">Historical performance logs from local optimization loops</p>
          </div>
          <div className="flex gap-2">
            {["All", "Completed", "Running", "Failed"].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`rounded px-2.5 py-1 text-[10px] font-medium transition-colors ${filterStatus === st ? "bg-white/10 text-white border border-white/10" : "bg-white/5 text-slate-450 hover:text-white"}`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-white/10 bg-black/10">
          <table className="w-full text-left font-sans text-xs">
            <thead className="bg-white/5 font-mono text-[10px] uppercase text-slate-400 font-bold border-b border-white/10">
              <tr>
                <th className="p-4">Experiment Name</th>
                <th className="p-4">Model Type</th>
                <th className="p-4">Dataset Segment</th>
                <th className="p-4">Metric Score</th>
                <th className="p-4">Loss Value</th>
                <th className="p-4">Runtime</th>
                <th className="p-4">Execution Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredExperiments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">No experiments match the filter criteria.</td>
                </tr>
              ) : (
                filteredExperiments.map((exp) => (
                  <tr key={exp.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 font-medium text-white">{exp.name}</td>
                    <td className="p-4 text-slate-350">{exp.modelType}</td>
                    <td className="p-4 font-mono text-[11px] text-slate-450">{exp.dataset}</td>
                    <td className="p-4 font-semibold text-cyan-400">{(exp.metricValue * 100).toFixed(1)}%</td>
                    <td className="p-4 text-slate-400 font-mono text-[11px]">{exp.loss.toFixed(4)}</td>
                    <td className="p-4 text-slate-450 font-mono">{Math.floor(exp.durationSeconds / 60)}m {exp.durationSeconds % 60}s</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${
                        exp.status === "Completed" ? "bg-green-500/10 text-green-400 border border-green-500/20" : 
                        exp.status === "Running" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse" :
                        exp.status === "Failed" ? "bg-red-500/10 text-red-500 border border-red-500/20" : 
                        "bg-slate-500/10 text-slate-450 border border-white/5"
                      }`}>
                        {exp.status === "Completed" && <CheckCircle className="h-2.5 w-2.5" />}
                        {exp.status === "Running" && <RefreshCw className="h-2.5 w-2.5 animate-spin" />}
                        {exp.status === "Failed" && <AlertCircle className="h-2.5 w-2.5" />}
                        {exp.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
