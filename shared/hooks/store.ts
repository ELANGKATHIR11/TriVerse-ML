/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { create } from "zustand";
import { DashboardTab, User, Experiment, ModelMetadata, OptunaTrial, RegistryModel, SecurityLog } from "../types";

interface AppState {
  // Navigation & Auth
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  isAuthenticated: boolean;
  setIsAuthenticated: (auth: boolean) => void;
  user: User;
  setUser: (user: User) => void;

  // Search filter
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  // Experiment Datasets
  experiments: Experiment[];
  addExperiment: (exp: Experiment) => void;
  
  // Model comparison selector
  selectedCompareIds: string[];
  toggleCompareModel: (id: string) => void;
  clearComparison: () => void;

  // ML models list
  models: ModelMetadata[];
  promoteModel: (id: string, stage: "Production" | "Staging" | "Archived") => void;

  // Optuna trials list
  optunaTrials: OptunaTrial[];
  bestTrialValue: number;

  // Registry Models list
  registryModels: RegistryModel[];
  
  // Chat History
  chatMessages: { [tabId: string]: any[] };
  addChatMessage: (tabId: string, role: "user" | "assistant", content: string, sim?: boolean) => void;

  // Security Audit log
  securityLogs: SecurityLog[];
  addSecurityLog: (log: SecurityLog) => void;
}

const mockUser: User = {
  name: "Alexander Vance",
  email: "elangkathir11@gmail.com",
  role: "Principal AI Platform Architect",
  avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=200",
  joinedDate: "2025-01-20",
  mfaEnabled: true,
  apiKey: "ca_live_9bce7382ad74f391afee294cf"
};

const mockExperiments: Experiment[] = [
  { id: "exp-001", name: "Credit-Score-ResNet", status: "Completed", metricValue: 0.941, loss: 0.12, modelType: "ResNet18", dataset: "FICO credit catalog", durationSeconds: 4320, createdAt: "2026-06-11T04:22:00Z" },
  { id: "exp-002", name: "Disease-XGBoost-L1", status: "Completed", metricValue: 0.898, loss: 0.16, modelType: "XGBoost", dataset: "MIMIC-IV Cohort", durationSeconds: 880, createdAt: "2026-06-10T19:50:00Z" },
  { id: "exp-003", name: "Drawing-CNN-AdamW", status: "Completed", metricValue: 0.978, loss: 0.08, modelType: "Custom CNN", dataset: "MNIST Extended", durationSeconds: 1540, createdAt: "2026-06-10T12:05:00Z" },
  { id: "exp-004", name: "Optuna-Autotune-LGBM", status: "Completed", metricValue: 0.925, loss: 0.14, modelType: "LightGBM", dataset: "FICO credit catalog", durationSeconds: 14500, createdAt: "2026-06-09T17:11:00Z" },
  { id: "exp-005", name: "Disease-DenseNet-v2", status: "Running", metricValue: 0.812, loss: 0.28, modelType: "DenseNet", dataset: "MIMIC-IV Cohort", durationSeconds: 3120, createdAt: "2026-06-11T08:12:00Z" },
  { id: "exp-006", name: "Credit-LogReg-Baseline", status: "Completed", metricValue: 0.845, loss: 0.31, modelType: "Logistic Regression", dataset: "FICO credit catalog", durationSeconds: 210, createdAt: "2026-06-08T09:00:00Z" },
  { id: "exp-007", name: "MNIST-ResNet18-Baseline", status: "Failed", metricValue: 0.450, loss: 1.82, modelType: "ResNet18", dataset: "MNIST Extended", durationSeconds: 830, createdAt: "2026-06-07T14:32:00Z" }
];

