/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer 
} from "recharts";
import { 
  Sliders, Trophy, RefreshCw, BarChart3, HelpCircle, Activity 
} from "lucide-react";

export default function OptunaTab() {
  const { optunaTrials, bestTrialValue } = useAppStore();
  const [activeOptimizerFilter, setActiveOptimizerFilter] = useState("All");

  const filteredTrials = optunaTrials.filter(t => 
    activeOptimizerFilter === "All" || t.params.optimizer === activeOptimizerFilter
  );

  // Parse chart coordinates data
  const optimizationHistory = optunaTrials.map(t => ({
    trial: `T-${t.trialNumber}`,
    value: t.value,
    bestVal: Math.max(...optunaTrials.slice(0, t.trialNumber).map(o => o.value))
  }));

  // Hyperparameter Importance Data Matrix
  const parameterImportance = [
    { name: "Learning Rate", weight: 46.2 },
    { name: "Dropout Ratio", weight: 28.5 },
    { name: "Optimizer Type", weight: 14.1 },
    { name: "Layer Blocks Count", weight: 8.4 },
    { name: "Regularization Penalty", weight: 2.8 },
  ];

  return (
    <div className="space-y-6">
      {/* Dynamic Headers */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Sliders className="h-5 w-5 text-teal-400" />
          <div>
            <h2 className="text-xs font-semibold text-zinc-200">Optuna Hyperparameter autotuners</h2>
            <p className="text-[10px] text-zinc-500">Auto-tuned search trials executing pruning heuristics.</p>
          </div>
        </div>
        <div className="rounded-lg border border-teal-500/15 bg-teal-500/5 px-3 py-1.5 font-mono text-[10.5px] text-teal-400 font-bold">
          Champ score Overall: {(bestTrialValue * 100).toFixed(1)}% Acc (Trial 6)
        </div>
      </div>

      {/* Specialty Optuna Graphs */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Optuna Search Value progress */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-8">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Optimization trial history objective progression</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={optimizationHistory} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="trial" stroke="#52525b" fontSize={10} />
                <YAxis stroke="#52525b" fontSize={10} domain={[0.7, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={1} dot={{ r: 4 }} name="Trial Score" />
                <Line type="stepAfter" dataKey="bestVal" stroke="#2dd4bf" strokeWidth={2.5} name="Best Champion value" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Feature Importance weights */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-4">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Gini Parameter importance analysis</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={parameterImportance} layout="vertical" margin={{ top: 10, right: 10, left: 35, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                <XAxis type="number" stroke="#52525b" fontSize={10} />
                <YAxis dataKey="name" type="category" stroke="#52525b" fontSize={10} width={90} />
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Bar dataKey="weight" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Weight %" barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Simulated Parallel Coordinate coordinate diagram */}
      <div className="rounded-xl border border-zinc-850 bg-zinc-900/20 p-5">
        <h3 className="text-xs font-semibold text-zinc-200 mb-3">Hyperparameter slice space parallel coordinates</h3>
        <p className="text-[11px] text-zinc-500 mb-4">Evaluate multi-dimensional correlations between Learning Rates, Dropout densities, and Objective Values.</p>
        
        {/* Vector coordinate map using beautiful SVGs */}
        <div className="border border-zinc-800 rounded-lg p-5 bg-zinc-950/45 relative h-48 overflow-hidden font-mono text-[9px] text-zinc-500">
          <svg className="absolute inset-0 h-full w-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
            <line x1="20%" y1="10%" x2="20%" y2="90%" stroke="#3f3f46" strokeWidth="2" strokeDasharray="2 2" />
            <line x1="40%" y1="10%" x2="40%" y2="90%" stroke="#3f3f46" strokeWidth="2" strokeDasharray="2 2" />
            <line x1="60%" y1="10%" x2="60%" y2="90%" stroke="#3f3f46" strokeWidth="2" strokeDasharray="2 2" />
            <line x1="80%" y1="10%" x2="80%" y2="90%" stroke="#3f3f46" strokeWidth="2" strokeDasharray="2 2" />

            {/* Trial vectors */}
            <path d="M 120 40 L 240 100 L 360 120 L 480 30" fill="none" stroke="#2dd4bf" strokeWidth="2" opacity="0.8" />
            <path d="M 120 80 L 240 60 L 360 80 L 480 90" fill="none" stroke="#3b82f6" strokeWidth="1.5" opacity="0.5" />
            <path d="M 120 120 L 240 130 L 360 40 L 480 120" fill="none" stroke="#f43f5e" strokeWidth="1" opacity="0.4" />
          </svg>

          {/* Labels floating */}
          <div className="absolute top-4 left-[15%]">LR: 0.1</div>
          <div className="absolute bottom-4 left-[15%]">LR: 0.0001</div>

          <div className="absolute top-4 left-[35%]">Dropout: 0.4</div>
          <div className="absolute bottom-4 left-[35%]">Dropout: 0.1</div>

          <div className="absolute top-4 left-[55%]">Layers: 6</div>
          <div className="absolute bottom-4 left-[55%]">Layers: 2</div>

          <div className="absolute top-4 left-[75%] font-bold text-teal-400">Objective: 93.8%</div>
          <div className="absolute bottom-4 left-[75%] text-rose-400">Objective: 72.0%</div>
        </div>
      </div>

      {/* Trial Listings Tables */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-xs font-semibold text-zinc-200">Execution grid history of trials</h3>
          <div className="flex gap-2">
            {["All", "AdamW", "Adam", "SGD"].map((opt) => (
              <button
                key={opt}
                onClick={() => setActiveOptimizerFilter(opt)}
                className={`rounded px-2.5 py-1 text-[10px] font-medium transition-all ${activeOptimizerFilter === opt ? "bg-teal-500 text-black" : "bg-zinc-900 text-zinc-400 hover:text-white"}`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-zinc-808 bg-zinc-950/40 font-sans text-xs">
          <table className="w-full text-left">
            <thead className="bg-zinc-900/60 font-mono text-[9.5px] uppercase text-zinc-500 font-bold border-b border-zinc-800">
              <tr>
                <th className="p-4">Trial ID</th>
                <th className="p-4">Heuristics State</th>
                <th className="p-4">Objective accuracy</th>
                <th className="p-4">Learning rate</th>
                <th className="p-4">Dropout density</th>
                <th className="p-4">Optimizer Core</th>
                <th className="p-4 font-mono">Blocks count</th>
                <th className="p-4">Running duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850/50">
              {filteredTrials.map((tr) => (
                <tr key={tr.trialNumber} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-4 font-mono font-bold text-zinc-450">trial_index_00{tr.trialNumber}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[8.5px] font-mono font-semibold uppercase ${
                      tr.state === "COMPLETE" ? "bg-green-500/10 text-green-400 border border-green-500/15" : "bg-red-500/10 text-red-400 border border-red-500/15"
                    }`}>
                      {tr.state}
                    </span>
                  </td>
                  <td className="p-4 font-mono font-bold text-teal-400">{(tr.value * 100).toFixed(2)}%</td>
                  <td className="p-4 font-mono text-zinc-350">{tr.params.learningRate}</td>
                  <td className="p-4 font-mono text-zinc-350">{tr.params.dropout}</td>
                  <td className="p-4 font-mono text-zinc-350">{tr.params.optimizer}</td>
                  <td className="p-4 font-mono text-zinc-450">{tr.params.numLayers} deep</td>
                  <td className="p-4 font-mono text-zinc-500">{tr.durationSeconds}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
