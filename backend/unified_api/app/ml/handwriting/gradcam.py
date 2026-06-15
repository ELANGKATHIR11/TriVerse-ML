"""
backend/unified_api/app/ml/handwriting/gradcam.py

Grad-CAM generator for handwriting models (both TensorFlow/Keras and PyTorch).
Returns a base64 encoded PNG of the original image overlaid with the Grad-CAM heatmap.
"""

from __future__ import annotations
import base64
from io import BytesIO
import numpy as np
import cv2
import matplotlib.pyplot as plt
import torch
import tensorflow as tf

def generate_gradcam_heatmap(model, img_array: np.ndarray, model_name: str, target_class: int | None = None) -> tuple[str, int]:
    """
    Generates Grad-CAM heatmap and returns base64 PNG string.
    img_array: 28x28 numpy array in range [0, 1].
    """
    model_name_lower = model_name.lower()
    
    if model_name_lower == "cnn":
        # Keras model
        # Input shape: (1, 28, 28, 1)
        X = np.expand_dims(img_array, axis=(0, -1))
        heatmap, pred_class = _keras_gradcam(model, X, target_class)
    elif model_name_lower in ("efficientnet", "efficientnet-b0", "efficientnetb0"):
        # PyTorch model
        # Input shape: (1, 1, 28, 28)
        X = np.expand_dims(img_array, axis=(0, 0))
        tensor = torch.tensor(X, dtype=torch.float32)
        heatmap, pred_class = _pytorch_gradcam(model, tensor, target_class)
    else:
        # ResNet18 (PyTorch model)
        # Input shape: (1, 3, 28, 28)
        X = np.expand_dims(img_array, axis=(0, -1))
        from app.ml.handwriting.resnet_model import ResNet18Trainer
        tensor = ResNet18Trainer._to_3channel_tensor(X)
        heatmap, pred_class = _pytorch_gradcam(model, tensor, target_class)
        
    # Overlay heatmap on original image
    overlaid_b64 = _overlay_heatmap(img_array, heatmap)
    return overlaid_b64, pred_class

def _keras_gradcam(model, X: np.ndarray, target_class: int | None = None) -> tuple[np.ndarray, int]:
    # Find last conv layer
    target_layer = None
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            target_layer = layer
            break
            
    if target_layer is None:
        raise ValueError("No Conv2D layer found in Keras model.")
        
    grad_model = tf.keras.models.Model(
        [model.inputs], [target_layer.output, model.output]
    )
    
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(X)
        if target_class is None:
            target_class = int(tf.argmax(predictions[0]))
        loss = predictions[:, target_class]
        
    grads = tape.gradient(loss, conv_outputs)
    guided_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ guided_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    heatmap = tf.maximum(heatmap, 0)
    max_val = tf.math.reduce_max(heatmap)
    if max_val > 0:
        heatmap = heatmap / max_val
        
    return heatmap.numpy(), target_class

def _pytorch_gradcam(model, tensor_input: torch.Tensor, target_class: int | None = None) -> tuple[np.ndarray, int]:
    # Find last conv layer
    target_layer = None
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            target_layer = module
            
    if target_layer is None:
        raise ValueError("No Conv2d layer found in PyTorch model.")
        
    device = next(model.parameters()).device
    tensor_input = tensor_input.to(device)
    
    gradients: list[torch.Tensor] = []
    activations: list[torch.Tensor] = []
    
    def forward_hook(module, input, output):
        activations.append(output)
        
    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])
        
    h1 = target_layer.register_forward_hook(forward_hook)
    h2 = target_layer.register_full_backward_hook(backward_hook)
    
    model.zero_grad()
    logits = model(tensor_input)
    
    if target_class is None:
        target_class = int(torch.argmax(logits, dim=1).item())
        
    loss = logits[0, target_class]
    loss.backward()
    
    h1.remove()
    h2.remove()
    
    grads = gradients[0].cpu().data.numpy()[0]
    acts = activations[0].cpu().data.numpy()[0]
    
    weights = np.mean(grads, axis=(1, 2))
    
    heatmap = np.zeros(acts.shape[1:], dtype=np.float32)
    for i, w in enumerate(weights):
        heatmap += w * acts[i]
        
    heatmap = np.maximum(heatmap, 0)
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
        
    return heatmap, target_class

def _overlay_heatmap(img_array: np.ndarray, heatmap: np.ndarray) -> str:
    # Resize heatmap to 28x28
    heatmap_resized = cv2.resize(heatmap, (28, 28))
    
    # Scale to uint8 [0, 255]
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    
    # Apply Jet colormap
    colormap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    
    # Convert gray original image to BGR
    img_uint8 = np.uint8(255 * img_array)
    img_bgr = cv2.cvtColor(img_uint8, cv2.COLOR_GRAY2BGR)
    
    # Blend colormap and original image
    overlaid = cv2.addWeighted(img_bgr, 0.6, colormap, 0.4, 0)
    
    # Encode as base64 PNG
    _, buffer = cv2.imencode('.png', overlaid)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return b64_str
