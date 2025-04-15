"""
Settings Dialog for Basketball Classifier App
This file contains a dialog for adjusting application settings.
"""

import psutil
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QSlider, QPushButton, QGroupBox, QGridLayout)

# Import styling
from style import STYLE, RED_COLOR, LIGHT_TEXT_COLOR

class SettingsDialog(QDialog):
    """Dialog for adjusting application settings"""
    
    def __init__(self, parent=None, scene_threshold=30.0, fps=0):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(700)
        self.setStyleSheet(STYLE)
        
        self.parent = parent
        self.scene_threshold = scene_threshold
        self.result_threshold = scene_threshold  # Store the result
        self.current_fps = fps
        
        # Setup timer for updating metrics
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)  # Update every second
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Application Settings")
        title_label.setFont(QFont("Consolas", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add space
        main_layout.addSpacing(10)
        
        # Performance Metrics section
        metrics_group = QGroupBox("Performance Metrics")
        metrics_group.setFont(QFont("Consolas", 10, QFont.Bold))
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU Usage
        cpu_label = QLabel("CPU Usage:")
        cpu_label.setFont(QFont("Consolas", 9))
        self.cpu_value = QLabel("0%")
        self.cpu_value.setFont(QFont("Consolas", 9))
        
        # FPS
        fps_label = QLabel("FPS:")
        fps_label.setFont(QFont("Consolas", 9))
        self.fps_value = QLabel(f"{self.current_fps}")
        self.fps_value.setFont(QFont("Consolas", 9))
        
        # Memory usage
        memory_label = QLabel("Memory Usage:")
        memory_label.setFont(QFont("Consolas", 9))
        self.memory_value = QLabel("0 MB")
        self.memory_value.setFont(QFont("Consolas", 9))
        
        # Add to grid
        metrics_layout.addWidget(cpu_label, 0, 0)
        metrics_layout.addWidget(self.cpu_value, 0, 1)
        metrics_layout.addWidget(fps_label, 1, 0)
        metrics_layout.addWidget(self.fps_value, 1, 1)
        metrics_layout.addWidget(memory_label, 2, 0)
        metrics_layout.addWidget(self.memory_value, 2, 1)
        
        # Add metrics group to main layout
        main_layout.addWidget(metrics_group)
        
        # Add space
        main_layout.addSpacing(10)
        
        # Scene sensitivity control
        scene_group = QGroupBox("Capture Settings")
        scene_group.setFont(QFont("Consolas", 10, QFont.Bold))
        scene_layout = QVBoxLayout(scene_group)
        
        # Label and value
        scene_header = QHBoxLayout()
        scene_label = QLabel("Scene Sensitivity:")
        scene_label.setFont(QFont("Consolas", 9))
        self.value_label = QLabel(f"{self.scene_threshold:.1f}")
        self.value_label.setFont(QFont("Consolas", 9))
        scene_header.addWidget(scene_label)
        scene_header.addStretch()
        scene_header.addWidget(self.value_label)
        
        # Slider
        self.scene_slider = QSlider(Qt.Horizontal)
        self.scene_slider.setRange(1, 80)
        self.scene_slider.setValue(int(self.scene_threshold))
        self.scene_slider.valueChanged.connect(self.update_threshold)
        
        # Add tooltip that appears on hover
        self.scene_slider.setToolTip("Higher values mean less sensitivity to scene changes")
        
        # Add components to scene layout
        scene_layout.addLayout(scene_header)
        scene_layout.addWidget(self.scene_slider)
        
        # Add scene group to main layout
        main_layout.addWidget(scene_group)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(button_layout)
    
    def update_threshold(self, value):
        """Update threshold value when slider is moved"""
        self.result_threshold = value
        self.value_label.setText(f"{value:.1f}")
    
    def update_metrics(self):
        """Update the performance metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_value.setText(f"{cpu_percent:.1f}%")
        
        # Update FPS from main app if available
        if hasattr(self.parent, 'fps'):
            self.current_fps = self.parent.fps
            self.fps_value.setText(f"{self.current_fps}")
        
        # Memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        self.memory_value.setText(f"{memory_mb:.1f} MB")
    
    def get_threshold(self):
        """Return the selected threshold value"""
        return self.result_threshold
        
    def closeEvent(self, event):
        """Stop timer when dialog is closed"""
        self.metrics_timer.stop()
        super().closeEvent(event) 