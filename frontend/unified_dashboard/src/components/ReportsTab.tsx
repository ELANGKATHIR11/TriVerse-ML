/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { 
  FileSpreadsheet, Download, Eye, Layers, ClipboardList, CheckSquare, Sparkles 
} from "lucide-react";

export default function ReportsTab() {
  const [selectedReportId, setSelectedReportId] = useState("rep-1");

  const reports = [
    { id: "rep-1", title: "Quarterly Credit Risk Model Performance Audit", date: "2026-06-11", type: "Security Board", author: "Alexander Vance", summary: "This audit documents accuracy margins on the FICO catalog, validating calibration indices and tree decision splits. Accuracy limits are stable at 94.1%, meeting executive guidelines." },
    { id: "rep-2", title: "Ambulatory Disease Classifier Diagnostic Review", date: "2026-06-10", type: "Clinical Review", author: "Dr. Eliza Green", summary: "A clinical validation summary of the CardioScan XGBoost biomarker models, assessing false alarm rates on holdout hospital cohorts. Retains an average Precision-Recall score of 0.884." },
    { id: "rep-3", title: "OCR Neural Network Hyperparameter Convergence summary", date: "2026-06-08", type: "Heuristics", author: "Dillon Wu", summary: "Delineates convolutional layer performance and parameters sizes for MNIST extended digits. AdamW optimizer shows 14s epoch rates compared to 62s on standard ResNets backbones." },
  ];

  const activeReport = reports.find(r => r.id === selectedReportId) || reports[0];

  const handleDownload = async (formatName: string) => {
    const format = formatName.toLowerCase();
    let taskType = "credit";
    if (selectedReportId === "rep-2") taskType = "disease";
    if (selectedReportId === "rep-3") taskType = "handwriting";
    
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    try {
      const res = await fetch("/api/reports/generate", {
        method: "POST",
        headers,
        body: JSON.stringify({
          title: activeReport.title,
          task_type: taskType,
          format: format,
          experiment_id: 1, // Default seeded ID
          recommendations: [
            "Retain current validation parameters configuration.",
            "Schedule secondary evaluation sweep with local Qwen Coder."
          ]
        })
      });
      
      if (!res.ok) {
        throw new Error("Failed to trigger report generation.");
      }
      
      const data = await res.json();
      alert(`Generating native ${formatName} report via TriVerse ML pipeline... Press OK to download.`);
      
      setTimeout(() => {
        const link = document.createElement("a");
        link.href = `/api${data.download_url}`;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }, 2500);
      
    } catch (e) {
      console.error(e);
      alert("Error generating report natively on backend.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-80) bg-zinc-900/10 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="h-5 w-5 text-teal-400" />
          <div>
            <h2 className="text-xs font-semibold text-zinc-200">Exportable Reports & System Audits</h2>
            <p className="text-[10px] text-zinc-500">Download completed model performance ledgers for medical board or finance board presentation.</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12 animate-fade-in">
        {/* Reports Directory ledgers */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-5 space-y-3">
          <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wide">Executive documents</h3>
          <div className="space-y-2.5">
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedReportId(r.id)}
                className={`w-full text-left p-3.5 rounded-lg border text-xs transition-colors flex flex-col justify-between ${
                  selectedReportId === r.id 
                    ? "bg-teal-500/10 border-teal-500/30 text-teal-450" 
                    : "bg-zinc-950 border-zinc-850 hover:bg-zinc-900 text-zinc-400"
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-bold truncate max-w-[200px]">{r.title}</span>
                  <span className="text-[9.5px] font-mono text-zinc-550 block font-bold">{r.date}</span>
                </div>
                <div className="flex items-center justify-between mt-3 text-[10px] text-zinc-500 font-mono">
                  <span>Author: {r.author}</span>
                  <span className="uppercase text-[9px] text-teal-450">{r.type}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Document Preview and Download action boards */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-5 lg:col-span-7 flex flex-col justify-between">
          <div>
            {/* Header reviews */}
            <div className="flex items-center justify-between border-b border-zinc-805 pb-3">
              <div>
                <h3 className="text-xs font-bold text-zinc-200">{activeReport.title}</h3>
                <span className="text-[10px] text-zinc-500 font-mono inline-block mt-0.5">Approved Ledger: {activeReport.id}</span>
              </div>
              <span className="rounded bg-teal-500/10 px-2 py-0.5 text-[9px] font-mono font-medium text-teal-400 uppercase">
                {activeReport.type}
              </span>
            </div>

            {/* Structured Executive abstract Summary */}
            <div className="mt-5 space-y-4">
              <span className="font-mono text-[9px] uppercase tracking-wider text-teal-400 font-bold block">Document abstract Summary</span>
              <p className="text-xs text-zinc-350 leading-relaxed bg-zinc-950/40 border border-zinc-850 rounded-xl p-4">{activeReport.summary}</p>
              
              {/* Checklist verification standards */}
              <div className="space-y-1.5 mt-2">
                <div className="flex gap-2 items-center text-xs text-zinc-400">
                  <CheckSquare className="h-4 w-4 text-teal-400 shrink-0" />
                  <span>K-Fold cross validation holdout accuracy limits verified.</span>
                </div>
                <div className="flex gap-2 items-center text-xs text-zinc-401">
                  <CheckSquare className="h-4 w-4 text-teal-500 shrink-0" />
                  <span>SHAP Global feature importance calculations checked.</span>
                </div>
                <div className="flex gap-2 items-center text-xs text-zinc-400">
                  <CheckSquare className="h-4 w-4 text-teal-450 shrink-0" />
                  <span>MFA credential audit and IP firewall logs check.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Download Buttons actions */}
          <div className="mt-6 pt-4 border-t border-zinc-800">
            <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500 font-bold block mb-3.5">Export certified asset</span>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                onClick={() => handleDownload("PDF")}
                className="py-2.5 px-3 rounded-lg bg-teal-500 hover:bg-teal-400 text-black font-bold text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Download className="h-4 w-4" />
                <span>Export PDF</span>
              </button>
              <button
                onClick={() => handleDownload("DOCX")}
                className="py-2.5 px-3 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-850 hover:text-white text-zinc-300 font-medium text-xs transition-colors flex items-center justify-center gap-2"
              >
                <Download className="h-4 w-4 text-zinc-400" />
                <span>Export DOCX</span>
              </button>
              <button
                onClick={() => handleDownload("PPTX")}
                className="py-2.5 px-3 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-850 hover:text-white text-zinc-300 font-medium text-xs transition-colors flex items-center justify-center gap-2"
              >
                <Download className="h-4 w-4 text-zinc-400" />
                <span>Export PPTX</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
