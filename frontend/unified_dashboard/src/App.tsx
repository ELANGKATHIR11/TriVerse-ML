/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from "react";
import { useAppStore } from "./state/store";
import { DashboardTab } from "./types";

// Dynamic Dashboard Tabs Import
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import OverviewTab from "./components/OverviewTab";
import CreditScoringTab from "./components/CreditScoringTab";
import DiseasePredictionTab from "./components/DiseasePredictionTab";
import HandwritingTab from "./components/HandwritingTab";
import ComparisonTab from "./components/ComparisonTab";
import LeaderboardTab from "./components/LeaderboardTab";
import DatasetAnalyticsTab from "./components/DatasetAnalyticsTab";
import TrainingMonitorTab from "./components/TrainingMonitorTab";
import MLflowTab from "./components/MLflowTab";
import OptunaTab from "./components/OptunaTab";
import ModelRegistryTab from "./components/ModelRegistryTab";
import ReportsTab from "./components/ReportsTab";
import AIAssistantTab from "./components/AIAssistantTab";
import DigitalTwinTab from "./components/DigitalTwinTab";
import SecurityTab from "./components/SecurityTab";
import ProfileTab from "./components/ProfileTab";
import LoginTab from "./components/LoginTab";

export default function App() {
  const { isAuthenticated, activeTab, fetchData } = useAppStore();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated, fetchData]);

  // Unauthenticated users routed directly to Login Form
  if (!isAuthenticated) {
    return <LoginTab />;
  }

  // Choose sub-dashboard tab to display
  const renderActiveTabContent = () => {
    switch (activeTab) {
      case DashboardTab.OVERVIEW:
        return <OverviewTab />;
      case DashboardTab.CREDIT_SCORING:
        return <CreditScoringTab />;
      case DashboardTab.DISEASE_PREDICTION:
        return <DiseasePredictionTab />;
      case DashboardTab.HANDWRITING:
        return <HandwritingTab />;
      case DashboardTab.COMPARISON:
        return <ComparisonTab />;
      case DashboardTab.LEADERBOARD:
        return <LeaderboardTab />;
      case DashboardTab.DATASET_ANALYTICS:
        return <DatasetAnalyticsTab />;
      case DashboardTab.TRAINING_MONITOR:
        return <TrainingMonitorTab />;
      case DashboardTab.MLFLOW:
        return <MLflowTab />;
      case DashboardTab.OPTUNA:
        return <OptunaTab />;
      case DashboardTab.MODEL_REGISTRY:
        return <ModelRegistryTab />;
      case DashboardTab.REPORTS:
        return <ReportsTab />;
      case DashboardTab.AI_ASSISTANT:
        return <AIAssistantTab />;
      case DashboardTab.DIGITAL_TWIN:
        return <DigitalTwinTab />;
      case DashboardTab.SECURITY:
        return <SecurityTab />;
      case DashboardTab.PROFILE:
        return <ProfileTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="flex min-h-screen w-full frosted-glass-bg font-sans text-slate-105 antialiased selection:bg-white/20 selection:text-white relative overflow-hidden">
      {/* Liquid fluid animated blobs behind the client container */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="liquid-blob liquid-blob-1" />
        <div className="liquid-blob liquid-blob-2" />
        <div className="liquid-blob liquid-blob-3" />
      </div>

      {/* Navigation menu drawer drawer layout */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Mobile responsive backdrop blur click-away indicator drawer */}
      {isSidebarOpen && (
        <div 
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm pointer-events-auto md:hidden"
        />
      )}

      {/* Main viewport */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Header onMenuClick={() => setIsSidebarOpen(true)} />

        <main id="main-content-scroll" className="flex-1 overflow-y-auto px-6 py-6 md:px-8 space-y-6">
          <div className="mx-auto max-w-7xl w-full">
            {renderActiveTabContent()}
          </div>
        </main>
      </div>
    </div>
  );
}
