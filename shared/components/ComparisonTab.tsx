/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAppStore } from "../state/store";
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from "recharts";
import { 
  Layers, CheckCheck, HelpCircle, HardDrive, Cpu, Sliders 
} from "lucide-react";

export default function ComparisonTab() {
  const { models, selectedCompareIds, toggleCompareModel } = useAppStore();

  // Find models matching chosen ids
  const compareModels = models.filter((m) => selectedCompareIds.includes(m.id));

  // Construct radar dimensions
  const radarData = [
    { subject: "Accuracy", A: 94, B: 92, C: 97, D: 89 },
    { subject: "F1 Score", A: 93, B: 92, C: 97, D: 88 },
    { subject: "Inference Speed", A: 85, B: 99, C: 90, D: 98 },
    { subject: "Footprint Size", A: 75, B: 88, C: 82, D: 95 },
    { subject: "Explainability", A: 78, B: 86, C: 42, D: 94 },
  ];

  // Dynamic mapped radar
  const dynamicRadarData = [
    { subject: "Accuracy" },
    { subject: "F1 Score" },
    { subject: "Inference Speed (norm)" },
    { subject: "Footprint Size (norm)" },
    { subject: "Explainability" },
  ].map((dim, idx) => {
    const row: any = { subject: dim.subject };
    compareModels.forEach((m, mIdx) => {
      let val = 50;
      if (idx === 0) val = m.accuracy * 100;
      else if (idx === 1) val = m.f1Score * 100;
      else if (idx === 2) val = Math.max(10, Math.min(100, (50 / m.inferenceTimeMs) * 100)); // Normalize
      else if (idx === 3) val = Math.max(10, Math.min(100, (30 / m.modelSizeMb) * 100)); // Normalize
      else if (idx === 4) val = m.explainabilityScore;
      row[`model_${mIdx}`] = parseFloat(val.toFixed(1));
    });
    return row;
  });

  const barColors = ["#2dd4bf", "#3b82f6", "#f59e0b", "#ec4899"];

  return (
    <div className="space-y-6">
      {/* Selection drawer matrix */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <h3 className="text-xs font-semibold text-zinc-200 mb-3">Checkbox Multi-Selector for Comparative Benchmarks</h3>
        <p className="text-[11px] text-zinc-500 mb-4">Select two or more candidate configurations from the local registry to compile overlays.</p>
        
        <div className="flex flex-wrap gap-3">
          {models.map((m) => {
            const isChecked = selectedCompareIds.includes(m.id);
            return (
              <button
                key={m.id}
                onClick={() => toggleCompareModel(m.id)}
                className={`flex items-center gap-2.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
                  isChecked 
                    ? "bg-teal-500/10 border-teal-500/30 text-teal-400" 
                    : "bg-zinc-950/45 border-zinc-850 hover:border-zinc-700 text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <div className={`flex h-4 w-4 items-center justify-center rounded-md border ${
                  isChecked ? "bg-teal-500 border-teal-500 text-black" : "border-zinc-700"
                }`}>
                  {isChecked && <CheckCheck className="h-3 w-3" />}
                </div>
                <span>{m.name}</span>
                <span className="font-mono text-[9px] text-zinc-500 uppercase">{m.version}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid details */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Radar Map Overlays chart */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-5">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Hexagonal Attribute Radar</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={dynamicRadarData}>
                <PolarGrid stroke="#27272a" />
                <PolarAngleAxis dataKey="subject" stroke="#71717a" fontSize={10} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#27272a" fontSize={8} />
                {compareModels.map((m, idx) => (
                  <Radar
                    key={m.id}
                    name={m.name}
                    dataKey={`model_${idx}`}
                    stroke={barColors[idx % barColors.length]}
                    fill={barColors[idx % barColors.length]}
                    fillOpacity={0.15}
                  />
                ))}
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Inference metrics charts */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-7">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Latency (Inference Ms) vs Footprint Size (Mb)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compareModels} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="name" stroke="#52525b" fontSize={9} />
                <YAxis stroke="#52525b" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                <Bar dataKey="inferenceTimeMs" fill="#2dd4bf" radius={[4, 4, 0, 0]} name="Inference Speed (Ms)" barSize={20} />
                <Bar dataKey="modelSizeMb" fill="#3b82f6" radius={[4, 4, 0, 0]} name="File Size (Mb)" barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Numerical Benchmark Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <h3 className="text-xs font-semibold text-zinc-200 mb-3">Candidate Side-by-Side Parameter Matrix</h3>
        <div className="overflow-x-auto rounded-lg border border-zinc-800/60 bg-zinc-950/40">
          <table className="w-full text-left font-sans text-xs">
            <thead className="bg-zinc-900/60 font-mono text-[10px] uppercase text-zinc-500 font-bold border-b border-zinc-800">
              <tr>
                <th className="p-4">Evaluating Target</th>
                <th className="p-4">Accuracy</th>
                <th className="p-4">Precision</th>
                <th className="p-4">Recall</th>
                <th className="p-4">F1 Score</th>
                <th className="p-4">ROC-AUC</th>
                <th className="p-4">Inference Ms</th>
                <th className="p-4">Explainability</th>
                <th className="p-4">Active Stage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {compareModels.map((m) => (
                <tr key={m.id} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-4 font-bold text-zinc-100">{m.name}</td>
                  <td className="p-4 font-mono text-zinc-300">{(m.accuracy * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-zinc-300">{(m.precision * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-zinc-300">{(m.recall * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-zinc-300">{(m.f1Score * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-teal-400 font-semibold">{m.auc.toFixed(3)}</td>
                  <td className="p-4 font-mono text-zinc-450">{m.inferenceTimeMs}ms</td>
                  <td className="p-4 font-mono text-zinc-300">{m.explainabilityScore}/100</td>
                  <td className="p-4">
                    <span className="rounded bg-teal-500/10 px-2.5 py-0.5 text-[9px] font-mono font-medium text-teal-400 border border-teal-500/15 uppercase tracking-wide">
                      {m.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
