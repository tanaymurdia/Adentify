"""
Fluid Animation for Basketball Classifier App
This file creates elegant, flowing red lines similar to the reference image.
Revised version using QGraphicsScene and QGraphicsBlurEffect for soft glow.
Includes fix for removing the default QGraphicsView border.
"""

import math
import random
import time
from PyQt5.QtCore import Qt, QTimer, QPointF, QPropertyAnimation, QEasingCurve, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen
from PyQt5.QtWidgets import (QWidget, QGraphicsOpacityEffect, QGraphicsView,
                             QGraphicsScene, QGraphicsPathItem, QGraphicsBlurEffect,
                             QGraphicsItem, QFrame) # <-- Import QFrame

# Define colors directly
RED_COLOR = QColor(255, 50, 50) # Adjusted red
DARK_BG_COLOR = QColor(0, 0, 0) # Black background

# --- Custom Graphics Item for the Curve ---
class CurveItem(QGraphicsPathItem):
    """A QGraphicsPathItem representing a single flowing, blurred curve."""
    def __init__(self, full_path, width, height):
        super().__init__(full_path)
        self.full_path = full_path # Store the complete path
        self.width = width
        self.height = height

        # --- Visual Properties ---
        self.base_color = RED_COLOR
        self.base_thickness = random.uniform(1.5, 2.5) # Increased thickness
        self.blur_radius = random.uniform(10, 18)    # Increased blur radius

        # --- Animation Properties ---
        self.life = 1.0
        self.fade_speed = random.uniform(0.0015, 0.004)
        self.animation_offset = random.uniform(0, 2 * math.pi)

        # --- Growth Animation ---
        self.progress = 0.0
        self.growth_complete = False
        self.growth_speed = random.uniform(0.01, 0.025)

        # --- Graphics Effects ---
        self.setOpacity(0.0) # Start fully transparent
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(self.blur_radius)
        self.setGraphicsEffect(self.blur_effect)

        # --- Pen ---
        self.current_pen = QPen(self.base_color)
        self.current_pen.setCapStyle(Qt.RoundCap)
        self.current_pen.setJoinStyle(Qt.RoundJoin)
        self.current_pen.setWidthF(self.base_thickness)
        self.setPen(self.current_pen)

        # Initial path setup (start empty)
        self.setPath(QPainterPath())

    def update_item(self):
        """Update the curve's state (growth, life, opacity, path). Returns True if alive."""
        if not self.growth_complete:
            # Grow the curve gradually
            self.progress += self.growth_speed
            if self.progress >= 1.0:
                self.progress = 1.0
                self.growth_complete = True
                self.setOpacity(1.0) # Set full opacity once grown
            else:
                 self.setOpacity(self.progress) # Fade in as it grows

            # Update the drawn path based on progress
            new_path = QPainterPath()
            start_point = self.full_path.pointAtPercent(0)
            # Check if the path is valid and progress > 0 before drawing
            if self.progress > 0 and start_point is not None:
                 new_path.moveTo(start_point)
                 step = 0.015 # Balance smoothness and performance
                 current_percent = step
                 while current_percent < self.progress:
                      pt = self.full_path.pointAtPercent(current_percent)
                      # Check if pointAtPercent returned a valid point
                      if pt is not None:
                           new_path.lineTo(pt)
                      current_percent += step
                 # Add the final point precisely at the progress percentage
                 final_pt = self.full_path.pointAtPercent(self.progress)
                 if final_pt is not None:
                      new_path.lineTo(final_pt)
                 self.setPath(new_path)
            else:
                 # Set an empty path if progress is 0 or path is invalid
                 self.setPath(QPainterPath())

        else:
            # Fade out
            self.life -= self.fade_speed
            self.setOpacity(max(0.0, self.life)) # Fade item's opacity

        # Optional: Update pen thickness pulsing
        # thickness_variation = math.sin(time.time() * 1.8 + self.animation_offset) * 0.2 + 1.0
        # self.current_pen.setWidthF(self.base_thickness * thickness_variation)
        # self.setPen(self.current_pen) # Uncomment if pulsing is desired

        # Check if item should be removed
        return self.life > -0.1

