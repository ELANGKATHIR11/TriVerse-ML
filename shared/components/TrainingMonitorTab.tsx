/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from "react";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from "recharts";
import { 
  Monitor, Play, Square, RefreshCcw, Cpu, HardDrive, Thermometer, Activity 
} from "lucide-react";

export default function TrainingMonitorTab() {
  const [isRunning, setIsRunning] = useState(true);
  const [metrics, setMetrics] = useState({
    epoch: 12,
    batch: 145,
    totalBatches: 400,
    accuracy: 0.884,
    loss: 0.145,
    etaSeconds: 84,
    system: { cpu: 65, ram: 14.2, gpuTemp: 72, gpuMemory: 10.4 }
  });

  const [accuracyHistory, setAccuracyHistory] = useState<{ x: number; val: number }[]>([]);
  const [lossHistory, setLossHistory] = useState<{ x: number; val: number }[]>([]);

  useEffect(() => {
    let tickCount = 0;
    if (!isRunning) return;

    const pullMetrics = async () => {
      try {
        const response = await fetch("/api/metrics/realtime");
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
          
          tickCount++;
          // Append to chart history (limit to 30 markers)
          setAccuracyHistory(prev => {
            const next = [...prev, { x: tickCount, val: data.accuracy }];
            return next.slice(-25);
          });
          setLossHistory(prev => {
            const next = [...prev, { x: tickCount, val: data.loss }];
            return next.slice(-25);
          });
        }
      } catch (err) {
        console.error("Failed to gather live logs metrics:", err);
      }
    };

    pullMetrics();
    const timer = setInterval(pullMetrics, 1200);
    return () => clearInterval(timer);
  }, [isRunning]);

  const togglePipeline = () => {
    setIsRunning(!isRunning);
  };

  return (
    <div className="space-y-6">
      {/* Simulation panel headers with state click actions */}
      <div className="glass-panel p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Monitor className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-slate-200">Device Cluster Hyper-parameter Fitting telemetry</h2>
            <p className="text-[10px] text-slate-400">Live monitoring stream reflecting backpropagation loops.</p>
          </div>
        </div>

        <button
          onClick={togglePipeline}
          className={`flex items-center gap-1.5 rounded-lg border px-4 py-2 text-xs font-semibold uppercase tracking-wide transition-colors ${
            isRunning 
              ? "bg-rose-500/10 border-rose-500/20 text-rose-400 hover:bg-rose-500/20" 
              : "bg-teal-500 text-black font-bold hover:bg-teal-400 cursor-pointer animate-pulse"
          }`}
        >
          {isRunning ? (
            <>
              <Square className="h-3.5 w-3.5 fill-rose-400" />
              <span>Suspend Pipeline</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-black" />
              <span>Active Pipeline</span>
            </>
          )}
        </button>
      </div>

      {/* Structured metrics readout dials */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 text-center">
        <div className="glass-panel p-4 shadow-md">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-450 font-bold block">Current Epoch</span>
          <span className="text-2xl font-black font-mono text-white mt-1 block">E-{(metrics.epoch).toString().padStart(2, "0")} / 100</span>
        </div>
        <div className="glass-panel p-4 shadow-md">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-450 font-bold block">Epoch batch</span>
          <span className="text-2xl font-black font-mono text-white mt-1 block">{metrics.batch} / {metrics.totalBatches}</span>
        </div>
        <div className="glass-panel p-4 shadow-md">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-455 font-bold block">Valid Accuracy</span>
          <span className="text-2xl font-black font-mono text-cyan-400 mt-1 block">{(metrics.accuracy * 100).toFixed(2)}%</span>
        </div>
        <div className="glass-panel p-4 shadow-md">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-455 font-bold block">Cross-Entropy Loss</span>
          <span className="text-2xl font-black font-mono text-rose-500 mt-1 block">{metrics.loss.toFixed(4)}</span>
        </div>
        <div className="glass-panel p-4 shadow-md">
          <span className="font-mono text-[9px] uppercase tracking-wider text-slate-450 font-bold block">Estimated ETA</span>
          <span className="text-2xl font-black font-mono text-slate-300 mt-1 block">
            {Math.floor(metrics.etaSeconds / 60)}m {metrics.etaSeconds % 60}s
          </span>
        </div>
      </div>

      {/* Continuous Live charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Live Validation Accuracy Chart */}
        <div className="glass-panel p-5 shadow-lg">
          <h3 className="text-xs font-semibold text-white mb-4">Live validation accuracy curve</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={accuracyHistory} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="x" stroke="#52525b" fontSize={10} hide />
                <YAxis stroke="#52525b" fontSize={10} domain={[0.5, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "rgba(255,255,255,0.1)", fontSize: "11px" }} />
                <Line type="basis" dataKey="val" stroke="#2dd4bf" strokeWidth={2.5} dot={false} name="Accuracy" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Loss curve */}
        <div className="glass-panel p-5 shadow-lg">
          <h3 className="text-xs font-semibold text-white mb-4">Live loss optimization curve</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lossHistory} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="x" stroke="#52525b" fontSize={10} hide />
                <YAxis stroke="#52525b" fontSize={10} domain={[0, 1.2]} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "rgba(255,255,255,0.1)", fontSize: "11px" }} />
                <Line type="monotone" dataKey="val" stroke="#f43f5e" strokeWidth={2.5} dot={false} name="Loss" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Device hardware specs dashboard */}
      <div className="glass-panel p-5 shadow-lg">
        <h3 className="text-xs font-semibold text-white mb-3">Nodes hardware utilization statistics</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="border border-white/5 bg-black/15 p-4 rounded-lg flex items-center gap-3">
            <Cpu className="h-5 w-5 text-cyan-400 shrink-0" />
            <div>
              <span className="font-mono text-[9px] uppercase text-slate-450 font-bold block">CPU Load</span>
              <span className="text-sm font-black font-mono text-white">{metrics.system.cpu}%</span>
            </div>
          </div>

          <div className="border border-white/5 bg-black/15 p-4 rounded-lg flex items-center gap-3">
            <HardDrive className="h-5 w-5 text-cyan-400 shrink-0" />
            <div>
              <span className="font-mono text-[9px] uppercase text-slate-450 font-bold block">RAM Allocation</span>
              <span className="text-sm font-black font-mono text-white">{metrics.system.ram} GB</span>
            </div>
          </div>

          <div className="border border-white/5 bg-black/15 p-4 rounded-lg flex items-center gap-3">
            <Thermometer className="h-5 w-5 text-rose-500 shrink-0" />
            <div>
              <span className="font-mono text-[9px] uppercase text-slate-450 font-bold block">S-Thermal core</span>
              <span className="text-sm font-black font-mono text-white">{metrics.system.gpuTemp}°C</span>
            </div>
          </div>

          <div className="border border-white/5 bg-black/15 p-4 rounded-lg flex items-center gap-3">
            <Cpu className="h-5 w-5 text-cyan-400 shrink-0" />
            <div>
              <span className="font-mono text-[9px] uppercase text-slate-450 font-bold block">VRAM usage</span>
              <span className="text-sm font-black font-mono text-white">{metrics.system.gpuMemory} GB / 16GB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
