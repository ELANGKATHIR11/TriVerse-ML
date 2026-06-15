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

  // Helper to detect advanced models
  const isAdvanced = (name: string) => {
    const ln = name.toLowerCase();
    return ln.includes("tabnet") || ln.includes("ft_transformer") || ln.includes("ft-transformer") || ln.includes("efficientnet") || ln.includes("transformer");
  };

  // KPI calculations
  const totalExps = experiments.length;
  const totalModels = models.length;
  const completedExps = experiments.filter(e => e.status === "Completed").length;
  const latestExp = totalExps > 0 ? experiments[totalExps - 1] : null;

  const creditModels = models.filter(m => m.task === "Credit Scoring");
  const diseaseModels = models.filter(m => m.task === "Disease Prediction");
  const visionModels = models.filter(m => m.task === "Handwriting Recognition");

  // Find Best Legacy and Advanced models
  const legacyModels = models.filter(m => !isAdvanced(m.name));
  const advancedModels = models.filter(m => isAdvanced(m.name));

  const bestLegacy = legacyModels.length > 0 ? legacyModels.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;
  const bestAdvanced = advancedModels.length > 0 ? advancedModels.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;

  // Winners per task
  const creditWinner = creditModels.length > 0 ? creditModels.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;
  const diseaseWinner = diseaseModels.length > 0 ? diseaseModels.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;
  const visionWinner = visionModels.length > 0 ? visionModels.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;

  // Global Champion (Highest accuracy)
  const globalChamp = models.length > 0 ? models.reduce((p, c) => p.accuracy > c.accuracy ? p : c) : null;

  // Specialized leaders
  const fastestModel = models.length > 0 ? models.reduce((p, c) => p.inferenceTimeMs < c.inferenceTimeMs ? p : c) : null;
  const lowestMemoryModel = models.length > 0 ? models.reduce((p, c) => p.memoryMb < c.memoryMb ? p : c) : null;
  const highestExplainable = models.length > 0 ? models.reduce((p, c) => p.explainabilityScore > c.explainabilityScore ? p : c) : null;

  // Map charts data
  const trendData = [
    { name: "Mon", CreditGuard: 0.88, CardioScan: 0.82, HandScribe: 0.91 },
    { name: "Tue", CreditGuard: 0.89, CardioScan: 0.84, HandScribe: 0.93 },
    { name: "Wed", CreditGuard: 0.91, CardioScan: 0.85, HandScribe: 0.95 },
    { name: "Thu", CreditGuard: 0.92, CardioScan: 0.87, HandScribe: 0.96 },
    { name: "Fri", CreditGuard: 0.94, CardioScan: 0.89, HandScribe: 0.97 },
    { name: "Sat", CreditGuard: 0.94, CardioScan: 0.90, HandScribe: 0.97 },
    { name: "Sun", CreditGuard: (globalChamp?.accuracy ?? 0.941), CardioScan: (diseaseWinner?.accuracy ?? 0.898), HandScribe: (visionWinner?.accuracy ?? 0.978) },
  ];

  const resourceData = models.map(m => ({
    name: m.name.substring(0, 15),
    CPU: m.name.toLowerCase().includes("cnn") ? 40 : 15,
    RAM: Math.round(m.memoryMb / 3),
    GPU: isAdvanced(m.name) ? 80 : 0
  })).slice(0, 5);

  const filteredExperiments = experiments.filter(e => {
    const matchesSearch = e.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          e.modelType.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === "All" || e.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Target Champion Summary Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="glass-panel p-4 border-l-4 border-l-teal-500 hover:bg-white/5 transition-all">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold font-mono">Credit scoring Winner</div>
          <div className="text-lg font-semibold text-white mt-1 truncate">{creditWinner ? creditWinner.name : "None"}</div>
          <div className="text-xs text-teal-400 font-mono mt-0.5">Acc: {creditWinner ? (creditWinner.accuracy * 100).toFixed(1) : 0}%</div>
        </div>
        <div className="glass-panel p-4 border-l-4 border-l-blue-500 hover:bg-white/5 transition-all">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold font-mono">Disease Prediction Winner</div>
          <div className="text-lg font-semibold text-white mt-1 truncate">{diseaseWinner ? diseaseWinner.name : "None"}</div>
          <div className="text-xs text-blue-400 font-mono mt-0.5">Acc: {diseaseWinner ? (diseaseWinner.accuracy * 100).toFixed(1) : 0}%</div>
        </div>
        <div className="glass-panel p-4 border-l-4 border-l-purple-500 hover:bg-white/5 transition-all">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold font-mono">Vision recognition Winner</div>
          <div className="text-lg font-semibold text-white mt-1 truncate">{visionWinner ? visionWinner.name : "None"}</div>
          <div className="text-xs text-purple-400 font-mono mt-0.5">Acc: {visionWinner ? (visionWinner.accuracy * 100).toFixed(1) : 0}%</div>
        </div>
        <div className="glass-panel p-4 border-l-4 border-l-amber-500 bg-amber-500/5 hover:bg-amber-500/10 transition-all">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold font-mono">Global platform Champion</div>
          <div className="text-lg font-semibold text-white mt-1 truncate">{globalChamp ? globalChamp.name : "None"}</div>
          <div className="text-xs text-amber-400 font-mono mt-0.5">Acc: {globalChamp ? (globalChamp.accuracy * 100).toFixed(1) : 0}%</div>
        </div>
      </div>

      {/* KPI Cards section */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Best Legacy Model</span>
            <Trophy className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white truncate">{bestLegacy ? bestLegacy.name : "N/A"}</span>
            <span className="text-[10px] text-slate-400 font-mono">Acc: {bestLegacy ? (bestLegacy.accuracy * 100).toFixed(1) : 0}%</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Best Advanced Model</span>
            <Trophy className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white truncate">{bestAdvanced ? bestAdvanced.name : "N/A"}</span>
            <span className="text-[10px] text-cyan-400 font-mono">Acc: {bestAdvanced ? (bestAdvanced.accuracy * 100).toFixed(1) : 0}%</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Fastest Inference</span>
            <Clock className="h-3.5 w-3.5 text-green-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white truncate">{fastestModel ? fastestModel.name : "N/A"}</span>
            <span className="text-[10px] text-green-450 font-mono">{fastestModel ? fastestModel.inferenceTimeMs.toFixed(2) : 0} ms</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Most Efficient</span>
            <Cpu className="h-3.5 w-3.5 text-purple-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white truncate">{lowestMemoryModel ? lowestMemoryModel.name : "N/A"}</span>
            <span className="text-[10px] text-purple-400 font-mono">{lowestMemoryModel ? lowestMemoryModel.memoryMb : 0} MB RAM</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Explainability Leader</span>
            <Target className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white truncate">{highestExplainable ? highestExplainable.name : "N/A"}</span>
            <span className="text-[10px] text-amber-400 font-mono">Score: {highestExplainable ? highestExplainable.explainabilityScore : 0}/100</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Active Catalog</span>
            <Database className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-sm font-semibold text-slate-200 truncate">FICO, Heart, MNIST</span>
            <span className="text-[9px] text-cyan-400 font-mono font-medium">6 sub-datasets</span>
          </div>
        </div>

        <div className="glass-panel p-4 relative overflow-hidden group hover:bg-white/10 transition-all duration-200">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 font-bold">Pipeline Execs</span>
            <Layers className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-2 flex flex-col">
            <span className="text-lg font-semibold text-white">{totalExps} Runs</span>
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
