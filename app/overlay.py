#!/usr/bin/env python
"""
Basketball Classifier Overlay
This provides a minimized transparent overlay with a glowing edge effect,
with a rounded rectangle border that gradiently merges into the background.
Fixed paintEvent to use layered rounded rectangles with color blending
from RED_COLOR at the outside to DARK_BG_COLOR at the inside of the glow.
"""
import os
import sys
import time
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint, QRectF
from PyQt5.QtGui import (QFont, QColor, QPainter, QPen, QBrush,
                         QRadialGradient, QLinearGradient, QPainterPath)
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout,
                             QPushButton)

# Import styling constants (or use defaults)
try:
    from style import RED_COLOR, LIGHT_TEXT_COLOR, DARK_BG_COLOR
except ImportError:
    print("Warning: style.py not found. Using default colors.")
    RED_COLOR = "#FF3C3C"
    LIGHT_TEXT_COLOR = "#FFFFFF"
    DARK_BG_COLOR = "#141414"


# Create QColor objects
RED_QCOLOR = QColor(RED_COLOR) if isinstance(RED_COLOR, str) else RED_COLOR
DARK_BG_QCOLOR = QColor(DARK_BG_COLOR) if isinstance(DARK_BG_COLOR, str) else DARK_BG_COLOR
LIGHT_TEXT_QCOLOR = QColor(LIGHT_TEXT_COLOR) if isinstance(LIGHT_TEXT_COLOR, str) else LIGHT_TEXT_COLOR

# Set alpha for the main background color
# Adjust alpha (0-255) as needed for desired background transparency
DARK_BG_QCOLOR.setAlpha(245)  # Increased from 230 to 245 for more opacity

