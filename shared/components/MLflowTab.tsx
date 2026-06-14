/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { 
  GitBranch, Folder, File, ChevronRight, Play, Eye, Settings, Share2, ClipboardList
} from "lucide-react";

export default function MLflowTab() {
  const [selectedRun, setSelectedRun] = useState("run_credit_9a4");
  const [expandedArtifacts, setExpandedArtifacts] = useState<string[]>(["root", "weights"]);

  const mlflowRuns = [
    { id: "run_credit_9a4", name: "CreditGuard-ResNet18-Prod", date: "2026-06-11 04:22 UTC", status: "FINISHED", params: { lr: "0.001", optimizer: "AdamW", batch_size: "32", dropout: "0.15" }, metrics: { accuracy: "0.941", loss: "0.120", auc: "0.965" } },
    { id: "run_cardio_101", name: "CardioScan-XGBoost-L1", date: "2026-06-10 19:50 UTC", status: "FINISHED", params: { max_depth: "6", lr: "0.05", subsample: "0.85", scale_pos: "3.6" }, metrics: { accuracy: "0.898", loss: "0.160", f1: "0.884" } },
    { id: "run_mnist_2b2", name: "HandScribe-CNN-v3", date: "2026-06-10 12:05 UTC", status: "FINISHED", params: { kernel_sizes: "3,3,5", lr: "0.003", dropout: "0.2" }, metrics: { accuracy: "0.978", loss: "0.080", f1: "0.975" } },
    { id: "run_credit_bd3", name: "Credit-LogReg-Baseline", date: "2026-06-08 09:00 UTC", status: "FINISHED", params: { penalty: "l2", C: "1.0", solver: "lbfgs" }, metrics: { accuracy: "0.845", loss: "0.310", auc: "0.892" } },
  ];

  const activeRun = mlflowRuns.find(r => r.id === selectedRun) || mlflowRuns[0];

  const toggleExpand = (folder: string) => {
    setExpandedArtifacts(prev => 
      prev.includes(folder) ? prev.filter(f => f !== folder) : [...prev, folder]
    );
  };

  return (
    <div className="space-y-6">
      {/* MLflow standard UI headers */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-900/10 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <GitBranch className="h-5 w-5 text-teal-400" />
          <div>
            <h2 className="text-xs font-semibold text-zinc-200">MLflow Tracking Experiment Registry Mockup</h2>
            <p className="text-[10px] text-zinc-500">Record and inspect parameters, models weights, and validation artifacts metrics.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="font-mono text-[10px] uppercase text-zinc-400">MLflow Server: http://127.0.0.1:5000</span>
        </div>
      </div>

      {/* 2-Column setup: Left side listing runs, right side showing details */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Runs list */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-4 space-y-3">
          <h3 className="text-xs font-semibold text-zinc-200 mb-2">Experiment Runs History</h3>
          <div className="space-y-2">
            {mlflowRuns.map((rn) => (
              <button
                key={rn.id}
                onClick={() => setSelectedRun(rn.id)}
                className={`w-full text-left p-3 rounded-lg border text-xs transition-colors flex flex-col justify-between ${
                  selectedRun === rn.id 
                    ? "bg-teal-500/10 border-teal-500/30 text-teal-400" 
                    : "bg-zinc-950 border-zinc-850 hover:bg-zinc-900 text-zinc-400"
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-bold truncate max-w-[150px]">{rn.name}</span>
                  <span className="rounded bg-teal-400/10 px-1.5 py-0.5 text-[8.5px] font-mono text-teal-400 uppercase font-semibold">
                    {rn.status}
                  </span>
                </div>
                <span className="font-mono text-[9px] text-zinc-500 mt-1">{rn.date}</span>
                <span className="font-mono text-[10px] text-zinc-400 mt-2 block">Acc Score: {Object.values(rn.metrics)[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Selected parameters & Artifact tree browser */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-805 pb-3">
            <div>
              <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wide">Run Parameters: {activeRun.id}</h3>
              <p className="text-[10px] text-zinc-500">System parameters loaded during this optimization block</p>
            </div>
            <span className="text-[10.5px] font-mono font-bold text-teal-400">Run Name: {activeRun.name}</span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Parameters Table */}
            <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-950/40">
              <span className="font-mono text-[9.5px] uppercase tracking-wider text-zinc-500 font-bold block mb-3">Model Parameters</span>
              <div className="space-y-2 font-mono text-[10px] text-zinc-400">
                {Object.entries(activeRun.params).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-zinc-900 pb-1">
                    <span className="text-zinc-500 font-medium">{k}</span>
                    <span className="text-zinc-205">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metrics Mapped */}
            <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-950/40">
              <span className="font-mono text-[9.5px] uppercase tracking-wider text-zinc-500 font-bold block mb-3">Compiled Metrics</span>
              <div className="space-y-2 font-mono text-[10px] text-zinc-400">
                {Object.entries(activeRun.metrics).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-zinc-900 pb-1">
                    <span className="text-zinc-500 font-medium uppercase">{k}</span>
                    <span className="text-teal-400 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Nesting Artifact directory tree */}
          <div className="border border-zinc-805 rounded-lg p-4 bg-zinc-950/40">
            <span className="font-mono text-[9.5px] uppercase tracking-wider text-zinc-500 font-bold block mb-3">Compiled Artifact Registry Tree</span>
            
            <div className="space-y-2 text-xs font-mono text-zinc-405">
              {/* Root */}
              <div 
                onClick={() => toggleExpand("root")}
                className="flex items-center gap-2 cursor-pointer hover:text-white"
              >
                <Folder className="h-4 w-4 text-teal-400 shrink-0" />
                <span className="font-semibold text-zinc-100">artifacts/</span>
              </div>

              {expandedArtifacts.includes("root") && (
                <div className="pl-5 space-y-2.5">
                  <div className="flex items-center gap-2">
                    <File className="h-3.5 w-3.5 text-zinc-500" />
                    <span>conda.yaml</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <File className="h-3.5 w-3.5 text-zinc-500" />
                    <span>MLmodel</span>
                  </div>

                  {/* Nested Directory 2 */}
                  <div 
                    onClick={() => toggleExpand("weights")}
                    className="flex items-center gap-2 cursor-pointer hover:text-white"
                  >
                    <Folder className="h-4 w-4 text-teal-400 shrink-0" />
                    <span className="text-zinc-200">weights/</span>
                  </div>

                  {expandedArtifacts.includes("weights") && (
                    <div className="pl-5 space-y-2">
                      <div className="flex items-center gap-2 text-teal-400">
                        <File className="h-3.5 w-3.5" />
                        <span>best_estimator.pt (44.2 MB)</span>
                      </div>
                      <div className="flex items-center gap-2 text-zinc-450">
                        <File className="h-3.5 w-3.5" />
                        <span>checkpoint_epoch20.ckpt</span>
                      </div>
                    </div>
                  )}

                  {/* Directory 3 */}
                  <div className="flex items-center gap-2">
                    <Folder className="h-4 w-4 text-zinc-500 shrink-0" />
                    <span>plots/</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
