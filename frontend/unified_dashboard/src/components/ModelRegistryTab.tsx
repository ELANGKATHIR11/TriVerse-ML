/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  Cpu, ArrowUpRight, ShieldCheck, History, Laptop, ShieldAlert, CloudLightning 
} from "lucide-react";

export default function ModelRegistryTab() {
  const { models, promoteModel, registryModels } = useAppStore();
  const [selectedModelId, setSelectedModelId] = useState("m-001");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const selectedModel = models.find(m => m.id === selectedModelId) || models[0] || {
    id: "",
    name: "No Models Registered",
    version: "v0.0.0",
    status: "None",
    modelSizeMb: 0,
    memoryMb: 0,
    inferenceTimeMs: 0,
    explainabilityScore: 0,
    accuracy: 0,
    precision: 0,
    f1Score: 0,
  };

  const handlePromoteStage = (id: string, stage: "Production" | "Staging" | "Archived") => {
    // Fire our Zustand reducer to mutate actual registry models
    promoteModel(id, stage);
    triggerLocalToast(`Model promoted to state: ${stage} successfully.`);
  };

  const triggerLocalToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Toast alert box */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 rounded-xl bg-zinc-950 border border-teal-500/30 p-4 shadow-2xl flex items-center gap-3 animate-fade-in-up">
          <div className="h-2 w-2 rounded-full bg-teal-400 animate-ping" />
          <span className="text-xs font-semibold text-zinc-100">{toastMessage}</span>
        </div>
      )}

      {/* Registry Title Headers */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Cpu className="h-5 w-5 text-teal-400" />
          <div>
            <h2 className="text-xs font-semibold text-zinc-200">Model Deployment Registry</h2>
            <p className="text-[10px] text-zinc-500">Record, promote, or rollback neural backbones across production endpoints.</p>
          </div>
        </div>
        <span className="rounded bg-teal-500/10 px-2.5 py-1 text-[10px] font-mono text-teal-400 border border-teal-500/20 uppercase font-semibold">
          Kubernetes: Connected
        </span>
      </div>

      {/* Side-by-side: left listing active registered items, right showing deployment logs */}
      <div className="grid gap-6 lg:grid-cols-12 animate-fade-in">
        {/* Model index */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-5 space-y-4">
          <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wide">Registered backbones</h3>
          <div className="space-y-2.5">
            {models.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelectedModelId(m.id)}
                className={`w-full text-left p-3.5 rounded-lg border text-xs transition-all flex flex-col justify-between ${
                  selectedModelId === m.id 
                    ? "bg-teal-500/10 border-teal-500/30 text-teal-450" 
                    : "bg-zinc-950 border-zinc-850 hover:bg-zinc-900 text-zinc-400"
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-bold truncate max-w-[200px]">{m.name}</span>
                  <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">{m.version}</span>
                </div>
                <div className="flex items-center justify-between w-full mt-3 font-mono text-[10px] text-zinc-400">
                  <span>Acc Score: {(m.accuracy * 100).toFixed(1)}%</span>
                  <span className="font-semibold text-teal-450">{m.status}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Deployment console and version managers */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-805 pb-3">
            <div>
              <h3 className="text-xs font-semibold text-zinc-150 font-sans">Active Configuration: {selectedModel.name}</h3>
              <p className="text-[10px] text-zinc-500 mt-0.5">Stage promotions audit</p>
            </div>
            <span className="rounded bg-teal-500/5 px-2.5 py-1 text-[9px] font-mono text-teal-400 font-bold border border-teal-500/10 uppercase">
              {selectedModel.status}
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="border border-zinc-800 rounded-lg p-3.5 bg-zinc-950/45 font-mono text-[10px] text-zinc-400">
              <span className="text-zinc-500 text-[9.5px] uppercase block mb-2 font-bold font-mono">Performance profile</span>
              <div className="space-y-1.5">
                <div>Model Type: XGBoost/ResNet</div>
                <div>Size on Disk: {selectedModel.modelSizeMb}MB</div>
                <div>Memory Requirement: {selectedModel.memoryMb}MB</div>
                <div>Latency Benchmark: {selectedModel.inferenceTimeMs}ms</div>
              </div>
            </div>

            <div className="border border-zinc-800 rounded-lg p-3.5 bg-zinc-950/45 font-mono text-[10px] text-zinc-400">
              <span className="text-zinc-500 text-[9.5px] uppercase block mb-2 font-bold font-mono">Telemetry signature</span>
              <div className="space-y-1.5">
                <div>Explainability: {selectedModel.explainabilityScore}/100</div>
                <div>Accuracy Bounds: {selectedModel.accuracy}</div>
                <div>Precision Bounds: {selectedModel.precision}</div>
                <div>F1 Stability index: {selectedModel.f1Score}</div>
              </div>
            </div>
          </div>

          {/* Target promotion inputs */}
          <div className="space-y-3 pt-3 border-t border-zinc-805">
            <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block">Promote or Rollback model deployment stage</span>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                onClick={() => handlePromoteStage(selectedModel.id, "Production")}
                className="py-2 px-3 rounded-lg bg-teal-550 hover:bg-teal-400 text-black font-bold text-[11px] transition-colors cursor-pointer text-center"
              >
                Promote to Production
              </button>
              <button
                onClick={() => handlePromoteStage(selectedModel.id, "Staging")}
                className="py-2 px-3 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-850 hover:text-white text-zinc-300 font-medium text-[11px] transition-colors text-center"
              >
                Promote to Staging
              </button>
              <button
                onClick={() => handlePromoteStage(selectedModel.id, "Archived")}
                className="py-2 px-3 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-red-950/20 hover:text-red-400 text-zinc-400 font-medium text-[11px] transition-colors text-center"
              >
                Retire Model (Archive)
              </button>
            </div>
          </div>

          {/* deployment activity logs */}
          <div className="p-4 rounded-xl border border-zinc-850 bg-zinc-900/30">
            <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-400 font-bold block mb-3">Deployment Log Stream (Kubernetes)</span>
            <div className="space-y-2.5 font-mono text-[10px] text-zinc-500 leading-normal">
              <div className="flex gap-2">
                <span className="text-zinc-600">[08:12:44]</span>
                <span className="text-zinc-400">Verified sha256 checksum mapping... OK</span>
              </div>
              <div className="flex gap-2">
                <span className="text-zinc-600">[08:12:45]</span>
                <span className="text-zinc-450">Routing gateway endpoint to version:</span>
                <span className="text-teal-400 font-bold">{selectedModel.version}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-zinc-600">[08:12:48]</span>
                <span className="text-zinc-400">Deploying cluster replicas on Node-G10X... READY</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
