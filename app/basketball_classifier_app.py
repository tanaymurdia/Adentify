#!/usr/bin/env python
"""
Basketball Classifier Windows Application
This standalone app uses the ONNX-converted model to classify images directly,
eliminating the need for client-server architecture.
"""
import os
import sys
import time
import threading
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageGrab
import cv2
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QPen
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, 
                           QPushButton, QProgressBar, QSlider)

# Import styling
from style import STYLE, RED_COLOR, LIGHT_TEXT_COLOR, DARK_BG_COLOR

# Import fluid animation
from fluid_animation import FluidAnimation

# Import settings dialog
from settings import SettingsDialog

# Constants
MODEL_PATH = os.path.abspath("models/hypernetwork_basketball_classifier.onnx")
TARGET_SIZE = 224
CAPTURE_INTERVAL = 500  # ms
SCENE_THRESHOLD = 30.0  # threshold for scene change detection
FPS_UPDATE_INTERVAL = 1000  # ms

class BasketballClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Basketball Classifier")
        self.setMinimumSize(900, 600)
        self.model = None
        self.running = False
        self.last_frame = None
        self.prev_frame = None
        self.fps_count = 0
        self.fps = 0
        self.last_fps_update = time.time()
        self.scene_change_threshold = SCENE_THRESHOLD
        
        # Center the window
        self.center_on_screen()
        
        # Set up UI
        self.init_ui()
        
        # Start loading model in a separate thread
        self.load_model_thread = threading.Thread(target=self.load_model)
        self.load_model_thread.daemon = True
        self.load_model_thread.start()
        
        # Apply style
        self.setStyleSheet(STYLE)

    def center_on_screen(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def init_ui(self):
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Set background color for the central widget
        self.central_widget.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        
        # Loading screen
        self.loading_widget = QWidget()
        self.loading_widget.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        loading_layout = QVBoxLayout(self.loading_widget)
        
        self.loading_label = QLabel("Loading Basketball Classifier Model...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFont(QFont("Consolas", 12))
        
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # Indeterminate progress
        
        loading_layout.addStretch()
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.loading_progress)
        loading_layout.addStretch()
        
        # Main screen
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        self.main_widget.hide()  # Hide until loading is complete
        content_layout = QVBoxLayout(self.main_widget)
        
        # Video display
        self.video_frame = QLabel()
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setMinimumHeight(350)
        self.video_frame.setContentsMargins(0, 0, 0, 10)  # Add bottom margin
        
        # Fluid animation widget
        self.fluid_animation = FluidAnimation(self.main_widget)
        self.fluid_animation.setMinimumHeight(350)
        self.fluid_animation.setContentsMargins(0, 0, 0, 10)  # Add bottom margin
        self.fluid_animation.hide()  # Initially hidden
        
        # Status and controls area
        controls_layout = QHBoxLayout()
        
        # Left side - model status
        status_layout = QVBoxLayout()
        self.model_status_label = QLabel("Model Status: Ready")
        self.model_status_label.setFont(QFont("Consolas", 9))
        self.model_status_label.setMinimumWidth(450)  # Increased to ensure full text visibility
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setFont(QFont("Consolas", 9))
        
        self.prediction_label = QLabel("Prediction: N/A")
        self.prediction_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.prediction_label.setMinimumWidth(450)  # Increased width for full text display
        
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setFont(QFont("Consolas", 10))
        self.confidence_label.setMinimumWidth(450)  # Added minimum width for consistency
        
        status_layout.addWidget(self.model_status_label)
        status_layout.addWidget(self.fps_label)
        status_layout.addWidget(self.prediction_label)
        status_layout.addWidget(self.confidence_label)
        status_layout.addStretch()
        
        # Right side - controls
        buttons_layout = QVBoxLayout()
        
        # Start/Stop capture button
        self.start_button = QPushButton("Start Capture")
        self.start_button.clicked.connect(self.toggle_capture)
        self.start_button.setEnabled(False)  # Disabled until model is loaded
        self.start_button.setFixedWidth(220)  # Increased from 180 to 220 to fit text
        self.start_button.setFixedHeight(36)  # Set fixed height for consistent button size
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setFixedWidth(220)  # Same width as start button
        self.settings_button.setFixedHeight(36)  # Same height as start button
        
        # Add widgets to buttons layout with right alignment
        button_container = QHBoxLayout()
        button_container.addStretch()  # Push button to the right
        button_container.addWidget(self.start_button)
        buttons_layout.addLayout(button_container)
        
        # Add settings button with the same alignment
        settings_container = QHBoxLayout()
        settings_container.addStretch()  # Push button to the right
        settings_container.addWidget(self.settings_button)
        buttons_layout.addLayout(settings_container)
        
        buttons_layout.addStretch()
        
        # Combine status and controls
        controls_layout.addLayout(status_layout)
        controls_layout.addLayout(buttons_layout)
        
        # Add all components to main layout
        content_layout.addWidget(self.video_frame)
        content_layout.addWidget(self.fluid_animation)
        
        # Add spacing between video/animation and controls
        content_layout.addSpacing(20)  # Add 20px spacing
        
        content_layout.addLayout(controls_layout)
        
        # Add both screens to main layout
        self.main_layout.addWidget(self.loading_widget)
        self.main_layout.addWidget(self.main_widget)
        
        # Setup timer for captures
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)

    def load_model(self):
        try:
            # Simulate longer loading for UX purposes
            time.sleep(1.5)
            
            # Initialize ONNX Runtime session
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Try to use GPU if available
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            self.model = ort.InferenceSession(MODEL_PATH, sess_options, providers=providers)
            
            # Get model input name
            self.input_name = self.model.get_inputs()[0].name
            
            # Update UI in main thread
            QtCore.QMetaObject.invokeMethod(
                self, "model_loaded", Qt.QueuedConnection,
                QtCore.Q_ARG(bool, True),
                QtCore.Q_ARG(str, "GPU" if 'CUDAExecutionProvider' in self.model.get_providers() else "CPU")
            )
        except Exception as e:
            # Update UI to show error
            QtCore.QMetaObject.invokeMethod(
                self, "model_loaded", Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False),
                QtCore.Q_ARG(str, str(e))
            )

    @QtCore.pyqtSlot(bool, str)
    def model_loaded(self, success, message):
        # Hide loading screen
        self.loading_widget.hide()
        self.main_widget.show()
        
        if success:
            self.start_button.setEnabled(True)
            self.model_status_label.setText(f"Model Status: Loaded ({message})")
            
            # Show fluid animation on startup
            self.video_frame.hide()
            self.fluid_animation.show()
            self.fluid_animation.start_animation()
        else:
            self.model_status_label.setText(f"Model Error: {message}")
            self.prediction_label.setText("Prediction: Error")
            self.prediction_label.setStyleSheet(f"color: {RED_COLOR};")

    def toggle_capture(self):
        if not self.running:
            # Start capture
            self.running = True
            self.start_button.setText("Stop Capture")
            
            # Reset frame detection state
            self.last_frame = None
            self.prev_frame = None
            
            # Hide fluid animation and show video frame
            self.fluid_animation.stop_animation()
            self.fluid_animation.hide()
            self.video_frame.show()
            
            # Force an immediate frame capture and classification
            self.immediate_process_frame()
            
            # Then start the regular timer
            self.timer.start(CAPTURE_INTERVAL)
        else:
            # Stop capture
            self.running = False
            self.start_button.setText("Start Capture")
            self.timer.stop()
            
            # Switch to fluid animation
            self.video_frame.hide()
            self.fluid_animation.show()
            self.fluid_animation.start_animation()
            
            # Reset prediction info
            self.prediction_label.setText("Prediction: N/A")
            self.prediction_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 10pt; font-weight: bold;")
            self.confidence_label.setText("Confidence: 0%")
            self.model_status_label.setText("Model Status: Idle")

    def immediate_process_frame(self):
        """Process a frame immediately without waiting for the timer"""
        try:
            # Capture screen
            screen = ImageGrab.grab()
            
            # Convert to numpy array
            frame = np.array(screen)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Resize for display while preserving aspect ratio
            h, w, _ = frame.shape
            ratio = min(780 / w, 380 / h)
            display_frame = cv2.resize(frame, (int(w * ratio), int(h * ratio)))
            
            # Initialize frame detection state
            self.last_frame = display_frame.copy()
            self.prev_frame = display_frame.copy()
            
            # Prepare for display
            display_img = QImage(display_frame.data, display_frame.shape[1], display_frame.shape[0], 
                              display_frame.strides[0], QImage.Format_RGB888).rgbSwapped()
            
            # Add info overlay with processing indicator
            pixmap = QPixmap.fromImage(display_img)
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(255, 62, 62), 3))  # Always use processing indicator for immediate frame
            painter.drawRect(5, 5, pixmap.width() - 10, pixmap.height() - 10)
            painter.end()
            
            self.video_frame.setPixmap(pixmap)
            
            # Always run inference on the immediate frame
            if self.model is not None:
                # Run in the current thread for immediate feedback
                self.run_inference(frame)
            
        except Exception as e:
            import traceback
            print(f"Error in immediate frame capture: {e}")
            print(traceback.format_exc())

    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self, self.scene_change_threshold, self.fps)
        if dialog.exec_():
            # If user clicked Apply
            self.scene_change_threshold = dialog.get_threshold()
            print(f"Scene sensitivity updated to: {self.scene_change_threshold}")

    def process_frame(self):
        try:
            # Capture screen
            screen = ImageGrab.grab()
            
            # Convert to numpy array
            frame = np.array(screen)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Resize for display while preserving aspect ratio
            h, w, _ = frame.shape
            ratio = min(780 / w, 380 / h)
            display_frame = cv2.resize(frame, (int(w * ratio), int(h * ratio)))
            
            # Store for scene detection
            if self.last_frame is None:
                self.last_frame = display_frame
                self.prev_frame = display_frame
                should_process = True
                print("Initial frame captured")
            else:
                # Scene change detection based on frame difference
                self.prev_frame = self.last_frame
                self.last_frame = display_frame
                
                # Calculate frame difference
                frame_diff = cv2.absdiff(self.prev_frame, self.last_frame)
                frame_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
                frame_change = np.mean(frame_diff)
                
                # Only process if significant change is detected
                should_process = frame_change > self.scene_change_threshold
                
                if should_process:
                    print(f"Scene change detected: {frame_change:.2f} > {self.scene_change_threshold}")
            
            # Update FPS counter
            self.fps_count += 1
            current_time = time.time()
            time_diff = current_time - self.last_fps_update
            
            if time_diff >= FPS_UPDATE_INTERVAL / 1000:
                self.fps = int(self.fps_count / time_diff)
                self.fps_label.setText(f"FPS: {self.fps}")
                self.fps_count = 0
                self.last_fps_update = current_time
            
            # Prepare for display
            display_img = QImage(display_frame.data, display_frame.shape[1], display_frame.shape[0], 
                              display_frame.strides[0], QImage.Format_RGB888).rgbSwapped()
            
            # Add info overlay
            pixmap = QPixmap.fromImage(display_img)
            painter = QPainter(pixmap)
            
            # Draw scene change indicator
            if should_process:
                painter.setPen(QPen(QColor(255, 62, 62), 3))
            else:
                painter.setPen(QPen(QColor(100, 100, 100), 3))
            
            painter.drawRect(5, 5, pixmap.width() - 10, pixmap.height() - 10)
            painter.end()
            
            self.video_frame.setPixmap(pixmap)
            
            # Only run inference if scene changed significantly
            if should_process and self.model is not None:
                print("Running inference on new frame")
                threading.Thread(target=self.run_inference, args=(frame,)).start()

        except Exception as e:
            import traceback
            print(f"Error capturing screen: {e}")
            print(traceback.format_exc())

    def run_inference(self, frame):
        try:
            # Convert to RGB and resize for model
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (TARGET_SIZE, TARGET_SIZE))
            
            # Convert to float32 numpy array
            img_array = np.array(img).astype(np.float32)
            
            # Add batch dimension
            img_batch = np.expand_dims(img_array, axis=0)
            
            # Run inference
            start_time = time.time()
            results = self.model.run(None, {self.input_name: img_batch})[0]
            inference_time = time.time() - start_time
            
            # Get prediction and confidence
            pred_value = float(results[0][0])
            is_basketball = pred_value > 0.5
            
            print(f"Inference result: {'Basketball' if is_basketball else 'Not Basketball'} ({pred_value:.4f})")
            
            # Update UI in main thread
            QtCore.QMetaObject.invokeMethod(
                self, "update_prediction", Qt.QueuedConnection,
                QtCore.Q_ARG(bool, is_basketball),
                QtCore.Q_ARG(float, pred_value),
                QtCore.Q_ARG(float, inference_time)
            )
            
        except Exception as e:
            import traceback
            print(f"Error in inference: {e}")
            print(traceback.format_exc())

    @QtCore.pyqtSlot(bool, float, float)
    def update_prediction(self, is_basketball, confidence, inference_time):
        # Update prediction labels
        prediction_text = "BASKETBALL" if is_basketball else "NOT BASKETBALL"
        self.prediction_label.setText(f"Prediction: {prediction_text}")
        
        # Set color based on prediction
        if is_basketball:
            self.prediction_label.setStyleSheet(f"color: {RED_COLOR}; font-size: 10pt; font-weight: bold;")
        else:
            self.prediction_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 10pt; font-weight: bold;")
        
        # Update confidence
        confidence_pct = confidence * 100 if is_basketball else (1 - confidence) * 100
        self.confidence_label.setText(f"Confidence: {confidence_pct:.2f}%")
        
        # Update model status with inference time
        self.model_status_label.setText(f"Model Status: Inference in {inference_time*1000:.1f}ms")


def main():
    app = QApplication(sys.argv)
    window = BasketballClassifierApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 