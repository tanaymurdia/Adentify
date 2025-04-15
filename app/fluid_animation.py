"""
Fluid Animation for Basketball Classifier App
This file contains a fluid animation widget for the app when capture is stopped or not yet started.
"""

import math
import random
import time
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QBrush, QColor, QPainterPath, QRadialGradient
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect

# Import color constants
from style import RED_COLOR, DARK_BG_COLOR

class Particle:
    """Represents a single particle in the fluid animation"""
    def __init__(self, x, y, size, opacity=1.0):
        self.x = x
        self.y = y
        self.size = size
        self.base_size = size
        self.dx = random.uniform(-1, 1) * 0.5
        self.dy = random.uniform(-1, 1) * 0.5
        self.color = QColor(RED_COLOR)
        self.opacity = opacity
        self.life = random.uniform(0.8, 1.0)
        self.fade_speed = random.uniform(0.001, 0.003)
        self.pulse_phase = random.uniform(0, 2 * math.pi)
        self.pulse_speed = random.uniform(0.02, 0.05)

    def update(self):
        # Update position
        self.x += self.dx
        self.y += self.dy
        
        # Pulsating size effect
        pulse = math.sin(self.pulse_phase)
        self.size = self.base_size * (1 + 0.2 * pulse)
        self.pulse_phase += self.pulse_speed
        
        # Slowly decrease life
        self.life -= self.fade_speed
        self.opacity = max(0, self.life)
        
        # Gradually slow down
        self.dx *= 0.99
        self.dy *= 0.99
        
        return self.life > 0

    def draw(self, painter, width, height):
        # Wrap around screen edges for seamless animation
        x = self.x % width
        y = self.y % height
        
        # Set opacity
        color = QColor(self.color)
        color.setAlphaF(self.opacity)
        
        # Create gradient for each particle
        gradient = QRadialGradient(x, y, self.size)
        gradient.setColorAt(0, color)
        color.setAlphaF(0)
        gradient.setColorAt(1, color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(x, y), self.size, self.size)


class FluidAnimation(QWidget):
    """Fluid animation widget that creates flowing red particles"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.max_particles = 40
        self.particle_timer = QTimer(self)
        self.particle_timer.timeout.connect(self.update_animation)
        self.last_particle_time = 0
        self.particle_interval = 100  # ms
        self.animation_active = False
        
        # Create opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animation for fade in/out
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(800)  # 800ms for fade
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def start_animation(self):
        """Start the fluid animation with fade-in effect"""
        self.animation_active = True
        self.particle_timer.start(16)  # ~60fps
        
        # Fade in
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
    def stop_animation(self):
        """Stop the animation with fade-out effect"""
        # Fade out
        self.fade_animation.stop()
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()
        
        # Connect the animation's finished signal to actually stop the timer
        self.fade_animation.finished.connect(self._complete_stop)
    
    def _complete_stop(self):
        """Complete the animation stop after fade-out completes"""
        if self.fade_animation.direction() == QPropertyAnimation.Forward:
            return  # Don't stop if we're fading in
            
        self.animation_active = False
        self.particle_timer.stop()
        self.particles.clear()
        
        # Disconnect to avoid multiple connections
        try:
            self.fade_animation.finished.disconnect(self._complete_stop)
        except TypeError:
            pass  # Already disconnected
        
    def update_animation(self):
        """Update the animation state"""
        if not self.animation_active:
            return
            
        current_time = time.time() * 1000
        if len(self.particles) < self.max_particles and current_time - self.last_particle_time > self.particle_interval:
            # Add new particles
            for _ in range(2):
                x = random.uniform(0, self.width())
                y = random.uniform(0, self.height())
                size = random.uniform(30, 80)
                self.particles.append(Particle(x, y, size))
            self.last_particle_time = current_time
            
        # Update existing particles
        self.particles = [p for p in self.particles if p.update()]
        
        # Redraw
        self.update()

    def paintEvent(self, event):
        """Paint the animation"""
        if not self.animation_active and not self.fade_animation.state() == QPropertyAnimation.Running:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Clear background (transparent)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 0))
        
        # Draw all particles
        for particle in self.particles:
            particle.draw(painter, self.width(), self.height())
        
        # Draw a subtle text label
        if hasattr(self, 'label_opacity'):
            painter.setOpacity(self.label_opacity)
            painter.setPen(QColor(RED_COLOR))
            painter.setFont(self.font())
            painter.drawText(event.rect(), Qt.AlignCenter, "Capture Stopped") 