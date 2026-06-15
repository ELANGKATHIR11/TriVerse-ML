/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  Lock, Mail, Cpu, Sparkles, AlertTriangle, RefreshCw 
} from "lucide-react";

export default function LoginTab() {
  const { login } = useAppStore();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Invalid credentials. Please verify your username and passphrase.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center frosted-glass-bg px-4">
      <div className="absolute top-0 left-0 w-full h-full bg-transparent pointer-events-none" />

      <div className="w-full max-w-md border border-white/10 bg-white/5 backdrop-blur-xl rounded-2xl p-8 shadow-2xl relative z-10 space-y-6">
        
        {/* Logo block */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-600 font-sans text-xl font-bold text-white shadow-lg shadow-cyan-500/20">
            T
          </div>
          <div>
            <h1 className="font-sans text-lg font-black tracking-wide text-white uppercase">
              TriVerse ML
            </h1>
            <p className="font-mono text-[9px] text-cyan-400 font-bold tracking-widest uppercase mt-0.5">
              Secure Experiment Workspace
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-[11px] text-rose-400">
            {error}
          </div>
        )}

        <div className="text-[10px] text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 p-2.5 rounded-lg leading-relaxed">
          <strong>Important:</strong> If the password gets rejected, please <strong>manually type</strong> <code>admin123</code>. Browsers like Edge and Brave often auto-fill incorrect saved credentials.
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-mono text-[9px] text-slate-500 font-bold mb-1 uppercase">Username</label>
            <div className="relative">
              <Mail className="absolute top-3 left-3.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full h-10 pl-10 pr-4 text-xs text-slate-200 bg-white/5 border border-white/10 rounded-lg focus:border-cyan-500/40 outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block font-mono text-[9px] text-slate-500 font-bold mb-1 uppercase">Passphrase</label>
            <div className="relative">
              <Lock className="absolute top-3 left-3.5 h-4 w-4 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full h-10 pl-10 pr-4 text-xs text-slate-200 bg-white/5 border border-white/10 rounded-lg focus:border-cyan-550/40 outline-none transition-all"
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 font-sans">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" defaultChecked className="rounded border-white/10 bg-white/5 text-cyan-500 font-bold" />
              <span>Remember active session</span>
            </label>
            <button type="button" className="hover:text-slate-200 transition-colors">Forgot passphrase?</button>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full h-10 rounded-lg bg-gradient-to-br from-cyan-400 to-indigo-600 hover:from-cyan-350 hover:to-indigo-550 text-white font-semibold text-xs transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-lg shadow-cyan-500/20"
          >
            {isSubmitting ? (
              <RefreshCw className="h-4 w-4 animate-spin text-white" />
            ) : (
              <>
                <Sparkles className="h-4 w-4 fill-white" />
                <span>Sign In Securely</span>
              </>
            )}
          </button>
        </form>

        {/* Informative advice */}
        <div className="rounded-lg bg-white/5 p-3 flex gap-2.5 items-start text-[10px] text-slate-400 leading-relaxed border border-white/10">
          <AlertCircleIcon className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
          <span>This is a local enterprise playground. Use pre-filled credentials to sign in instantly. SMS/Authenticator MFA is configured.</span>
        </div>
      </div>
    </div>
  );
}

function AlertCircleIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}