const mockModels: ModelMetadata[] = [
  { id: "m-001", name: "CreditGuard-ResNet18", version: "v2.1.0", task: "Credit Scoring", accuracy: 0.941, f1Score: 0.932, precision: 0.928, recall: 0.936, auc: 0.965, inferenceTimeMs: 14.5, modelSizeMb: 44.8, memoryMb: 120, explainabilityScore: 78, status: "Production" },
  { id: "m-002", name: "CardioScan-XGBoost", version: "v1.4.2", task: "Disease Prediction", accuracy: 0.898, f1Score: 0.884, precision: 0.891, recall: 0.877, auc: 0.921, inferenceTimeMs: 1.2, modelSizeMb: 12.4, memoryMb: 35, explainabilityScore: 94, status: "Production" },
  { id: "m-003", name: "HandScribe-CNN", version: "v3.0.1", task: "Handwriting Recognition", accuracy: 0.978, f1Score: 0.975, precision: 0.972, recall: 0.978, auc: 0.991, inferenceTimeMs: 8.4, modelSizeMb: 24.1, memoryMb: 85, explainabilityScore: 42, status: "Production" },
  { id: "m-004", name: "Credit-LightGBM-Optuna", version: "v1.0.0-rc1", task: "Credit Scoring", accuracy: 0.925, f1Score: 0.921, precision: 0.915, recall: 0.927, auc: 0.952, inferenceTimeMs: 2.1, modelSizeMb: 18.2, memoryMb: 45, explainabilityScore: 86, status: "Staging" }
];

const mockOptunaTrials: OptunaTrial[] = [
  { trialNumber: 1, state: "COMPLETE", value: 0.812, params: { learningRate: 0.05, numLayers: 2, optimizer: "SGD", dropout: 0.1, batchSize: 64 }, durationSeconds: 15 },
  { trialNumber: 2, state: "COMPLETE", value: 0.845, params: { learningRate: 0.01, numLayers: 3, optimizer: "Adam", dropout: 0.2, batchSize: 32 }, durationSeconds: 28 },
  { trialNumber: 3, state: "PRUNED", value: 0.720, params: { learningRate: 0.1, numLayers: 4, optimizer: "SGD", dropout: 0.4, batchSize: 128 }, durationSeconds: 12 },
  { trialNumber: 4, state: "COMPLETE", value: 0.892, params: { learningRate: 0.003, numLayers: 4, optimizer: "Adam", dropout: 0.2, batchSize: 32 }, durationSeconds: 42 },
  { trialNumber: 5, state: "COMPLETE", value: 0.914, params: { learningRate: 0.001, numLayers: 5, optimizer: "AdamW", dropout: 0.1, batchSize: 32 }, durationSeconds: 58 },
  { trialNumber: 6, state: "COMPLETE", value: 0.938, params: { learningRate: 0.0007, numLayers: 5, optimizer: "AdamW", dropout: 0.15, batchSize: 64 }, durationSeconds: 74 },
  { trialNumber: 7, state: "COMPLETE", value: 0.921, params: { learningRate: 0.0005, numLayers: 6, optimizer: "AdamW", dropout: 0.25, batchSize: 64 }, durationSeconds: 90 },
];

const mockRegistryModels: RegistryModel[] = [
  { name: "CreditGuard-ResNet18", currentVersion: "v2.1.0", stage: "Production", lastUpdated: "2026-06-11T04:22:00Z", author: "Alexander Vance", runs: ["run_credit_9a4", "run_credit_bd3"] },
  { name: "CardioScan-XGBoost", currentVersion: "v1.4.2", stage: "Production", lastUpdated: "2026-06-10T19:50:00Z", author: "Eliza Green", runs: ["run_cardio_101"] },
  { name: "HandScribe-CNN", currentVersion: "v3.0.1", stage: "Production", lastUpdated: "2026-06-10T12:05:00Z", author: "Dillon Wu", runs: ["run_mnist_2b2", "run_mnist_2f9"] },
  { name: "Disease-DenseNet", currentVersion: "v1.0.0-rc2", stage: "Staging", lastUpdated: "2026-06-11T08:12:00Z", author: "Alexander Vance", runs: ["run_densenet_005"] }
];

