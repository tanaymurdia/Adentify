# Adentify

A standalone desktop application that uses machine learning to detect basketball content in real-time, with smart volume control that automatically adjusts based on content detection.

## Features

- **Real-time Basketball Detection**: Identifies basketball content directly from your screen using a specialized ONNX model
- **Temporal Consensus System**: Uses a weighted voting system across multiple frames to reduce fluctuations and provide stable predictions
- **Smart Volume Control**: 
  - Automatically lowers volume when non-basketball content is detected
  - Remembers your preferred volume level for basketball content
  - Provides smooth audio fades between states
  - Adapts to user volume preferences dynamically
- **Confidence-Based Prediction**: High confidence predictions have more influence than uncertain ones
- **History Tracking**: Displays the last several classification results to show trends
- **Multiple Viewing Modes**:
  - Full application with detailed information
  - Minimal overlay mode for use while watching content
- **Scene Change Detection**: Optimizes processing by only analyzing when significant visual changes occur

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/Adentify.git
   cd Adentify
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure you have the ONNX model file in the correct location:
   ```
   models/hypernetwork_basketball_classifier.onnx
   ```

## Running Adentify

Simply run the main application file:

```
python app/basketball_classifier_app.py
```

## Usage

1. **Start Capture**: Click the "Start Capture" button to begin detecting basketball content
2. **Volume Control**: Adentify will automatically:
   - Maintain your preferred volume when basketball is detected
   - Reduce volume by 80% when non-basketball content is shown
   - Smoothly transition between these states

3. **Overlay Mode**: Click "Start Overlay" for a minimal floating display that shows just the essential information

4. **Reading the Display**:
   - The "CONSENSUS" indicator shows the stable classification across multiple frames
   - "Current Frame" shows the classification for just the latest frame
   - The history display shows recent predictions with their confidence levels
   - Trend indicators (↑, ↓, =) show if confidence is increasing, decreasing, or stable

5. **Settings**: Adjust scene sensitivity and other parameters through the Settings button

## How It Works

- The system uses a consensus algorithm that considers both:
  - Recency (newer frames matter more than older ones)
  - Confidence (high confidence predictions have more influence)
  
- The volume control system:
  - Tracks what volume level you prefer during basketball content
  - Reduces volume during non-basketball content
  - Smoothly fades between states to avoid jarring changes
  - Automatically restores your preferred level when basketball returns

- Detection uses scene change analysis to avoid redundant processing and provide responsive performance

## Requirements

- Windows operating system
- Python 3.6 or higher
- GPU support recommended but not required

## License

This project is proprietary and confidential.

## Acknowledgments

- PyQt5 for the UI framework
- ONNX Runtime for efficient model deployment
- OpenCV for image processing capabilities