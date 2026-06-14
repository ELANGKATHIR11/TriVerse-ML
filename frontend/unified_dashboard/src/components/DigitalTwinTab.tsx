/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { 
  Play, RefreshCw, Layers, Cpu, Server, CheckCircle, AlertTriangle, Terminal, ArrowRight, HelpCircle 
} from "lucide-react";

export default function DigitalTwinTab() {
  const [activeNode, setActiveNode] = useState("Training");

  const nodes = [
    { name: "Raw Dataset", status: "Healthy", desc: "Sourcing FICO & MIMIC-IV folders", metric: "120.4k rows", icon: Layers },
    { name: "Validation", status: "Healthy", desc: "Assessing schemas & null bounds", metric: "0 duplications", icon: CheckCircle },
    { name: "Preprocessing", status: "Healthy", desc: "Z-score normalization & encoding", metric: "18 features", icon: RefreshCw },
    { name: "FE Engineering", status: "Healthy", desc: "Weight-of-Evidence indexing", metric: "4 indicators", icon: Cpu },
    { name: "Training", status: "Healthy", desc: "Backward gradient weights pathing", metric: "E-100/100 done", icon: Play },
    { name: "Evaluation", status: "Healthy", desc: "Assessing accuracy bounds on test", metric: "94.1% AUC score", icon: Server },
    { name: "Explainability", status: "Healthy", desc: "Extracting SHAP bee-swarm graphs", metric: "98% coverage", icon: HelpCircle },
    { name: "Model Registry", status: "Healthy", desc: "Registering stage candidates", metric: "v2.1.0 Ready", icon: Server },
    { name: "Inference Edge", status: "Healthy", desc: "Live endpoint pipeline triggers", metric: "14ms Latency", icon: CheckCircle },
  ];

  const pipelineLogs: { [key: string]: string[] } = {
    "Raw Dataset": [
      "[INFO 09:12] Initialized workspace loader client.",
      "[INFO 09:12] Ingesting parquet table formats for train cohorts.",
      "[OK] Portfolios validated. MD5-Signature: match."
    ],
    "Validation": [
      "[INFO 09:12] Analyzing null variables distributions.",
      "[WARN 09:12] Segment 'HomeYears' has 4.88% missing records.",
      "[OK] Schema constraints alignment check completed successfully."
    ],
    "Preprocessing": [
      "[INFO 09:12] Applying standard scalar transforms.",
      "[INFO 09:12] Imputing missing vectors using baseline median constants.",
      "[OK] Continuous and discrete columns compiled."
    ],
    "FE Engineering": [
      "[INFO 09:12] Compiling Weight of Evidence scoring bounds.",
      "[OK] Generated 4 interaction indicators. Data Quality score: 98.4%."
    ],
    "Training": [
      "[INFO 09:12] Initiating ResNet18 Backpropagation cycles.",
      "[INFO 09:13] Epoch 50/100 completed. Accuracy: 91.2% Loss: 0.16",
      "[INFO 09:15] Epoch 100/100 completed. Convergence criteria met. OK"
    ],
    "Evaluation": [
      "[INFO 09:15] Computing holdout confusion matrices.",
      "[OK] AUC score validated: 0.965. No score decay detected."
    ],
    "Explainability": [
      "[INFO 09:15] Extracting 2048 sample SHAP matrices.",
      "[OK] Calculated Gini values for revolving card weights."
    ],
    "Model Registry": [
      "[INFO 09:15] Promoting model version 'v2.1.0' to Production cluster.",
      "[OK] Registry records updated."
    ],
    "Inference Edge": [
      "[INFO 09:16] Provisioning Kubernetes pods gateway clusters.",
      "[INFO 09:16] Endpoint online: /api/v1/predict (Latency: 14.5ms)"
    ]
  };

  return (
    <div className="space-y-6">
      {/* Overview block */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5">
        <h2 className="text-xs font-semibold text-zinc-200">Interactive MLOps Pipeline Flow (Digital Twin Map)</h2>
        <p className="text-[10px] text-zinc-500">A live, end-to-end twin schematic showing training pipelines nodes status index and telemetry logs stream.</p>
      </div>

      {/* flow nodes grid maps */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-550 block mb-4 font-bold">Node execution chain</span>
        
        <div className="flex flex-wrap items-center justify-center gap-4">
          {nodes.map((nd, idx) => {
            const NodeIcon = nd.icon;
            const isSelected = activeNode === nd.name;
            return (
              <div key={nd.name} className="flex items-center gap-2">
                <button
                  onClick={() => setActiveNode(nd.name)}
                  className={`p-3.5 rounded-xl border text-left transition-all max-w-[170px] ${
                    isSelected 
                      ? "bg-teal-500/10 border-teal-500 text-teal-400 font-semibold ring-2 ring-teal-500/10" 
                      : "bg-zinc-950 border-zinc-850 hover:border-zinc-700 text-zinc-400"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <NodeIcon className={`h-4.5 w-4.5 ${isSelected ? "text-teal-400" : "text-zinc-500"}`} />
                    <span className="rounded-full bg-emerald-400/10 border border-emerald-500/15 px-1.5 py-0.5 text-[8.5px] text-emerald-400 font-mono">
                      {nd.status}
                    </span>
                  </div>
                  <h4 className="text-[11px] font-bold mt-2 font-sans truncate">{nd.name}</h4>
                  <p className="text-[9.5px] text-zinc-500 mt-0.5 leading-normal truncate">{nd.desc}</p>
                  <span className="text-[9px] font-mono text-zinc-400 mt-2 block font-semibold">{nd.metric}</span>
                </button>
                {idx < nodes.length - 1 && (
                  <ArrowRight className="hidden xl:block h-4 w-4 text-zinc-700 shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Drilldown details terminal */}
      <div className="rounded-xl border border-zinc-80) bg-zinc-900/20 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Terminal className="h-5 w-5 text-teal-400" />
          <h3 className="text-xs font-semibold text-zinc-150">Pipeline Node logs: {activeNode}</h3>
        </div>

        <div className="rounded-xl border border-zinc-808 bg-zinc-950 p-4 font-mono text-[10.5px] text-zinc-400 space-y-2 max-h-60 overflow-y-auto">
          {pipelineLogs[activeNode] ? (
            pipelineLogs[activeNode].map((logLine, lIdx) => (
              <div key={lIdx} className="leading-relaxed">
                <span className="text-zinc-600">[{lIdx + 1}]</span> {logLine}
              </div>
            ))
          ) : (
            <div>No diagnostic trace found for node.</div>
          )}
        </div>
      </div>
    </div>
  );
}
