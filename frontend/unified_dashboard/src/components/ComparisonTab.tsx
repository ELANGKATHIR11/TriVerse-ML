/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from "recharts";
import { 
  CheckCheck, Cpu, Sliders, HardDrive, Layers, Activity, Sparkles
} from "lucide-react";

export default function ComparisonTab() {
  const { models, selectedCompareIds, toggleCompareModel } = useAppStore();
  const [selectedTaskFilter, setSelectedTaskFilter] = useState<string>("All");

  const tasks = ["All", "Credit Scoring", "Disease Prediction", "Handwriting Recognition"];

  // Grouped list of models for selection matrix
  const creditModels = models.filter(m => m.task === "Credit Scoring");
  const diseaseModels = models.filter(m => m.task === "Disease Prediction");
  const visionModels = models.filter(m => m.task === "Handwriting Recognition");

  // Models currently selected for comparison
  const compareModels = models.filter((m) => selectedCompareIds.includes(m.id))
    .filter(m => selectedTaskFilter === "All" || m.task === selectedTaskFilter);

  // Dynamic mapped radar for performance dimensions
  const dynamicRadarData = [
    { subject: "Accuracy" },
    { subject: "F1 Score" },
    { subject: "Precision" },
    { subject: "Recall" },
    { subject: "Inference Speed (norm)" },
    { subject: "Footprint Size (norm)" },
    { subject: "Explainability" },
  ].map((dim, idx) => {
    const row: any = { subject: dim.subject };
    compareModels.forEach((m, mIdx) => {
      let val = 50;
      if (idx === 0) val = m.accuracy * 100;
      else if (idx === 1) val = m.f1Score * 100;
      else if (idx === 2) val = m.precision * 100;
      else if (idx === 3) val = m.recall * 100;
      else if (idx === 4) val = Math.max(10, Math.min(100, (20 / (m.inferenceTimeMs + 0.1)) * 100)); // Normalize speed
      else if (idx === 5) val = Math.max(10, Math.min(100, (50 / (m.modelSizeMb + 0.1)) * 100)); // Normalize size
      else if (idx === 6) val = m.explainabilityScore;
      row[`model_${m.id}`] = parseFloat(val.toFixed(1));
    });
    return row;
  });

  const barColors = [
    "#2dd4bf", // teal
    "#3b82f6", // blue
    "#ec4899", // pink
    "#f59e0b", // amber
    "#10b981", // emerald
    "#8b5cf6", // violet
    "#ef4444", // red
    "#14b8a6", // secondary teal
  ];

  const renderModelButton = (m: any) => {
    const isChecked = selectedCompareIds.includes(m.id);
    return (
      <button
        key={m.id}
        onClick={() => toggleCompareModel(m.id)}
        className={`flex items-center gap-2.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
          isChecked 
            ? "bg-teal-500/10 border-teal-500/40 text-teal-400 shadow-md shadow-teal-950/20" 
            : "bg-zinc-950/45 border-zinc-850 hover:border-zinc-750 text-zinc-400 hover:text-zinc-200"
        }`}
      >
        <div className={`flex h-4 w-4 items-center justify-center rounded-md border ${
          isChecked ? "bg-teal-500 border-teal-500 text-black animate-pulse" : "border-zinc-700"
        }`}>
          {isChecked && <CheckCheck className="h-3 w-3" />}
        </div>
        <div className="text-left">
          <div className="font-semibold">{m.name}</div>
          <div className="font-mono text-[9px] text-zinc-500 uppercase">{m.version}</div>
        </div>
      </button>
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Category selector */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
            <Sliders className="h-5 w-5 text-teal-400" />
            Comparative Benchmark Suite
          </h2>
          <p className="text-xs text-zinc-400">Select any candidate model configuration from our local registry to view real-time overlay analyses.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {tasks.map((tsk) => (
            <button
              key={tsk}
              onClick={() => setSelectedTaskFilter(tsk)}
              className={`rounded px-3 py-1.5 text-xs font-medium border transition-all ${
                selectedTaskFilter === tsk 
                  ? "bg-gradient-to-r from-teal-550 to-emerald-500 text-black border-transparent font-semibold shadow-md shadow-teal-950/10" 
                  : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700"
              }`}
            >
              {tsk}
            </button>
          ))}
        </div>
      </div>

      {/* Checklist matrices categorized */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Section A: Credit Scoring */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wide flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
              Section A: Credit Scoring
            </h3>
            <span className="text-[10px] font-mono text-zinc-500">GMSC Dataset</span>
          </div>
          <div className="flex flex-col gap-2 max-h-[200px] overflow-y-auto pr-1">
            {creditModels.map(renderModelButton)}
            {creditModels.length === 0 && <span className="text-[11px] text-zinc-650 italic">No models registered</span>}
          </div>
        </div>

        {/* Section B: Disease Prediction */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wide flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
              Section B: Disease Predict
            </h3>
            <span className="text-[10px] font-mono text-zinc-500">Heart Disease Dataset</span>
          </div>
          <div className="flex flex-col gap-2 max-h-[200px] overflow-y-auto pr-1">
            {diseaseModels.map(renderModelButton)}
            {diseaseModels.length === 0 && <span className="text-[11px] text-zinc-650 italic">No models registered</span>}
          </div>
        </div>

        {/* Section C: Vision Recognition */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wide flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-pink-400" />
              Section C: Handwriting / Vision
            </h3>
            <span className="text-[10px] font-mono text-zinc-500">MNIST Digits Dataset</span>
          </div>
          <div className="flex flex-col gap-2 max-h-[200px] overflow-y-auto pr-1">
            {visionModels.map(renderModelButton)}
            {visionModels.length === 0 && <span className="text-[11px] text-zinc-650 italic">No models registered</span>}
          </div>
        </div>
      </div>

      {compareModels.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-8 text-center">
          <Sparkles className="h-8 w-8 text-zinc-650 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-zinc-400">No models matching active selection</h4>
          <p className="text-[11px] text-zinc-550 max-w-sm mx-auto mt-1">Please select one or more candidate models from the sections above to compile performance overlays.</p>
        </div>
      ) : (
        <>
          {/* Comparison charts visual grid */}
          <div className="grid gap-6 lg:grid-cols-12">
            {/* Hexagonal radar overlays */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-5 flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                  <Activity className="h-4 w-4 text-teal-400" />
                  Multidimensional Radar Benchmark
                </h3>
                <p className="text-[10px] text-zinc-500 mt-0.5">Normalized performance metrics compared side-by-side.</p>
              </div>
              <div className="h-72 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={dynamicRadarData}>
                    <PolarGrid stroke="#27272a" />
                    <PolarAngleAxis dataKey="subject" stroke="#a1a1aa" fontSize={9} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#27272a" fontSize={7} />
                    {compareModels.map((m, idx) => (
                      <Radar
                        key={m.id}
                        name={m.name}
                        dataKey={`model_${m.id}`}
                        stroke={barColors[idx % barColors.length]}
                        fill={barColors[idx % barColors.length]}
                        fillOpacity={0.12}
                      />
                    ))}
                    <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px", borderRadius: "8px" }} />
                    <Legend iconSize={7} iconType="circle" wrapperStyle={{ fontSize: "10px", marginTop: "10px" }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Latency vs size bar chart */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-7 flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                  <HardDrive className="h-4 w-4 text-blue-400" />
                  Latency vs. Disk Space footprint
                </h3>
                <p className="text-[10px] text-zinc-500 mt-0.5">Inference response time (milliseconds) and model file size (megabytes).</p>
              </div>
              <div className="h-72 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={compareModels} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis dataKey="name" stroke="#71717a" fontSize={9} tickLine={false} />
                    <YAxis stroke="#71717a" fontSize={9} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px", borderRadius: "8px" }} />
                    <Legend iconSize={7} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                    <Bar dataKey="inferenceTimeMs" fill="#2dd4bf" radius={[4, 4, 0, 0]} name="Inference Speed (Ms)" barSize={18} />
                    <Bar dataKey="modelSizeMb" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Model Size (Mb)" barSize={18} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Side by side stats grid */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
            <h3 className="text-xs font-semibold text-zinc-200 mb-3 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-emerald-400" />
              Parameter Benchmark Matrix
            </h3>
            <div className="overflow-x-auto rounded-lg border border-zinc-805 bg-zinc-950/40">
              <table className="w-full text-left font-sans text-xs">
                <thead className="bg-zinc-900/60 font-mono text-[9px] uppercase tracking-wider text-zinc-550 border-b border-zinc-800">
                  <tr>
                    <th className="p-4">Candidate Model Name</th>
                    <th className="p-4">Evaluating Task</th>
                    <th className="p-4 text-center">Accuracy</th>
                    <th className="p-4 text-center">Precision</th>
                    <th className="p-4 text-center">Recall</th>
                    <th className="p-4 text-center">F1 Score</th>
                    <th className="p-4 text-center">ROC-AUC</th>
                    <th className="p-4 text-center">Inference Latency</th>
                    <th className="p-4 text-center">Memory VRAM</th>
                    <th className="p-4 text-center">Explainability Gini</th>
                    <th className="p-4 text-center">Deployment State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40">
                  {compareModels.map((m, idx) => (
                    <tr key={m.id} className="hover:bg-zinc-900/20 transition-colors">
                      <td className="p-4 font-bold text-zinc-250 flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: barColors[idx % barColors.length] }} />
                        {m.name}
                      </td>
                      <td className="p-4 text-zinc-500 font-medium">{m.task}</td>
                      <td className="p-4 text-center font-mono text-teal-400 font-semibold">{(m.accuracy * 100).toFixed(2)}%</td>
                      <td className="p-4 text-center font-mono text-zinc-400">{(m.precision * 100).toFixed(1)}%</td>
                      <td className="p-4 text-center font-mono text-zinc-400">{(m.recall * 100).toFixed(1)}%</td>
                      <td className="p-4 text-center font-mono text-zinc-400">{(m.f1Score * 100).toFixed(1)}%</td>
                      <td className="p-4 text-center font-mono text-teal-500 font-semibold">{m.auc.toFixed(3)}</td>
                      <td className="p-4 text-center font-mono text-zinc-450">{m.inferenceTimeMs} ms</td>
                      <td className="p-4 text-center font-mono text-zinc-500">{m.memoryMb} MB</td>
                      <td className="p-4 text-center font-mono text-amber-500 font-semibold">{m.explainabilityScore}/100</td>
                      <td className="p-4 text-center">
                        <span className="rounded bg-teal-500/10 px-2 py-0.5 text-[9px] font-mono text-teal-400 font-medium border border-teal-500/15 uppercase">
                          {m.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
