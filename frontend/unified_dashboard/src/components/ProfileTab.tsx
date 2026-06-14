/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { useAppStore } from "../state/store";
import { 
  User, CheckCircle, RefreshCw, Key, ShieldCheck, Mail, ShieldAlert 
} from "lucide-react";

export default function ProfileTab() {
  const { user, setUser } = useAppStore();
  const [name, setName] = useState(user.name);
  const [role, setRole] = useState(user.role);
  const [email, setEmail] = useState(user.email);
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setUser({
      ...user,
      name,
      role,
      email
    });
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="rounded-xl border border-zinc-80) bg-zinc-900/10 p-5">
        <h2 className="text-xs font-semibold text-zinc-200">Account Preferences & Profile Config</h2>
        <p className="text-[10px] text-zinc-500">Update identity metrics or override security keys configurations.</p>
      </div>

      <form onSubmit={handleSubmit} className="border border-zinc-800 rounded-xl bg-zinc-900/20 p-6 space-y-4">
        {success && (
          <div className="rounded-lg border border-teal-500/15 bg-teal-500/5 p-3.5 text-xs text-teal-400 font-semibold flex items-center gap-2 font-mono">
            <CheckCircle className="h-4.5 w-4.5" />
            <span>Profile metadata updated successfully locally!</span>
          </div>
        )}

        <div className="flex items-center gap-4 border-b border-zinc-850 pb-5 mb-3">
          <img
            src={user.avatarUrl}
            alt={user.name}
            className="h-14 w-14 rounded-xl object-cover ring-2 ring-teal-500/15"
          />
          <div>
            <h3 className="text-xs font-bold text-zinc-150">{user.name}</h3>
            <span className="font-mono text-[9px] text-zinc-500 block uppercase tracking-wider">{user.role}</span>
          </div>
        </div>

        <div>
          <label className="block font-mono text-[9.5px] text-zinc-500 font-bold mb-1.5 uppercase">Full Identity Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full text-xs text-zinc-200 bg-zinc-950 border border-zinc-850 rounded-lg p-2.5 focus:border-teal-500/40 outline-none font-medium"
          />
        </div>

        <div>
          <label className="block font-mono text-[9.5px] text-zinc-500 font-bold mb-1.5 uppercase">Organizational Active Role</label>
          <input
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full text-xs text-zinc-200 bg-zinc-950 border border-zinc-850 rounded-lg p-2.5 focus:border-teal-500/40 outline-none font-medium"
          />
        </div>

        <div>
          <label className="block font-mono text-[9.5px] text-zinc-500 font-bold mb-1.5 uppercase">Security Audit Email Contact</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full text-xs text-zinc-200 bg-zinc-950 border border-zinc-850 rounded-lg p-2.5 focus:border-teal-500/40 outline-none font-medium text-zinc-300"
          />
        </div>

        <button
          type="submit"
          className="py-2 px-4 rounded-lg bg-teal-555 hover:bg-teal-400 text-black font-semibold text-xs transition-colors cursor-pointer"
        >
          Save Profile Preferences
        </button>
      </form>
    </div>
  );
}
