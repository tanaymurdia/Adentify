#!/usr/bin/env python
"""
Basketball Classifier Overlay
This provides a minimized transparent overlay for the basketball classifier app.
"""
import os
import sys
import time
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, 
                           QVBoxLayout, QHBoxLayout, 
                           QPushButton)

class ClassifierOverlay(QWidget):
    exitOverlay = pyqtSignal()  # Signal to notify main app when overlay is closed
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.85)
        self.running = False
        self.prediction = "N/A"
        self.confidence = 0.0
        
        # Set initial size
        self.resize(300, 130)
        
        # Initialize UI
        self.init_ui()
        
        # Position in top-right corner
        self.position_overlay()
    
    def init_ui(self):
        """Set up the overlay UI"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Prediction display
        self.prediction_label = QLabel("N/A")
        self.prediction_label.setFont(QFont("Consolas", 16, QFont.Bold))
        self.prediction_label.setStyleSheet("color: white;")
        self.prediction_label.setAlignment(Qt.AlignCenter)
        
        # Confidence display
        self.confidence_label = QLabel("0%")
        self.confidence_label.setFont(QFont("Consolas", 12))
        self.confidence_label.setStyleSheet("color: white;")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Play/Pause button
        self.toggle_button = QPushButton("⏸️")
        self.toggle_button.setFont(QFont("Segoe UI Symbol", 12))
        self.toggle_button.setFixedSize(36, 36)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 180);
                color: white;
                border-radius: 18px;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 200);
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_capture)
        
        # Exit overlay button
        self.exit_button = QPushButton("✕")
        self.exit_button.setFont(QFont("Segoe UI Symbol", 12))
        self.exit_button.setFixedSize(36, 36)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 0, 0, 180);
                color: white;
                border-radius: 18px;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
            }
        """)
        self.exit_button.clicked.connect(self.exit_overlay_mode)
        
        # Add buttons to layout with spacing
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(self.exit_button)
        buttons_layout.addStretch()
        
        # Add all elements to main layout
        self.layout.addWidget(self.prediction_label)
        self.layout.addWidget(self.confidence_label)
        self.layout.addSpacing(10)
        self.layout.addLayout(buttons_layout)
    
    def position_overlay(self):
        """Position the overlay in the top-right corner of the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 20)
    
    def paintEvent(self, event):
        """Custom paint event to create rounded corners with blur effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle
        brush = QBrush(QColor(30, 30, 30, 200))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        
        # Add border
        pen = QPen(QColor(200, 0, 0, 150), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect(), 15, 15)
    
    def mousePressEvent(self, event):
        """Allow dragging the overlay around"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Move the overlay when dragged"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def toggle_capture(self):
        """Toggle capture state"""
        self.running = not self.running
        self.toggle_button.setText("▶️" if not self.running else "⏸️")
        
        # The actual capture logic will be handled in the main app
    
    def update_prediction(self, is_basketball, confidence):
        """Update the prediction display"""
        # Update prediction label
        prediction_text = "BASKETBALL" if is_basketball else "NOT BASKETBALL"
        self.prediction_label.setText(prediction_text)
        
        # Set color based on prediction
        if is_basketball:
            self.prediction_label.setStyleSheet("color: rgb(255, 62, 62); font-weight: bold;")
        else:
            self.prediction_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Update confidence
        confidence_pct = confidence * 100 if is_basketball else (1 - confidence) * 100
        self.confidence_label.setText(f"{confidence_pct:.1f}%")
    
    def exit_overlay_mode(self):
        """Exit overlay mode and emit signal to main app"""
        self.hide()
        self.exitOverlay.emit() 