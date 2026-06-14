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
  Trophy, Flame, Award, ShieldAlert, Cpu, Eye, CheckCircle2, Star, Zap
} from "lucide-react";

export default function LeaderboardTab() {
  const { models } = useAppStore();
  const [activeTaskFilter, setActiveTaskFilter] = useState("All");

  // Sort model lists
  const sortedByAcc = [...models].sort((a, b) => b.accuracy - a.accuracy);
  const sortedBySpeed = [...models].sort((a, b) => a.inferenceTimeMs - b.inferenceTimeMs);
  const sortedByExplain = [...models].sort((a, b) => b.explainabilityScore - a.explainabilityScore);
  const sortedByResource = [...models].sort((a, b) => a.memoryMb - b.memoryMb);

  const bestOverall = sortedByAcc[0];
  const fastest = sortedBySpeed[0];
  const explainLeader = sortedByExplain[0];
  const cleanResourceLeader = sortedByResource[0];

  const tasks = ["All", "Credit Scoring", "Disease Prediction", "Handwriting Recognition"];
  const displayRankings = models
    .filter(m => activeTaskFilter === "All" || m.task === activeTaskFilter)
    .sort((a, b) => b.accuracy - a.accuracy);

  // Scatter plot data mapping Accuracy vs Latency
  const scatterData = models.map((m) => ({
    name: m.name,
    accuracy: parseFloat((m.accuracy * 100).toFixed(1)),
    latency: m.inferenceTimeMs,
    size: m.modelSizeMb
  }));

  // Ranking over historical weeks
  const historicalRankingTrend = [
    { name: "Wk 22", ResNet18: 0.88, XGBoost: 0.82, CNN: 0.91 },
    { name: "Wk 23", ResNet18: 0.91, XGBoost: 0.84, CNN: 0.94 },
    { name: "Wk 24", ResNet18: 0.93, XGBoost: 0.89, CNN: 0.96 },
    { name: "Wk 25", ResNet18: 0.941, XGBoost: 0.898, CNN: 0.978 },
  ];

  return (
    <div className="space-y-6">
      {/* Dynamic Bento Highlights */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-700 transition">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/20 mb-3 text-teal-400">
            <Trophy className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-500 uppercase font-bold block">Champion Overall Model</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{bestOverall?.name}</h4>
          <span className="text-[10px] text-teal-400 font-mono font-semibold uppercase mt-0.5 inline-block">Score: {(bestOverall?.accuracy * 100).toFixed(1)}% Acc</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-700 transition">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 mb-3 text-blue-400">
            <Zap className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-500 uppercase font-bold block">Fastest Inference Speed</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{fastest?.name}</h4>
          <span className="text-[10px] text-blue-400 font-mono font-semibold uppercase mt-0.5 inline-block">Latency: {fastest?.inferenceTimeMs} MS</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-700 transition">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20 mb-3 text-amber-500">
            <Eye className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-500 uppercase font-bold block">Most Explainable AI</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{explainLeader?.name}</h4>
          <span className="text-[10px] text-amber-500 font-mono font-semibold uppercase mt-0.5 inline-block">{explainLeader?.explainabilityScore}/100 SHAP Gini</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 relative overflow-hidden group hover:border-zinc-700 transition">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20 mb-3 text-emerald-450">
            <Cpu className="h-5 w-5" />
          </div>
          <span className="font-mono text-[9px] text-zinc-500 uppercase font-bold block">Minimal resource footprint</span>
          <h4 className="text-sm font-semibold text-zinc-200 mt-1 truncate">{cleanResourceLeader?.name}</h4>
          <span className="text-[10px] text-emerald-400 font-mono font-semibold uppercase mt-0.5 inline-block">{cleanResourceLeader?.memoryMb} MB VRAM</span>
        </div>
      </div>

      {/* Global & Task specific leaderboard table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xs font-semibold text-zinc-200">System Global Model Leaderboard</h3>
            <p className="text-[10px] text-zinc-500 font-medium">Verified benchmarks across testing holdout datasets</p>
          </div>
          <div className="flex gap-2">
            {tasks.map((tsk) => (
              <button
                key={tsk}
                onClick={() => setActiveTaskFilter(tsk)}
                className={`rounded px-2.5 py-1 text-[10px] font-medium transition-colors ${activeTaskFilter === tsk ? "bg-teal-500 text-black" : "bg-zinc-900 text-zinc-400 hover:text-white"}`}
              >
                {tsk}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-zinc-805 bg-zinc-950/40">
          <table className="w-full text-left font-sans text-xs">
            <thead className="bg-zinc-900/60 font-mono text-[10px] uppercase text-zinc-500 font-bold border-b border-zinc-800">
              <tr>
                <th className="p-4 w-12">Rank</th>
                <th className="p-4">Model Name</th>
                <th className="p-4">Evaluating Task</th>
                <th className="p-4">Accuracy</th>
                <th className="p-4">Precision / Recall</th>
                <th className="p-4">Latency</th>
                <th className="p-4">File size</th>
                <th className="p-4">Stability status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {displayRankings.map((m, idx) => (
                <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-4 font-mono font-bold text-zinc-500">#{idx + 1}</td>
                  <td className="p-4 flex items-center gap-2 font-semibold text-zinc-100">
                    <span>{m.name}</span>
                    {idx === 0 && <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 shrink-0" />}
                  </td>
                  <td className="p-4 text-zinc-400">{m.task}</td>
                  <td className="p-4 font-mono font-bold text-teal-400">{(m.accuracy * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-zinc-500">{(m.precision * 100).toFixed(0)}% / {(m.recall * 100).toFixed(0)}%</td>
                  <td className="p-4 font-mono text-zinc-450">{m.inferenceTimeMs}ms</td>
                  <td className="p-4 font-mono text-zinc-500">{m.modelSizeMb}Mb</td>
                  <td className="p-4">
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
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Precision Latency Frontier (Accuracy % vs Speed Ms)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" dataKey="latency" name="Latency" unit="ms" stroke="#52525b" fontSize={10} />
                <YAxis type="number" dataKey="accuracy" name="Accuracy" unit="%" stroke="#52525b" fontSize={10} domain={[80, 100]} />
                <ZAxis type="number" dataKey="size" range={[60, 400]} name="Size" unit="Mb" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Scatter name="Models" data={scatterData} fill="#2dd4bf" line={false} shape="circle" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weekly rankings history line chart */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Weekly Accuracy Progression Checkpoints</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalRankingTrend} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" stroke="#52525b" fontSize={10} />
                <YAxis stroke="#52525b" fontSize={10} domain={[0.8, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Line type="monotone" dataKey="ResNet18" stroke="#2dd4bf" strokeWidth={2} name="ResNet18 Backbone" />
                <Line type="monotone" dataKey="XGBoost" stroke="#3b82f6" strokeWidth={2} name="Cardio XGBoost" />
                <Line type="monotone" dataKey="CNN" stroke="#ec4899" strokeWidth={2} name="HandScribe CNN" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
