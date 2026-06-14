/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export enum DashboardTab {
  OVERVIEW = "overview",
  CREDIT_SCORING = "credit_scoring",
  DISEASE_PREDICTION = "disease_prediction",
  HANDWRITING = "handwriting_recognition",
  COMPARISON = "comparison",
  LEADERBOARD = "leaderboard",
  DATASET_ANALYTICS = "dataset_analytics",
  TRAINING_MONITOR = "training_monitor",
  MLFLOW = "mlflow",
  OPTUNA = "optuna",
  MODEL_REGISTRY = "model_registry",
  REPORTS = "reports",
  AI_ASSISTANT = "ai_assistant",
  DIGITAL_TWIN = "digital_twin",
  SECURITY = "security",
  PROFILE = "profile"
}

export interface User {
  name: string;
  email: string;
  role: string;
  avatarUrl?: string;
  joinedDate: string;
  mfaEnabled: boolean;
  apiKey: string;
}

export interface Experiment {
  id: string;
  name: string;
  status: "Completed" | "Running" | "Failed" | "Queued";
  metricValue: number; // Accuracy or F1
  loss: number;
  modelType: string;
  dataset: string;
  durationSeconds: number;
  createdAt: string;
}

export interface ModelMetadata {
  id: string;
  name: string;
  version: string;
  task: string;
  accuracy: number;
  f1Score: number;
  precision: number;
  recall: number;
  auc: number;
  inferenceTimeMs: number;
  modelSizeMb: number;
  memoryMb: number;
  explainabilityScore: number; // 0-100
  status: "Staging" | "Production" | "Archived" | "Candidate";
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  shapValue: number;
}

export interface PatientRecord {
  age: number;
  gender: "Male" | "Female";
  cholesterol: number;
  bloodPressure: number;
  heartRate: number;
  bloodSugar: number;
  smoker: "Yes" | "No";
  familyHistory: "Yes" | "No";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: string[];
}

export interface OptunaTrial {
  trialNumber: number;
  state: "COMPLETE" | "PRUNED" | "RUNNING";
  value: number; // Objective value
  params: {
    learningRate: number;
    numLayers: number;
    optimizer: string;
    dropout: number;
    batchSize: number;
  };
  durationSeconds: number;
}

export interface RegistryModel {
  name: string;
  currentVersion: string;
  stage: "Production" | "Staging" | "Archived" | "None";
  lastUpdated: string;
  author: string;
  runs: string[];
}

export interface SecurityLog {
  id: string;
  userId: string;
  action: string;
  ipAddress: string;
  location: string;
  userAgent: string;
  timestamp: string;
  status: "Success" | "Failed" | "Warning";
}
