#!/usr/bin/env python
"""
Basketball Classifier Overlay
This provides a minimized transparent overlay for the basketball classifier app.
"""
import os
import sys
import time
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QRadialGradient, QLinearGradient, QPainterPath
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, 
                           QVBoxLayout, QHBoxLayout, 
                           QPushButton)

# Import styling constants
from style import RED_COLOR, LIGHT_TEXT_COLOR, DARK_BG_COLOR

# Create QColor object from RED_COLOR (handling whether it's a string or already a QColor)
RED_QCOLOR = QColor(RED_COLOR) if isinstance(RED_COLOR, str) else RED_COLOR

class ClassifierOverlay(QWidget):
    exitOverlay = pyqtSignal()  # Signal to notify main app when overlay is closed
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.95)
        self.running = False
        self.prediction = "N/A"
        self.confidence = 0.0
        
        # Set initial size
        self.resize(280, 140)
        
        # Initialize UI
        self.init_ui()
        
        # Position in top-right corner
        self.position_overlay()
    
    def init_ui(self):
        """Set up the overlay UI"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(4)  # Reduce spacing between elements
        
        # Prediction display
        self.prediction_label = QLabel("N/A")
        self.prediction_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.prediction_label.setStyleSheet("color: white;")
        self.prediction_label.setAlignment(Qt.AlignCenter)
        
        # Confidence display
        self.confidence_label = QLabel("0%")
        self.confidence_label.setFont(QFont("Arial", 8))
        self.confidence_label.setStyleSheet("color: white;")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)  # Space between buttons
        
        # Button size matches the reference images
        button_size = 40
        
        # Play/Pause button with basketball-themed styling
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(button_size, button_size)
        play_pause_style = """
            QPushButton {
                background-color: #111;
                color: #f55;
                border-radius: 20px;
                border: 2px solid #f55;
                font-family: 'Arial';
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #222;
                border: 2px solid #f77;
                color: #f77;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """
        self.toggle_button.setStyleSheet(play_pause_style)
        # Start with play button (▶) since we're not running yet
        self.toggle_button.setText("▶")
        self.toggle_button.clicked.connect(self.toggle_capture)
        
        # Exit overlay button
        self.exit_button = QPushButton()
        self.exit_button.setFixedSize(button_size, button_size)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #111;
                color: #f55;
                border-radius: 20px;
                border: 2px solid #f55;
                font-family: Arial;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #222;
                border: 2px solid #f77;
                color: #f77;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        self.exit_button.setText("×")
        self.exit_button.clicked.connect(self.exit_overlay_mode)
        
        # Add buttons to layout with spacing
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addWidget(self.exit_button)
        buttons_layout.addStretch()
        
        # Add all elements to main layout
        self.layout.addWidget(self.prediction_label)
        self.layout.addSpacing(2)  # Small spacing after prediction
        self.layout.addWidget(self.confidence_label)
        self.layout.addSpacing(10)  # Spacing before buttons
        self.layout.addLayout(buttons_layout)
    
    def position_overlay(self):
        """Position the overlay in the top-right corner of the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 20)
    
    def paintEvent(self, event):
        """Custom paint event to create rounded corners with blur effect and gradient border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create shadow effect
        shadow_rect = self.rect().adjusted(-3, -3, 3, 3)
        shadow_color = QColor(0, 0, 0, 90)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRoundedRect(shadow_rect, 16, 16)
        
        # Draw outer rectangle with red color for border base
        outer_rect = self.rect()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 60, 60, 200))  # Red color
        painter.drawRoundedRect(outer_rect, 14, 14)
        
        # Create gradient from border to background
        border_width = 4  # Thicker border for more visible gradient
        inner_rect = self.rect().adjusted(border_width, border_width, -border_width, -border_width)
        
        # Create radial gradient for a smooth transition
        gradient = QRadialGradient(self.rect().center(), self.rect().width()/2)
        gradient.setColorAt(0.8, QColor(20, 20, 20, 250))  # Inner background color
        gradient.setColorAt(0.9, QColor(60, 20, 20, 250))  # Mid transition
        gradient.setColorAt(1.0, QColor(255, 60, 60, 180))  # Outer border color
        
        # Draw inner rectangle with gradient
        painter.setBrush(QColor(20, 20, 20, 250))  # Dark background
        painter.drawRoundedRect(inner_rect, 10, 10)
        
        # Draw an additional gradient overlay for enhanced border effect
        border_gradient = QLinearGradient(outer_rect.topLeft(), outer_rect.bottomRight())
        border_gradient.setColorAt(0, QColor(255, 100, 100, 120))
        border_gradient.setColorAt(0.5, QColor(255, 50, 50, 100))
        border_gradient.setColorAt(1, QColor(200, 40, 40, 140))
        
        painter.setPen(QPen(QColor(255, 60, 60, 0), 1))  # Invisible pen
        painter.setBrush(border_gradient)
        
        # Create path to draw only the border area (between outer and inner rects)
        path = QPainterPath()
        path.addRoundedRect(QRectF(outer_rect), 14, 14)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(QRectF(inner_rect), 10, 10)
        path = path.subtracted(inner_path)
        
        # Draw the border with gradient
        painter.drawPath(path)
    
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
        
        # Update button style for play/pause state
        if self.running:
            # Use double vertical bar symbol for pause that looks cleaner
            self.toggle_button.setText("‖")
        else:
            # Use the same styling for the play button (red on black)
            self.toggle_button.setText("▶")
    
    def update_prediction(self, is_basketball, confidence):
        """Update the prediction display"""
        # Update prediction label
        prediction_text = "BASKETBALL" if is_basketball else "NOT BASKETBALL"
        self.prediction_label.setText(prediction_text)
        
        # Set color based on prediction
        if is_basketball:
            self.prediction_label.setStyleSheet("color: #f66; font-weight: bold;")
        else:
            self.prediction_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Update confidence
        confidence_pct = confidence * 100 if is_basketball else (1 - confidence) * 100
        self.confidence_label.setText(f"{confidence_pct:.1f}%")
    
    def exit_overlay_mode(self):
        """Exit overlay mode and emit signal to main app"""
        self.hide()
        self.exitOverlay.emit()
        
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        event.accept() 