# --- Main Animation Widget (now QGraphicsView) ---
class FluidAnimation(QGraphicsView):
    """Fluid animation widget using QGraphicsScene for blurred curves."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Scene Setup ---
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        # Initial scene rect, will be updated in resizeEvent
        self.setSceneRect(0, 0, self.width(), self.height())

        # --- View Setup ---
        self.setFrameShape(QFrame.NoFrame) # <--- REMOVE DEFAULT BORDER
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(DARK_BG_COLOR)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

        # --- Animation Control ---
        self.curves = [] # Holds CurveItem instances
        self.max_curves = 12 # Slightly increased density
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.last_curve_time = 0
        self.curve_interval = 750 # ms, slightly faster generation

        # --- Fade In/Out (Using Opacity Effect on the Viewport) ---
        self.opacity_effect = QGraphicsOpacityEffect(self)
        # Apply effect to viewport() for content fade without affecting potential parent widget borders
        self.viewport().setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(800)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation_active = False

    def _create_curve_path(self):
        """Generates the QPainterPath for a new curve."""
        path = QPainterPath()
        # Use sceneRect dimensions which are updated on resize
        w, h = self.sceneRect().width(), self.sceneRect().height()
        if w <= 0 or h <= 0: # Avoid division by zero if view not yet sized
             return path

        edge_margin = 70
        side_choice = random.randint(0, 3)

        # Start point generation (same as before)
        if side_choice == 0: # Top
            start_x = random.uniform(edge_margin, w - edge_margin)
            start_y = random.uniform(-edge_margin, edge_margin)
        elif side_choice == 1: # Right
            start_x = random.uniform(w - edge_margin, w + edge_margin)
            start_y = random.uniform(edge_margin, h - edge_margin)
        elif side_choice == 2: # Bottom
            start_x = random.uniform(edge_margin, w - edge_margin)
            start_y = random.uniform(h - edge_margin, h + edge_margin)
        else: # Left
            start_x = random.uniform(-edge_margin, edge_margin)
            start_y = random.uniform(edge_margin, h - edge_margin)

        path.moveTo(start_x, start_y)

        num_segments = random.randint(3, 5)
        # Ensure segment_length is positive
        segment_length = max(10.0, min(w, h) / (num_segments * 0.7))
        prev_angle = random.uniform(0, 2 * math.pi)
        prev_point = QPointF(start_x, start_y)

        # Cubic Bezier generation (same as before)
        for _ in range(num_segments):
            angle_change = random.uniform(-math.pi / 7, math.pi / 7)
            current_angle = prev_angle + angle_change
            distance = segment_length * random.uniform(0.8, 1.2)

            end_x = prev_point.x() + math.cos(current_angle) * distance
            end_y = prev_point.y() + math.sin(current_angle) * distance
            end_point = QPointF(end_x, end_y)

            ctrl_dist1 = distance * random.uniform(0.2, 0.5)
            ctrl_dist2 = distance * random.uniform(0.5, 0.8)
            angle_offset1 = random.uniform(-math.pi / 12, math.pi / 12)
            angle_offset2 = random.uniform(-math.pi / 12, math.pi / 12)

            ctrl1_x = prev_point.x() + math.cos(prev_angle + angle_offset1) * ctrl_dist1
            ctrl1_y = prev_point.y() + math.sin(prev_angle + angle_offset1) * ctrl_dist1
            ctrl1 = QPointF(ctrl1_x, ctrl1_y)

            ctrl2_x = end_point.x() - math.cos(current_angle + angle_offset2) * (distance - ctrl_dist2)
            ctrl2_y = end_point.y() - math.sin(current_angle + angle_offset2) * (distance - ctrl_dist2)
            ctrl2 = QPointF(ctrl2_x, ctrl2_y)

            path.cubicTo(ctrl1, ctrl2, end_point)

            prev_point = end_point
            prev_angle = current_angle

        return path


    def start_animation(self):
        """Start the fluid animation with fade-in effect."""
        if self.animation_active:
            return
        self.animation_active = True
        self.animation_timer.start(16) # Target ~60fps

        # Clear scene and list immediately before starting
        self.scene.clear() # Removes all items from the scene
        self.curves.clear() # Clears the Python list holding references
        self.last_curve_time = time.time() * 1000 # Reset generation timer

        # Fade in the viewport
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.opacity_effect.opacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def stop_animation(self):
        """Stop the animation with fade-out effect."""
        if not self.animation_active and self.fade_animation.state() != QPropertyAnimation.Running:
             return

        self.animation_active = False # Prevent new curves

        # Fade out the viewport
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.opacity_effect.opacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()

        # Connect safely to _complete_stop
        connection = lambda: self._complete_stop(connection)
        try:
             self.fade_animation.finished.disconnect()
        except TypeError:
             pass
        self.fade_animation.finished.connect(connection)

    def _complete_stop(self, connection_lambda):
        """Complete the animation stop after fade-out completes."""
        if self.fade_animation.endValue() == 0: # Only if fading out
            self.animation_timer.stop()
            # Ensure scene and list are cleared after fade out finishes
            self.scene.clear()
            self.curves.clear()
            # print("Animation Stopped and Cleared")

        try:
            self.fade_animation.finished.disconnect(connection_lambda)
        except TypeError:
            pass

    def update_animation(self):
        """Update the animation state: add curves, update items."""
        current_time = time.time() * 1000

        # Add new curves periodically
        if self.animation_active and len(self.curves) < self.max_curves and \
           current_time - self.last_curve_time > self.curve_interval:
            new_full_path = self._create_curve_path()
            # Only add if path is valid (has elements)
            if not new_full_path.isEmpty():
                curve_item = CurveItem(new_full_path, self.sceneRect().width(), self.sceneRect().height())
                self.scene.addItem(curve_item)
                self.curves.append(curve_item)
                self.last_curve_time = current_time

        # Update existing curves and remove dead ones
        alive_curves = []
        items_to_remove = []
        for curve in self.curves:
            if curve.update_item():
                alive_curves.append(curve)
            else:
                items_to_remove.append(curve)

        # Remove dead items from the scene *after* iterating
        for item in items_to_remove:
             # Check if item is still in the scene before removing (safety check)
             if item.scene() == self.scene:
                  self.scene.removeItem(item)

        self.curves = alive_curves
        # Scene handles repainting efficiently based on item changes


    def resizeEvent(self, event):
        """Handle view resize: update scene rect and fit view."""
        super().resizeEvent(event)
        # Update the scene rectangle to match the new view size
        new_rect = QRectF(0, 0, event.size().width(), event.size().height())
        self.setSceneRect(new_rect)
        # Fit the scene content within the view without scrollbars
        self.fitInView(new_rect, Qt.IgnoreAspectRatio) # Stretch to fill