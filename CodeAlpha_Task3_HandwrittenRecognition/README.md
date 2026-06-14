# CodeAlpha Task 3: Handwritten Character Recognition (VisionVerse)

## Project Objective
Implement high-performance deep learning visual classification models to recognize handwritten characters from images. The application processes user sketches on a dynamic canvas or uploaded files, resizes and normalizes them, and runs them through either a custom Convolutional Neural Network (CNN) built in TensorFlow/Keras or a modified ResNet18 model built in PyTorch (GPU accelerated). It supports digits from the MNIST dataset and balanced character layouts from the EMNIST dataset.

## Technologies Used
- **Deep Learning**: PyTorch (ResNet18 backbone, CUDA training), TensorFlow/Keras (CNN), NumPy, Pillow.
- **HPO & MLOps**: Optuna, MLflow.
- **Backend Service**: FastAPI (Python), Uvicorn.
- **Frontend Dashboard**: React, Vite, HTML5 Canvas API, Recharts, TailwindCSS.

## Folder Structure
- `backend/`: FastAPI Python app containing PyTorch and Keras model architectures, dataset loaders, and WebSocket streaming hooks.
- `datasets/`: MNIST Digits and EMNIST Character datasets.
- `frontend/`: React code implementing the drawing scratchpad canvas, file upload modules, and real-time probability distribution indicators.
- `screenshots/`: Task execution and evaluation interface screenshots.
- `report.pdf`: Detailed Task 3 report and model convergence analysis.
- `architecture.png`: Module architectural layout schematic.

## How to Run

### 1. Backend Service
1. Navigate to the backend directory:
   ```bash
   cd CodeAlpha_Task3_HandwrittenRecognition/backend
   ```
2. Activate your conda environment (e.g. `dgpu-aiml`):
   ```bash
   conda activate dgpu-aiml
   ```
3. Run the uvicorn API:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Interface
1. Navigate to the frontend directory in a separate terminal:
   ```bash
   cd CodeAlpha_Task3_HandwrittenRecognition/frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
4. Access the handwriting drawing board at `http://localhost:3000`.
