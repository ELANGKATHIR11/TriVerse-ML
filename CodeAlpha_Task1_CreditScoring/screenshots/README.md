# Credit Scoring - App Screenshots & Walkthrough

This directory contains visual captures demonstrating the capabilities of the **Credit Scoring** engine within the **TriVerse AI** platform.

## Screenshot Directory

### `01_home.png`
- **Description**: The main dashboard screen showing global system health, CPU/GPU temperature, active environment parameters, and direct navigation keys to CreditVerse, HealthVerse, and VisionVerse modules.
- **Key Elements**: Glassmorphic widgets, system utilization graph, active model counts.

### `02_dataset.png`
- **Description**: The Dataset Inspector page showing stats for the *Give Me Some Credit* and *Statlog German Credit* datasets.
- **Key Elements**: Quality scores, missing value rates (e.g. MonthlyIncome), class imbalance chart (Delinquent vs Non-Delinquent), feature correlation matrix heatmaps.

### `03_training.png`
- **Description**: The training panel showing progress curves of the 5 active models as they train on the local GPU (RTX 5060).
- **Key Elements**: Live logs, epoch progress indicators, training time, CPU/GPU power consumption curves.

### `04_results.png`
- **Description**: The model leaderboard after training completes. It ranks Logistic Regression, Decision Tree, Random Forest, CatBoost, and MLP.
- **Key Elements**: Metric tables (Accuracy, Precision, Recall, F1, ROC-AUC), parameter configurations, and "Promote to Production" status.

### `05_comparison.png`
- **Description**: High-fidelity comparative chart of the models.
- **Key Elements**: ROC-Curves comparison, Precision-Recall curves, confusion matrices, and inference latency comparison charts.

### `06_prediction.png`
- **Description**: The interactive credit scoring portal where users can fill in financial metrics (e.g. DebtRatio, age, monthly income) to assess delinquency risk.
- **Key Elements**: Input form sliders, risk percentage dial, SHAP force plot showing which attributes pushed the decision positive or negative.