const mockSecurityLogs: SecurityLog[] = [
  { id: "log-1", userId: "usr-avance", action: "API Token generated", ipAddress: "192.168.1.144", location: "San Francisco, US", userAgent: "Mozilla/5.0 Chrome/131.0", timestamp: "2026-06-11T08:44:00Z", status: "Success" },
  { id: "log-2", userId: "usr-avance", action: "User Sign In", ipAddress: "192.168.1.144", location: "San Francisco, US", userAgent: "Mozilla/5.0 Chrome/131.0", timestamp: "2026-06-11T08:12:00Z", status: "Success" },
  { id: "log-3", userId: "usr-avance", action: "Model Promoted (CreditGuard-ResNet18 v2.1.0 → Production)", ipAddress: "192.168.1.144", location: "San Francisco, US", userAgent: "Mozilla/5.0 Chrome/131.0", timestamp: "2026-06-11T04:30:00Z", status: "Success" },
  { id: "log-4", userId: "usr-avance", action: "Unauthorized SSH Access Attempt", ipAddress: "85.204.116.14", location: "Frankfurt, DE", userAgent: "SSH-2.0-Go", timestamp: "2026-06-10T22:15:00Z", status: "Warning" },
  { id: "log-5", userId: "usr-egreen", action: "Model Version Deleted (CardioScan v1.4.1)", ipAddress: "172.56.21.90", location: "London, UK", userAgent: "Mozilla/5.0 Safari/17", timestamp: "2026-06-10T18:02:00Z", status: "Success" }
];

export const useAppStore = create<AppState>((set) => ({
  activeTab: DashboardTab.OVERVIEW,
  setActiveTab: (tab) => set({ activeTab: tab }),
  isAuthenticated: true, // Login page defaults to completed, but user can log out
  setIsAuthenticated: (auth) => set({ isAuthenticated: auth }),
  user: mockUser,
  setUser: (user) => set({ user }),

  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),

  experiments: mockExperiments,
  addExperiment: (exp) => set((state) => ({ experiments: [exp, ...state.experiments] })),

  selectedCompareIds: ["m-001", "m-004"],
  toggleCompareModel: (id) => set((state) => {
    const ids = [...state.selectedCompareIds];
    const index = ids.indexOf(id);
    if (index >= 0) {
      // Don't go below 1 choice
      if (ids.length <= 1) return state;
      ids.splice(index, 1);
    } else {
      ids.push(id);
    }
    return { selectedCompareIds: ids };
  }),
  clearComparison: () => set({ selectedCompareIds: [] }),

  models: mockModels,
  promoteModel: (id, stage) => set((state) => {
    const updatedModels = state.models.map(m => m.id === id ? { ...m, status: stage } : m);
    // Find model that was promoted for registry update
    const modelItem = state.models.find(m => m.id === id);
    let updatedRegistry = [...state.registryModels];
    if (modelItem) {
      updatedRegistry = state.registryModels.map(rm => 
        rm.name === modelItem.name ? { ...rm, stage: stage, lastUpdated: new Date().toISOString() } : rm
      );
    }
    return { models: updatedModels, registryModels: updatedRegistry };
  }),

  optunaTrials: mockOptunaTrials,
  bestTrialValue: 0.938,

  registryModels: mockRegistryModels,

  chatMessages: {
    global: [
      { id: "msg-1", role: "assistant", content: "Hello! I am your CodeAlpha AI Copilot. How can I help you benchmark models, inspect feature importance, or troubleshoot loss curves today?", timestamp: "2026-06-11T09:12:00Z" }
    ]
  },
  addChatMessage: (tabId, role, content) => set((state) => {
    const list = state.chatMessages[tabId] || [];
    const newMessage = {
      id: "msg-" + Math.random().toString(36).substring(2, 9),
      role,
      content,
      timestamp: new Date().toISOString()
    };
    return {
      chatMessages: {
        ...state.chatMessages,
        [tabId]: [...list, newMessage]
      }
    };
  }),

  securityLogs: mockSecurityLogs,
  addSecurityLog: (log) => set((state) => ({ securityLogs: [log, ...state.securityLogs] }))
}));
