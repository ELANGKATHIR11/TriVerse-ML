/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, Legend
} from "recharts";
import { 
  Database, CheckCircle2, ShieldAlert, Sparkles, Server, BarChart3, HelpCircle 
} from "lucide-react";

export default function DatasetAnalyticsTab() {
  const [activeSet, setActiveSet] = useState("FICO credit catalog");

  // Missing values percent data
  const missingValuesData = [
    { feature: "Income", missing: 0.12 },
    { feature: "Age", missing: 0.00 },
    { feature: "DebtRatio", missing: 0.85 },
    { feature: "Delinquency", missing: 0.00 },
    { feature: "Utilization", missing: 1.45 },
    { feature: "HomeYears", missing: 4.88 },
  ];

  // Class Imbalance Pie
  const imbalanceData = [
    { name: "Approved (Low Risk)", value: 7850, color: "#2dd4bf" },
    { name: "Declined (High Risk)", value: 2150, color: "#f43f5e" },
  ];

  // Correlation grid rows representing features
  // Features: [Income, Age, DebtRatio, Delinquencies, Utilization]
  const correlationMatrix = [
    { row: "Income", col: "Income", val: 1.0, color: "bg-teal-500" },
    { row: "Income", col: "Age", val: 0.38, color: "bg-teal-500/40" },
    { row: "Income", col: "DebtRatio", val: -0.15, color: "bg-red-500/10" },
    { row: "Income", col: "Delinq", val: -0.21, color: "bg-red-500/20" },
    { row: "Income", col: "Utili", val: -0.08, color: "bg-red-500/10" },

    { row: "Age", col: "Income", val: 0.38, color: "bg-teal-500/40" },
    { row: "Age", col: "Age", val: 1.0, color: "bg-teal-500" },
    { row: "Age", col: "DebtRatio", val: -0.04, color: "bg-zinc-900" },
    { row: "Age", col: "Delinq", val: -0.32, color: "bg-red-500/30" },
    { row: "Age", col: "Utili", val: -0.18, color: "bg-red-500/20" },

    { row: "DebtRatio", col: "Income", val: -0.15, color: "bg-red-500/10" },
    { row: "DebtRatio", col: "Age", val: -0.04, color: "bg-zinc-900" },
    { row: "DebtRatio", col: "DebtRatio", val: 1.0, color: "bg-teal-500" },
    { row: "DebtRatio", col: "Delinq", val: 0.12, color: "bg-teal-500/10" },
    { row: "DebtRatio", col: "Utili", val: 0.28, color: "bg-teal-500/30" },

    { row: "Delinq", col: "Income", val: -0.21, color: "bg-red-500/20" },
    { row: "Delinq", col: "Age", val: -0.32, color: "bg-red-500/30" },
    { row: "Delinq", col: "DebtRatio", val: 0.12, color: "bg-teal-500/10" },
    { row: "Delinq", col: "Delinq", val: 1.0, color: "bg-teal-500" },
    { row: "Delinq", col: "Utili", val: 0.44, color: "bg-teal-500/40" },

    { row: "Utili", col: "Income", val: -0.08, color: "bg-red-500/10" },
    { row: "Utili", col: "Age", val: -0.18, color: "bg-red-500/20" },
    { row: "Utili", col: "DebtRatio", val: 0.28, color: "bg-teal-500/30" },
    { row: "Utili", col: "Delinq", val: 0.44, color: "bg-teal-500/40" },
    { row: "Utili", col: "Utili", val: 1.0, color: "bg-teal-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Tab select header */}
      <div className="flex items-center justify-between border-b border-zinc-805 pb-4">
        <div>
          <h2 className="text-sm font-semibold text-zinc-200">Interactive Exploratory Data Analytics (EDA)</h2>
          <p className="text-[10px] text-zinc-500">Examine dataset profile metrics, missing values, skew indices, and parameter correlations.</p>
        </div>
        <select
          value={activeSet}
          onChange={(e) => setActiveSet(e.target.value)}
          className="text-xs bg-zinc-90 w-52 rounded-lg border border-zinc-800 p-2 text-zinc-300 focus:border-teal-500/40"
        >
          <option value="FICO credit catalog">FICO Credit Portfolio</option>
          <option value="MIMIC-IV Cohort">MIMIC-IV Clinical Cohorts</option>
          <option value="MNIST Extended">MNIST Handwritten set</option>
        </select>
      </div>

      {/* KPI Cards section */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block">Overall Quality Score</span>
          <span className="text-2xl font-bold font-mono text-teal-400 mt-1 block">99.1%</span>
          <span className="text-[10px] text-zinc-400 mt-0.5 block">0 duplicate rows detected</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block">Data Readiness Index</span>
          <span className="text-2xl font-bold font-mono text-teal-400 mt-1 block">PRODUCTION READY</span>
          <span className="text-[10px] text-zinc-400 mt-0.5 block">Holdout test split verified</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block">Features Count</span>
          <span className="text-2xl font-bold font-mono text-zinc-200 mt-1 block">18 Dimensions</span>
          <span className="text-[10px] text-zinc-400 mt-0.5 block">5 numerical, 13 categorical</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block">Total Row Records</span>
          <span className="text-2xl font-bold font-mono text-zinc-200 mt-1 block">120,400</span>
          <span className="text-[10px] text-zinc-400 mt-0.5 block">80% Training / 20% Test partition</span>
        </div>
      </div>

      {/* Specialty Visualizations: Correlation heatmap and Class imbalances */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Pearson Correlation Grid Matrix */}
        <div className="rounded-xl border border-zinc-850 bg-zinc-900/20 p-5 lg:col-span-6">
          <h3 className="text-xs font-semibold text-zinc-200 mb-3">Pearson Feature Correlation Heatmap Matrix</h3>
          <p className="text-[10px] text-zinc-500 mb-4">Positive coefficients reflect direct proportionalities; negative coefficients represent reverse shifts.</p>

          <div className="grid grid-cols-6 gap-1 font-mono text-[10px] text-center">
            {/* Headers */}
            <div className="p-2 text-zinc-650 font-semibold" />
            <div className="p-2 text-zinc-500 font-bold font-mono text-[9px] uppercase">Income</div>
            <div className="p-2 text-zinc-500 font-bold font-mono text-[9px] uppercase">Age</div>
            <div className="p-2 text-zinc-500 font-bold font-mono text-[9px] uppercase">Debt</div>
            <div className="p-2 text-zinc-500 font-bold font-mono text-[9px] uppercase">Delinq</div>
            <div className="p-2 text-zinc-500 font-bold font-mono text-[9px] uppercase">Utili</div>

            {/* Matrix Data Rendering */}
            {["Income", "Age", "DebtRatio", "Delinq", "Utili"].map((rowLabel) => {
              const cells = correlationMatrix.filter(c => c.row === rowLabel);
              return (
                <div key={rowLabel} className="contents">
                  <div className="p-2 text-zinc-400 text-left truncate font-bold font-mono text-[9px] uppercase">{rowLabel}</div>
                  {cells.map((cell, cIdx) => (
                    <div 
                      key={cIdx} 
                      className={`p-2 rounded-md font-bold text-zinc-950 flex shadow items-center justify-center ${cell.color}`}
                    >
                      {cell.val.toFixed(2)}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>

        {/* Missing values and Class imbalance */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-6 flex flex-col justify-between">
          <h3 className="text-xs font-semibold text-zinc-200 mb-4">Class Target Label Imbalances</h3>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={imbalanceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {imbalanceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800 mt-2 flex items-center justify-between text-xs text-zinc-400">
            <span>Class Skew (78.5% Approved)</span>
            <span className="font-mono text-amber-400 font-semibold text-[10px]">SMOTE Upsampling Advised</span>
          </div>
        </div>
      </div>

      {/* Segment Missing Values horizontal chart */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <h3 className="text-xs font-semibold text-zinc-200 mb-4">Null Value Index Ratio (%) per Feature Block</h3>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={missingValuesData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
              <XAxis dataKey="feature" stroke="#52525b" fontSize={10} />
              <YAxis stroke="#52525b" fontSize={10} unit="%" />
              <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "11px" }} />
              <Bar dataKey="missing" fill="#f43f5e" name="Missing %" radius={[4, 4, 0, 0]} barSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
