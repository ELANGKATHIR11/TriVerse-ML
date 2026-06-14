/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAppStore } from "../state/store";
import { 
  ShieldCheck, ShieldAlert, History, Key, CheckSquare, Laptop 
} from "lucide-react";

export default function SecurityTab() {
  const { securityLogs } = useAppStore();

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-80) bg-zinc-900/10 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-teal-400" />
          <div>
            <h2 className="text-xs font-semibold text-zinc-200">Security Parameters & Event Audit Ledger</h2>
            <p className="text-[10px] text-zinc-500 font-medium">Coordinate credentials, configure API tokens, and trace suspicious container network access anomalies.</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* API keys token display */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Key className="h-4.5 w-4.5 text-teal-400" />
            <h3 className="text-xs font-semibold text-zinc-150">Active platform API keys</h3>
          </div>
          <p className="text-[10px] text-zinc-500 leading-normal">Allows secure model deployment query access from outer containers.</p>
          
          <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-900 font-mono text-[10.5px] text-zinc-400 truncate">
            ca_live_9bce7382ad74f391afee294cf
          </div>
        </div>

        {/* Identity compliance metrics */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4.5 w-4.5 text-teal-505" />
            <h3 className="text-xs font-semibold text-zinc-150">Multi-Factor Compliance</h3>
          </div>
          <p className="text-[10px] text-zinc-500 leading-normal">MFA status of the active administrator node session.</p>
          
          <div className="flex items-center gap-2.5 rounded-lg border border-emerald-500/10 bg-emerald-500/5 px-3 py-2 text-xs text-green-400 font-semibold font-mono">
            <CheckSquare className="h-4.5 w-4.5" />
            <span>MFA SECURELY ENABLED (SMS + App)</span>
          </div>
        </div>

        {/* Device logs */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/10 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Laptop className="h-4.5 w-4.5 text-teal-400" />
            <h3 className="text-xs font-semibold text-zinc-150">Firewall IP blocking logs</h3>
          </div>
          <div className="font-mono text-[10px] text-zinc-400 space-y-2">
            <div className="flex justify-between">
              <span>Blocked IP (Frankfurt)</span>
              <span className="text-rose-400 font-bold">Blocked</span>
            </div>
            <div className="flex justify-between">
              <span>MFA Token drift limit</span>
              <span className="text-emerald-400">Match OK</span>
            </div>
          </div>
        </div>
      </div>

      {/* Structured Security event list table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5">
        <h3 className="text-xs font-semibold text-zinc-200 mb-3.5">Security Compliance Activity Ledger</h3>
        
        <div className="overflow-x-auto rounded-lg border border-zinc-808 bg-zinc-950/40">
          <table className="w-full text-left font-sans text-xs">
            <thead className="bg-zinc-900/60 font-mono text-[9.5px] uppercase text-zinc-500 font-bold border-b border-zinc-800">
              <tr>
                <th className="p-4">Reference Log</th>
                <th className="p-4">Core Event Action</th>
                <th className="p-4">IP Address</th>
                <th className="p-4">Geographic Location</th>
                <th className="p-4 font-mono">Client Host Browser</th>
                <th className="p-4">Log Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850/50 text-zinc-400">
              {securityLogs.map((log) => (
                <tr key={log.id} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="p-4 font-mono">{log.id}</td>
                  <td className="p-4 text-zinc-250 font-medium">{log.action}</td>
                  <td className="p-4 font-mono text-[11px] text-zinc-500">{log.ipAddress}</td>
                  <td className="p-4 text-zinc-350">{log.location}</td>
                  <td className="p-4 font-mono text-[10.5px] text-zinc-500 truncate max-w-[150px]">{log.userAgent}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[8.5px] font-mono font-bold uppercase ${
                      log.status === "Success" ? "bg-green-500/10 text-green-400" : 
                      log.status === "Warning" ? "bg-amber-500/10 text-amber-500" : "bg-red-500/10 text-red-500"
                    }`}>
                      {log.status === "Warning" && <ShieldAlert className="h-3 w-3 shrink-0" />}
                      {log.status}
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
