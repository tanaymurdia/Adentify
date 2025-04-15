"""
Settings Dialog for Basketball Classifier App
This file contains a dialog for adjusting application settings.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QSlider, QPushButton)

# Import styling
from style import STYLE, RED_COLOR

class SettingsDialog(QDialog):
    """Dialog for adjusting application settings"""
    
    def __init__(self, parent=None, scene_threshold=30.0):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setStyleSheet(STYLE)
        
        self.scene_threshold = scene_threshold
        self.result_threshold = scene_threshold  # Store the result
        
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
        main_layout.addSpacing(20)
        
        # Scene sensitivity control
        scene_layout = QVBoxLayout()
        
        # Label and value
        scene_header = QHBoxLayout()
        scene_label = QLabel("Scene Sensitivity:")
        scene_label.setFont(QFont("Consolas", 10))
        self.value_label = QLabel(f"{self.scene_threshold:.1f}")
        self.value_label.setFont(QFont("Consolas", 10))
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
        
        # Add to main layout
        main_layout.addLayout(scene_layout)
        
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
    
    def get_threshold(self):
        """Return the selected threshold value"""
        return self.result_threshold 