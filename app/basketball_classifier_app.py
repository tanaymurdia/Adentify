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
                           QPushButton, QProgressBar, QSlider, QCheckBox)

# Import styling
from style import STYLE, RED_COLOR, LIGHT_TEXT_COLOR, DARK_BG_COLOR

# Import fluid animation
from fluid_animation import FluidAnimation

# Import settings dialog
from settings import SettingsDialog

# Import overlay
from overlay import ClassifierOverlay

# Import volume controller
from functionality import VolumeController

# Constants
MODEL_PATH = os.path.abspath("models/hypernetwork_basketball_classifier.onnx")
TARGET_SIZE = 224
CAPTURE_INTERVAL = 500  # ms
SCENE_THRESHOLD = 30.0  # threshold for scene change detection
FPS_UPDATE_INTERVAL = 1000  # ms
HISTORY_SIZE = 4  # Number of predictions to keep in history
MIN_CONSENSUS_CONFIDENCE = 65.0  # Minimum confidence level for strong consensus

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
        self.overlay_mode = False
        
        # Volume control setup
        self.volume_controller = VolumeController()
        self.volume_control_enabled = True
        
        # Prediction history tracking
        self.prediction_history = []  # List of (is_basketball, confidence) tuples
        self.history_labels = []  # List of QLabel widgets for history display
        self.consensus_prediction = None  # The stable consensus prediction
        self.consensus_confidence = 0.0  # Confidence in the consensus
        
        # Create overlay
        self.overlay = ClassifierOverlay()
        self.overlay.exitOverlay.connect(self.exit_overlay_mode)
        self.overlay.toggle_button.clicked.connect(self.overlay_toggle_capture)
        
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
        
        # Consensus prediction (stable output from multiple frames)
        self.consensus_label = QLabel("CONSENSUS: N/A")
        self.consensus_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.consensus_label.setMinimumWidth(450)
        
        # Current frame prediction
        self.prediction_label = QLabel("Current Frame: N/A")
        self.prediction_label.setFont(QFont("Consolas", 10))
        self.prediction_label.setMinimumWidth(450)  # Increased width for full text display
        
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setFont(QFont("Consolas", 10))
        self.confidence_label.setMinimumWidth(450)  # Added minimum width for consistency
        
        # Volume status
        self.volume_label = QLabel("Volume control: Active")
        self.volume_label.setFont(QFont("Consolas", 9))
        
        # Volume control toggle
        self.volume_checkbox = QCheckBox("Enable volume control")
        self.volume_checkbox.setChecked(True)
        self.volume_checkbox.toggled.connect(self.toggle_volume_control)
        
        # Prediction history section
        history_title = QLabel("Recent Predictions:")
        history_title.setFont(QFont("Consolas", 9, QFont.Bold))
        
        status_layout.addWidget(self.model_status_label)
        status_layout.addWidget(self.fps_label)
        status_layout.addWidget(self.consensus_label)
        status_layout.addWidget(self.prediction_label)
        status_layout.addWidget(self.confidence_label)
        status_layout.addWidget(self.volume_label)
        status_layout.addWidget(self.volume_checkbox)
        status_layout.addWidget(history_title)
        
        # Add history labels
        history_layout = QHBoxLayout()
        for i in range(HISTORY_SIZE):
            label = QLabel(f"{i+1}: N/A")
            label.setFont(QFont("Consolas", 9))
            label.setMinimumWidth(100)
            self.history_labels.append(label)
            history_layout.addWidget(label)
        
        history_layout.addStretch()
        status_layout.addLayout(history_layout)
        status_layout.addStretch()
        
        # Right side - controls
        buttons_layout = QVBoxLayout()
        
        # Start/Stop capture button
        self.start_button = QPushButton("Start Capture")
        self.start_button.clicked.connect(self.toggle_capture)
        self.start_button.setEnabled(False)  # Disabled until model is loaded
        self.start_button.setFixedWidth(220)  # Increased from 180 to 220 to fit text
        self.start_button.setFixedHeight(36)  # Set fixed height for consistent button size
        
        # Start Overlay button
        self.overlay_button = QPushButton("Start Overlay")
        self.overlay_button.clicked.connect(self.toggle_overlay_mode)
        self.overlay_button.setEnabled(False)  # Disabled until model is loaded
        self.overlay_button.setFixedWidth(220)  # Same width as other buttons
        self.overlay_button.setFixedHeight(36)  # Same height as other buttons
        
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
        
        # Add overlay button with the same alignment
        overlay_container = QHBoxLayout()
        overlay_container.addStretch()  # Push button to the right
        overlay_container.addWidget(self.overlay_button)
        buttons_layout.addLayout(overlay_container)
        
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

    def toggle_volume_control(self, enabled):
        """Enable or disable volume control functionality"""
        self.volume_control_enabled = enabled
        if enabled:
            self.volume_label.setText("Volume control: Active")
            # Update volume based on current consensus
            if self.consensus_prediction is not None:
                self.volume_controller.update_classification(
                    self.consensus_prediction, 
                    self.consensus_confidence
                )
        else:
            self.volume_label.setText("Volume control: Disabled")
            # Restore original volume
            self.volume_controller.restore_volume()

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
            self.overlay_button.setEnabled(True)  # Enable overlay button when model is loaded
            self.model_status_label.setText(f"Model Status: Loaded ({message})")
            
            # Show fluid animation on startup
            self.video_frame.hide()
            self.fluid_animation.show()
            self.fluid_animation.start_animation()
        else:
            self.model_status_label.setText(f"Model Error: {message}")
            self.prediction_label.setText("Current Frame: Error")
            self.prediction_label.setStyleSheet(f"color: {RED_COLOR};")

    def toggle_capture(self):
        if not self.running:
            # Start capture
            self.running = True
            self.start_button.setText("Stop Capture")
            
            # Reset frame detection state
            self.last_frame = None
            self.prev_frame = None
            
            # Reset prediction history and consensus
            self.prediction_history = []
            self.consensus_prediction = None
            self.consensus_confidence = 0.0
            
            for label in self.history_labels:
                label.setText("N/A")
                label.setStyleSheet("")
            
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
            self.prediction_label.setText("Current Frame: N/A")
            self.prediction_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 10pt;")
            self.confidence_label.setText("Confidence: 0%")
            self.consensus_label.setText("CONSENSUS: N/A")
            self.consensus_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 11pt; font-weight: bold;")
            self.model_status_label.setText("Model Status: Idle")
            
            # Restore volume when stopping
            if self.volume_control_enabled:
                self.volume_controller.restore_volume()

    def calculate_consensus(self):
        """Calculate a stable consensus prediction from history"""
        if not self.prediction_history:
            return None, 0.0
        
        # Count basketball and non-basketball predictions
        basketball_count = sum(1 for is_bb, _ in self.prediction_history if is_bb)
        not_basketball_count = len(self.prediction_history) - basketball_count
        
        # Calculate weights based on:
        # 1. Recency (newer predictions have more weight)
        # 2. Confidence magnitude (high and low confidences have more weight than mid-range)
        recency_weights = [max(0.5, 1.0 - 0.15 * i) for i in range(len(self.prediction_history))]
        
        basketball_confidence = 0.0
        not_basketball_confidence = 0.0
        effective_bb_count = 0
        effective_not_bb_count = 0
        
        for i, (is_bb, conf) in enumerate(self.prediction_history):
            # Calculate confidence magnitude weight
            # - Predictions close to 0.5 get reduced weight (uncertain)
            # - Predictions close to 0 or 1 get increased weight (certain)
            confidence_certainty = abs(conf - 0.5) * 2  # 0.0 for conf=0.5, 1.0 for conf=0 or 1
            confidence_weight = 0.5 + confidence_certainty  # Range from 0.5 to 1.5
            
            # Combine recency and confidence weights
            combined_weight = recency_weights[i] * confidence_weight
            
            if is_bb:
                basketball_confidence += combined_weight * conf
                effective_bb_count += combined_weight
            else:
                not_basketball_confidence += combined_weight * (1.0 - conf)
                effective_not_bb_count += combined_weight
        
        # Normalize confidences
        if effective_bb_count > 0:
            basketball_confidence /= effective_bb_count
        if effective_not_bb_count > 0:
            not_basketball_confidence /= effective_not_bb_count
        
        # Determine consensus using effective counts
        if effective_bb_count > effective_not_bb_count * 1.1:  # 10% threshold for stability
            return True, basketball_confidence * 100
        elif effective_not_bb_count > effective_bb_count * 1.1:
            return False, not_basketball_confidence * 100
        else:
            # If counts are close, use the class with higher confidence
            if basketball_confidence > not_basketball_confidence:
                return True, basketball_confidence * 100
            else:
                return False, not_basketball_confidence * 100

    def get_confidence_trend(self):
        """Determine if confidence is trending up, down or stable"""
        if len(self.prediction_history) < 2:
            return "stable"
            
        # Get the last two confidences for the consensus class
        confidences = []
        is_consensus = self.consensus_prediction
        
        for is_bb, conf in self.prediction_history[:2]:
            if is_bb == is_consensus:
                confidences.append(conf)
            else:
                confidences.append(1.0 - conf)
                
        if len(confidences) < 2:
            return "stable"
            
        diff = confidences[0] - confidences[1]
        
        if abs(diff) < 0.05:  # Less than 5% change
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

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
        # Update prediction labels for current frame
        prediction_text = "Basketball" if is_basketball else "Not Basketball"
        self.prediction_label.setText(f"Current Frame: {prediction_text}")
        
        # Set color based on prediction
        if is_basketball:
            self.prediction_label.setStyleSheet(f"color: {RED_COLOR}; font-size: 10pt;")
        else:
            self.prediction_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 10pt;")
        
        # Update confidence
        confidence_pct = confidence * 100 if is_basketball else (1 - confidence) * 100
        self.confidence_label.setText(f"Confidence: {confidence_pct:.2f}%")
        
        # Update model status with inference time
        self.model_status_label.setText(f"Model Status: Inference in {inference_time*1000:.1f}ms")
        
        # Add to prediction history
        self.prediction_history.insert(0, (is_basketball, confidence))
        
        # Trim history to max size
        if len(self.prediction_history) > HISTORY_SIZE:
            self.prediction_history = self.prediction_history[:HISTORY_SIZE]
        
        # Calculate consensus from history
        prev_consensus = self.consensus_prediction
        self.consensus_prediction, self.consensus_confidence = self.calculate_consensus()
        confidence_trend = self.get_confidence_trend()
        
        # Update consensus label
        if self.consensus_prediction is not None:
            consensus_text = "BASKETBALL" if self.consensus_prediction else "NOT BASKETBALL"
            
            # Add trend indicator
            if confidence_trend == "increasing":
                trend_indicator = " ↑"
            elif confidence_trend == "decreasing":
                trend_indicator = " ↓"
            else:
                trend_indicator = " ="
                
            self.consensus_label.setText(f"CONSENSUS: {consensus_text} ({self.consensus_confidence:.1f}%){trend_indicator}")
            
            # High confidence consensus gets stronger styling
            if self.consensus_confidence >= MIN_CONSENSUS_CONFIDENCE:
                if self.consensus_prediction:
                    self.consensus_label.setStyleSheet(f"color: {RED_COLOR}; font-size: 11pt; font-weight: bold;")
                else:
                    self.consensus_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 11pt; font-weight: bold;")
            else:
                # Lower confidence gets less prominent styling
                if self.consensus_prediction:
                    self.consensus_label.setStyleSheet(f"color: {RED_COLOR}; font-size: 11pt; font-style: italic;")
                else:
                    self.consensus_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 11pt; font-style: italic;")
        
        # Update history display
        for i, label in enumerate(self.history_labels):
            if i < len(self.prediction_history):
                hist_is_basketball, hist_confidence = self.prediction_history[i]
                hist_text = "Basketball" if hist_is_basketball else "Not Basketball"
                hist_confidence_pct = hist_confidence * 100 if hist_is_basketball else (1 - hist_confidence) * 100
                label.setText(f"{i+1}: {hist_text} ({hist_confidence_pct:.1f}%)")
                
                # Set color based on prediction
                if hist_is_basketball:
                    label.setStyleSheet(f"color: {RED_COLOR};")
                else:
                    label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR};")
            else:
                label.setText(f"{i+1}: N/A")
                label.setStyleSheet("")
        
        # Update volume control if consensus changed or confidence changed significantly
        if self.volume_control_enabled and self.consensus_prediction is not None:
            # Only adjust volume if consensus changed or on first prediction
            if prev_consensus != self.consensus_prediction or prev_consensus is None:
                self.volume_controller.update_classification(
                    self.consensus_prediction, 
                    self.consensus_confidence
                )
        
        # Update overlay if it's active
        if self.overlay_mode:
            # Use consensus prediction for overlay instead of single frame
            if self.consensus_prediction is not None:
                self.overlay.update_prediction(
                    self.consensus_prediction, 
                    self.consensus_confidence / 100.0  # Convert back to 0-1 scale
                )
            else:
                self.overlay.update_prediction(is_basketball, confidence)

    def toggle_overlay_mode(self):
        """Toggle between main window and overlay mode"""
        if not self.overlay_mode:
            # Switch to overlay mode
            self.overlay_mode = True
            self.overlay_button.setText("Exit Overlay")
            
            # Make sure overlay shows the correct initial button state
            if not self.running:
                self.overlay.toggle_button.setText("▶")
            else:
                self.overlay.toggle_button.setText("‖")
            
            self.overlay.running = self.running  # Sync running state
            
            self.hide()  # Hide main window
            self.overlay.show()  # Show overlay
        else:
            # Exit overlay mode
            self.exit_overlay_mode()

    def exit_overlay_mode(self):
        """Exit overlay mode and return to main window"""
        self.overlay_mode = False
        self.overlay_button.setText("Start Overlay")
        self.overlay.hide()  # Hide overlay
        self.show()  # Show main window
        self.activateWindow()  # Focus main window

    def overlay_toggle_capture(self):
        """Handle toggle capture from overlay"""
        if self.running:
            # Stop capture
            self.toggle_capture()
        else:
            # Start capture
            self.toggle_capture()
        
        # Update overlay button state to match with correct styling
        if self.running:
            self.overlay.toggle_button.setText("‖")
        else:
            self.overlay.toggle_button.setText("▶")
            
        self.overlay.running = self.running
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Restore volume to original level
        self.volume_controller.restore_volume()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = BasketballClassifierApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 