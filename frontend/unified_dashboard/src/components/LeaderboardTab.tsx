/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  ScatterChart, Scatter, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer, ZAxis
} from "recharts";
import { 
  Trophy, Award, Cpu, Eye, Star, Zap, Activity, Info
} from "lucide-react";

export default function LeaderboardTab() {
  const { models } = useAppStore();
  const [activeTaskFilter, setActiveTaskFilter] = useState("All");

  const computeModelScore = (m: any) => {
    const acc = m.accuracy || 0;
    const prec = m.precision || 0;
    const rec = m.recall || 0;
    
    // Normalize inference latency: 15 / (latency + 15)
    const latency = m.inferenceTimeMs || 15;
    const normSpeed = 15 / (latency + 15);
    
    // Normalize memory usage or training time. Since we have memoryMb, let's normalize footprint: 50 / (memoryMb + 50)
    const mem = m.memoryMb || 100;
    const normMem = 50 / (mem + 50);

    // Weighted Score: 40% Accuracy, 20% Precision, 20% Recall, 10% Latency, 10% Footprint
    const score = (acc * 0.40) + (prec * 0.20) + (rec * 0.20) + (normSpeed * 0.10) + (normMem * 0.10);
    return parseFloat((score * 100).toFixed(2));
  };

  // Sort model lists based on weighted scoring formula
  const scoredModels = models.map(m => ({
    ...m,
    weightedScore: computeModelScore(m)
  })).sort((a, b) => b.weightedScore - a.weightedScore);

  const bestOverall = scoredModels[0];
  const fastest = [...models].sort((a, b) => a.inferenceTimeMs - b.inferenceTimeMs)[0];
  const explainLeader = [...models].sort((a, b) => b.explainabilityScore - a.explainabilityScore)[0];
  const cleanResourceLeader = [...models].sort((a, b) => a.memoryMb - b.memoryMb)[0];

  const tasks = ["All", "Credit Scoring", "Disease Prediction", "Handwriting Recognition"];
  
  const displayRankings = scoredModels
    .filter(m => activeTaskFilter === "All" || m.task === activeTaskFilter);

  // Scatter plot data mapping Accuracy vs Latency
  const scatterData = models.map((m) => ({
    name: m.name,
    accuracy: parseFloat((m.accuracy * 100).toFixed(1)),
    latency: m.inferenceTimeMs,
    size: m.modelSizeMb
  }));

  // Ranking over historical checkpoints
  const historicalRankingTrend = [
    { name: "Baseline", ResNet18: 82.5, XGBoost: 79.1, CNN: 88.0, Advanced: 81.0 },
    { name: "HPO Alpha", ResNet18: 88.2, XGBoost: 84.6, CNN: 92.4, Advanced: 89.2 },
    { name: "GPU Match", ResNet18: 93.0, XGBoost: 89.0, CNN: 96.1, Advanced: 93.5 },
    { name: "RTX Final", ResNet18: 94.1, XGBoost: 89.8, CNN: 97.8, Advanced: 96.7 },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Bento Highlights */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-750 transition-all">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-550/10 border border-teal-500/20 mb-3 text-teal-400">
            <Trophy className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-550 uppercase font-bold block">Champion Overall Model</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{bestOverall?.name}</h4>
          <span className="text-[10px] text-teal-400 font-mono font-semibold uppercase mt-0.5 inline-block">Weighted: {bestOverall?.weightedScore} pts</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-750 transition-all">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 mb-3 text-blue-400">
            <Zap className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-550 uppercase font-bold block">Fastest Inference Speed</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{fastest?.name}</h4>
          <span className="text-[10px] text-blue-400 font-mono font-semibold uppercase mt-0.5 inline-block">Latency: {fastest?.inferenceTimeMs} MS</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-750 transition-all">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20 mb-3 text-amber-500">
            <Eye className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-550 uppercase font-bold block">Most Explainable AI</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{explainLeader?.name}</h4>
          <span className="text-[10px] text-amber-500 font-mono font-semibold uppercase mt-0.5 inline-block">{explainLeader?.explainabilityScore}/100 SHAP Gini</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-750 transition-all">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20 mb-3 text-emerald-400">
            <Cpu className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-550 uppercase font-bold block">Minimal resource footprint</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{cleanResourceLeader?.name}</h4>
          <span className="text-[10px] text-emerald-400 font-mono font-semibold uppercase mt-0.5 inline-block">{cleanResourceLeader?.memoryMb} MB VRAM</span>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wide flex items-center gap-2">
              <Award className="h-4.5 w-4.5 text-teal-400" />
              Unified Performance Index Leaderboard
            </h3>
            <p className="text-[10px] text-zinc-500 mt-0.5">Ranks calculated using the formula: 40% Accuracy, 20% Precision, 20% Recall, 10% Latency, 10% Resource Footprint.</p>
          </div>
          <div className="flex gap-2">
            {tasks.map((tsk) => (
              <button
                key={tsk}
                onClick={() => setActiveTaskFilter(tsk)}
                className={`rounded px-2.5 py-1 text-[10px] font-medium border transition-colors ${
                  activeTaskFilter === tsk 
                    ? "bg-teal-500 text-black border-transparent" 
                    : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:text-white"
                }`}
              >
                {tsk}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-zinc-805 bg-zinc-950/40">
          <table className="w-full text-left font-sans text-xs">
            <thead className="bg-zinc-900/60 font-mono text-[9px] uppercase tracking-wider text-zinc-550 border-b border-zinc-800">
              <tr>
                <th className="p-4 w-12 text-center">Rank</th>
                <th className="p-4">Model Name</th>
                <th className="p-4">Evaluating Task</th>
                <th className="p-4 text-center">Accuracy</th>
                <th className="p-4 text-center">Precision / Recall</th>
                <th className="p-4 text-center">Latency (ms)</th>
                <th className="p-4 text-center">VRAM Usage</th>
                <th className="p-4 text-center">Weighted Score</th>
                <th className="p-4 text-center">Stability Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/40">
              {displayRankings.map((m, idx) => (
                <tr key={m.id} className="hover:bg-zinc-900/20 transition-colors">
                  <td className="p-4 text-center font-mono font-bold text-zinc-550">
                    {idx === 0 ? (
                      <span className="flex items-center justify-center h-5 w-5 rounded-full bg-amber-500/10 text-amber-500 font-semibold text-[10px] mx-auto border border-amber-500/20">
                        1
                      </span>
                    ) : idx === 1 ? (
                      <span className="flex items-center justify-center h-5 w-5 rounded-full bg-zinc-400/10 text-zinc-300 font-semibold text-[10px] mx-auto border border-zinc-400/20">
                        2
                      </span>
                    ) : idx === 2 ? (
                      <span className="flex items-center justify-center h-5 w-5 rounded-full bg-amber-700/10 text-amber-600 font-semibold text-[10px] mx-auto border border-amber-700/20">
                        3
                      </span>
                    ) : (
                      `#${idx + 1}`
                    )}
                  </td>
                  <td className="p-4 flex items-center gap-2 font-semibold text-zinc-150">
                    <span>{m.name}</span>
                    {idx === 0 && <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 shrink-0" />}
                  </td>
                  <td className="p-4 text-zinc-450 font-medium">{m.task}</td>
                  <td className="p-4 text-center font-mono font-bold text-teal-400">{(m.accuracy * 100).toFixed(1)}%</td>
                  <td className="p-4 text-center font-mono text-zinc-500">{(m.precision * 100).toFixed(0)}% / {(m.recall * 100).toFixed(0)}%</td>
                  <td className="p-4 text-center font-mono text-zinc-450">{m.inferenceTimeMs}ms</td>
                  <td className="p-4 text-center font-mono text-zinc-500">{m.memoryMb}Mb</td>
                  <td className="p-4 text-center font-mono text-teal-500 font-bold text-[13px]">{m.weightedScore}</td>
                  <td className="p-4 text-center">
                    <span className="rounded bg-teal-500/10 px-2 py-0.5 text-[9px] font-mono text-teal-400 font-semibold uppercase">
                      {m.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Specialty scatter analytics */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Scatter Accuracy vs Latency */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
              <Activity className="h-4 w-4 text-teal-400" />
              Accuracy vs. Latency Efficient Frontier
            </h3>
            <p className="text-[10px] text-zinc-550 mt-0.5">Visualization of model accuracy relative to real-time inference latency. Optimal models reside in the top-left.</p>
          </div>
          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" dataKey="latency" name="Latency" unit="ms" stroke="#71717a" fontSize={9} tickLine={false} />
                <YAxis type="number" dataKey="accuracy" name="Accuracy" unit="%" stroke="#71717a" fontSize={9} domain={[80, 100]} tickLine={false} />
                <ZAxis type="number" dataKey="size" range={[60, 400]} name="Size" unit="Mb" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px", borderRadius: "8px" }} />
                <Scatter name="Models" data={scatterData} fill="#2dd4bf" line={false} shape="circle" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weekly rankings history line chart */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
              <Info className="h-4 w-4 text-blue-400" />
              Optimization History & Progression Track
            </h3>
            <p className="text-[10px] text-zinc-550 mt-0.5">Tracking performance gains of the core model backbones across successive iteration cycles.</p>
          </div>
          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalRankingTrend} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" stroke="#71717a" fontSize={9} tickLine={false} />
                <YAxis stroke="#71717a" fontSize={9} domain={[70, 100]} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px", borderRadius: "8px" }} />
                <Line type="monotone" dataKey="ResNet18" stroke="#2dd4bf" strokeWidth={2.5} name="ResNet18 Backbone" dot={{ r: 3 }} />
                <Line type="monotone" dataKey="XGBoost" stroke="#3b82f6" strokeWidth={2.5} name="Cardio XGBoost" dot={{ r: 3 }} />
                <Line type="monotone" dataKey="CNN" stroke="#ec4899" strokeWidth={2.5} name="HandScribe CNN" dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Advanced" stroke="#f59e0b" strokeWidth={2.5} name="TabNet / FT-Transformer" dot={{ r: 3 }} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
