# Adentify

A real-time basketball content detection application.

## Project Overview

Adentify is an intelligent desktop application that uses deep learning to automatically identify basketball content in real-time through screen capture and analysis.

## Features

- **Real-time Screen Analysis**: Captures and analyzes screen content in real-time
- **Intelligent Scene Detection**: Optimizes processing by detecting meaningful frame changes
- **Modern Cyberpunk UI**: Black and red-themed interface with performance metrics
- **GPU Acceleration**: Utilizes CUDA for faster inference when available
- **Adjustable Sensitivity**: Control how aggressively the model processes frames

## Installation

### Requirements

- Windows OS
- Python 3.7+
- Required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Ensure the ONNX model is in the correct location:
   `models/hypernetwork_basketball_classifier.onnx`

2. Run the application:
   ```bash
   cd app
   python basketball_classifier_app.py
   ```

3. After the model loads, click "Start Capture" to begin analyzing your screen
4. Adjust the scene sensitivity slider to control detection threshold
5. The application will highlight when basketball content is detected

## Architecture

- **PyQt5-based UI**: Modern interface with real-time metrics
- **ONNX Runtime**: Efficient model execution with GPU support when available
- **Intelligent Frame Processing**: Scene change detection to optimize performance

## License

This project is proprietary and confidential.

## Acknowledgments

- PyQt5 for the UI framework
- ONNX Runtime for efficient model deployment
- OpenCV for image processing capabilities