class ClassifierOverlay(QWidget):
    exitOverlay = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.running = False
        self.prediction = "N/A"
        self.confidence = 0.0
        self.resize(300, 160) # Keep size consistent
        self.init_ui()
        self.position_overlay()
        self._drag_position = QPoint()

    def init_ui(self):
        """Set up the overlay UI"""
        self.layout = QVBoxLayout(self)
        # Margin should accommodate the glow_extent defined in paintEvent
        glow_margin = 12  # Reduced from 25 to 12 for thinner margin
        self.layout.setContentsMargins(glow_margin, glow_margin, glow_margin, glow_margin)
        self.layout.setSpacing(6)

        # --- UI Elements (Labels, Buttons) - Keep consistent ---
        self.prediction_label = QLabel("N/A")
        self.prediction_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.prediction_label.setStyleSheet(f"color: {LIGHT_TEXT_QCOLOR.name()}; background-color: transparent;")
        self.prediction_label.setAlignment(Qt.AlignCenter)

        self.confidence_label = QLabel("0%")
        self.confidence_label.setFont(QFont("Arial", 9))
        self.confidence_label.setStyleSheet(f"color: {LIGHT_TEXT_QCOLOR.name()}; background-color: transparent;")
        self.confidence_label.setAlignment(Qt.AlignCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(25)

        button_size = 45
        button_radius = button_size / 2
        button_border_color = RED_QCOLOR.name()
        button_border_hover_qcolor = QColor(button_border_color)
        button_border_hover_qcolor = button_border_hover_qcolor.lighter(140)
        button_border_hover_qcolor.setHsv(button_border_hover_qcolor.hue(), max(0, int(button_border_hover_qcolor.saturation() * 0.7)), button_border_hover_qcolor.value())
        button_border_hover_color = button_border_hover_qcolor.name()

        button_bg_color = "#181818"
        button_hover_bg_color = "#282828"
        button_pressed_bg_color = "#383838"

        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(button_size, button_size)
        play_pause_style = f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_border_color};
                border-radius: {button_radius}px;
                border: 2px solid {button_border_color};
                font-family: 'Arial';
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_bg_color};
                border: 2px solid {button_border_hover_color};
                color: {button_border_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed_bg_color};
            }}
        """
        self.toggle_button.setStyleSheet(play_pause_style)
        self.toggle_button.setText("▶")
        self.toggle_button.clicked.connect(self.toggle_capture)

        self.exit_button = QPushButton()
        self.exit_button.setFixedSize(button_size, button_size)
        exit_button_style = f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_border_color};
                border-radius: {button_radius}px;
                border: 2px solid {button_border_color};
                font-family: Arial;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_bg_color};
                border: 2px solid {button_border_hover_color};
                color: {button_border_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed_bg_color};
            }}
        """
        self.exit_button.setStyleSheet(exit_button_style)
        self.exit_button.setText("×")
        self.exit_button.clicked.connect(self.exit_overlay_mode)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addWidget(self.exit_button)
        buttons_layout.addStretch()

        self.layout.addWidget(self.prediction_label)
        self.layout.addSpacing(5)
        self.layout.addWidget(self.confidence_label)
        self.layout.addSpacing(15)
        self.layout.addLayout(buttons_layout)
        # --- End of UI Elements ---

    def position_overlay(self):
        """Position the overlay in the top right corner."""
        try:
            screen_geometry = QApplication.primaryScreen().availableGeometry()
        except AttributeError:
             screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 20)

    def paintEvent(self, event):
        """Paint event for background and the layered rounded rectangle glow."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Define base colors
        bg_color_base = QColor(DARK_BG_QCOLOR) # Use base color for blending
        red_color_base = QColor(RED_QCOLOR)   # Use base color for blending

        # Define geometry
        corner_radius = 20.0
        glow_extent = 5  # Reduced from 18 to 10 for thinner gradient

        # Rectangles defining the glow region and the solid background region
        solid_bg_rect = QRectF(self.rect()).adjusted(glow_extent, glow_extent, -glow_extent, -glow_extent)
        outer_glow_rect = QRectF(self.rect())

        # Ensure the solid background rectangle is valid
        if solid_bg_rect.width() <= 0 or solid_bg_rect.height() <= 0:
            print("Warning: Widget size too small for defined glow extent. Drawing solid background.")
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bg_color_base)) # Use brush for solid fill
            painter.drawRoundedRect(self.rect(), corner_radius, corner_radius)
            return

        # --- Draw the Layered Rounded Rectangle Gradient ---

        num_glow_layers = 60 # Increased layers for smoother transition

        # Iterate from the outer edge inwards
        for i in range(num_glow_layers):
            # Calculate the blending factor for this layer (0 at outer edge, 1 at inner edge of glow)
            lerp_factor = i / (num_glow_layers - 1) if num_glow_layers > 1 else 0.0

            # Calculate the current rectangle for this layer
            current_rect = QRectF(
                outer_glow_rect.left() * (1.0 - lerp_factor) + solid_bg_rect.left() * lerp_factor,
                outer_glow_rect.top() * (1.0 - lerp_factor) + solid_bg_rect.top() * lerp_factor,
                outer_glow_rect.width() * (1.0 - lerp_factor) + solid_bg_rect.width() * lerp_factor,
                outer_glow_rect.height() * (1.0 - lerp_factor) + solid_bg_rect.height() * lerp_factor
            )

            # Blend colors from RED_COLOR (outside, lerp_factor=0) to DARK_BG_COLOR (inside, lerp_factor=1)
            current_red = int(red_color_base.red() * (1.0 - lerp_factor) + bg_color_base.red() * lerp_factor)
            current_green = int(red_color_base.green() * (1.0 - lerp_factor) + bg_color_base.green() * lerp_factor)
            current_blue = int(red_color_base.blue() * (1.0 - lerp_factor) + bg_color_base.blue() * lerp_factor)

            # Calculate alpha fading from near-transparent at the outermost edge to
            # the alpha of the background color at the innermost edge of the glow.
            # This creates the merge effect with the background behind the overlay.
            # Alpha goes from 0 (or a small start_alpha) to bg_color_base.alpha()
            start_alpha = 0 # Start with full transparency at the outer edge
            end_alpha = bg_color_base.alpha() # End with background color's alpha at the inner edge of glow band
            current_alpha = int(start_alpha * (1.0 - lerp_factor) + end_alpha * lerp_factor)
            current_alpha = min(255, max(0, current_alpha)) # Clamp alpha

            # Create the color for the current layer
            current_color = QColor(current_red, current_green, current_blue, current_alpha)

            # Set pen color and thickness
            painter.setPen(QPen(current_color, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush) # Don't fill the shape

            # Draw the rounded rectangle border for the current layer
            painter.drawRoundedRect(current_rect, corner_radius, corner_radius)

        # --- Draw the Solid Inner Background ---
        painter.setPen(Qt.NoPen)
        # Use a brush with the background color (including its alpha) for the solid fill
        painter.setBrush(QBrush(bg_color_base))
        painter.drawRoundedRect(solid_bg_rect, corner_radius, corner_radius)


    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def toggle_capture(self):
        """Toggle the running state and update the button text."""
        self.running = not self.running
        if self.running:
            self.toggle_button.setText("‖") # Pause symbol
        else:
            self.toggle_button.setText("▶") # Play symbol
        self.update()


    def update_prediction(self, is_basketball, confidence):
        """Update the prediction labels."""
        if is_basketball:
            prediction_text = "BASKETBALL"
            prediction_color = RED_QCOLOR.name()
            confidence_pct = confidence * 100
        else:
            prediction_text = "NOT BASKETBALL"
            prediction_color = LIGHT_TEXT_QCOLOR.name()
            confidence_pct = (1 - confidence) * 100

        self.prediction_label.setText(prediction_text)
        self.prediction_label.setStyleSheet(f"color: {prediction_color}; font-weight: bold; background-color: transparent;")

        self.confidence_label.setText(f"{confidence_pct:.1f}%")
        self.confidence_label.setStyleSheet(f"color: {LIGHT_TEXT_QCOLOR.name()}; background-color: transparent;")
        self.update()


    def exit_overlay_mode(self):
        """Hide the overlay and emit the exit signal."""
        self.hide()
        self.exitOverlay.emit()

    def closeEvent(self, event):
        """Handle the window close event."""
        self.exit_overlay_mode()
        event.accept()

# Example usage
if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = ClassifierOverlay()
    overlay.show()

    def update_test():
        """Simulate updating prediction data."""
        import random
        is_ball = random.choice([True, False])
        conf = random.uniform(0.7, 0.99) if is_ball else random.uniform(0.6, 0.95)
        if overlay.isVisible():
            overlay.update_prediction(is_ball, conf)

    timer = QTimer()
    timer.timeout.connect(update_test)
    timer.start(1500)

    overlay.exitOverlay.connect(app.quit)

    sys.exit(app.exec_())