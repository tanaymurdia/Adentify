"""
Basketball Classifier - Audio Control Functionality
Handles system volume control with smooth transitions based on basketball detection
"""
import time
import threading
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeController:
    def __init__(self):
        # Initialize the volume controller
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
        
        # Store volume states
        self.original_volume = self.get_volume()
        self.target_volume = self.original_volume
        self.current_volume = self.original_volume
        
        # User's preferred basketball volume (dynamically tracked)
        self.user_basketball_volume = self.original_volume
        
        # Configuration
        self.volume_reduction_factor = 0.2  # Reduce to 20% when not basketball (80% reduction)
        self.fade_duration = 1.0  # Seconds for fade transition
        self.fade_steps = 20  # Number of steps in a fade transition
        self.volume_check_interval = 0.5  # Check for user volume changes more frequently
        
        # State tracking
        self.is_basketball = True
        self.is_transitioning = False
        self.fade_thread = None
        self.volume_monitor_thread = None
        self.running = True
        
        # Start volume monitoring thread
        self.start_volume_monitoring()
    
    def get_volume(self):
        """Get current system volume (0.0 to 1.0)"""
        try:
            # Scalar volume is from 0.0 to 1.0
            return self.volume.GetMasterVolumeLevelScalar()
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 1.0
    
    def set_volume(self, level):
        """Set system volume (0.0 to 1.0)"""
        try:
            # Ensure level is within valid range
            level = max(0.0, min(1.0, level))
            self.volume.SetMasterVolumeLevelScalar(level, None)
            self.current_volume = level
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False
    
    def start_volume_monitoring(self):
        """Start a thread to monitor volume changes made by the user"""
        self.volume_monitor_thread = threading.Thread(target=self.monitor_volume)
        self.volume_monitor_thread.daemon = True
        self.volume_monitor_thread.start()
    
    def monitor_volume(self):
        """Monitor volume changes during basketball content to adapt to user preferences"""
        last_checked_volume = self.current_volume
        
        while self.running:
            # Only track volume changes when in basketball mode and not during transitions
            if self.is_basketball and not self.is_transitioning:
                current_vol = self.get_volume()
                
                # If volume changed significantly and not by our own code
                if abs(current_vol - last_checked_volume) > 0.01:  # More sensitive to changes
                    # User changed the volume - update preferred basketball volume
                    print(f"User adjusted volume to: {current_vol:.2f}")
                    self.user_basketball_volume = current_vol
                    self.current_volume = current_vol
                
                # Even if we didn't detect a significant change, always update 
                # the user's preferred level to the current system volume
                # This ensures we capture any small incremental changes too
                self.user_basketball_volume = current_vol
                
                last_checked_volume = current_vol
            
            # Check periodically
            time.sleep(self.volume_check_interval)
    
    def fade_volume(self, start_vol, end_vol, duration, steps):
        """Smoothly fade volume from start to end"""
        self.is_transitioning = True
        
        # Calculate volume steps
        volume_steps = np.linspace(start_vol, end_vol, steps)
        step_time = duration / steps
        
        # Perform the fade
        for vol in volume_steps:
            if not self.running:
                break
            self.set_volume(vol)
            time.sleep(step_time)
        
        # Ensure we reach final volume
        if self.running:
            self.set_volume(end_vol)
        
        self.is_transitioning = False
    
    def update_classification(self, is_basketball, confidence):
        """Update volume based on classification result"""
        # Don't take any action if classification hasn't changed
        if self.is_basketball == is_basketball:
            return
        
        # Get current system volume before making changes
        current_system_volume = self.get_volume()
        
        # Print transition information
        if is_basketball:
            print(f"======= TRANSITION: NOT BASKETBALL → BASKETBALL =======")
            print(f"  Current system volume: {current_system_volume:.2f}")
            print(f"  User's basketball volume: {self.user_basketball_volume:.2f}")
            print(f"  Confidence level: {confidence:.1f}%")
        else:
            print(f"======= TRANSITION: BASKETBALL → NOT BASKETBALL =======")
            print(f"  Current system volume: {current_system_volume:.2f}")
            print(f"  Will save as user's basketball volume: {current_system_volume:.2f}")
            print(f"  Confidence level: {confidence:.1f}%")
        
        # Update state
        prev_state = self.is_basketball
        self.is_basketball = is_basketball
        
        # Calculate confidence factor (higher confidence = more dramatic changes)
        confidence_factor = min(1.0, confidence / 100.0)
        
        if is_basketball:
            # Important: Only use user_basketball_volume if we're coming from a non-basketball state
            # This prevents jumps to an old volume level when already at the user's current preference
            if not prev_state:
                print(f"Basketball detected, restoring to user volume: {self.user_basketball_volume:.2f}")
                self.target_volume = self.user_basketball_volume
            else:
                # We should never get here, but just in case - keep current volume
                print(f"Basketball already detected, maintaining current volume")
                self.target_volume = current_system_volume
        else:
            # Not basketball - capture current volume as user's preferred basketball volume
            # (only if not already in a reduced state)
            if not self.is_transitioning:
                self.user_basketball_volume = current_system_volume
                print(f"Saving user's basketball volume preference: {self.user_basketball_volume:.2f}")
            
            # Reduce volume based on confidence and user's preferred level
            # Use higher reduction factor (80% reduction = 20% of original)
            reduced_volume = self.user_basketball_volume * self.volume_reduction_factor * confidence_factor
            self.target_volume = max(reduced_volume, self.user_basketball_volume * 0.1)  # Don't go below 10% of user pref
            print(f"Not basketball, reducing volume to: {self.target_volume:.2f} (80% reduction)")
        
        # Only proceed with fade if target is different from current
        if abs(current_system_volume - self.target_volume) < 0.01:
            print(f"No volume change needed, already at {current_system_volume:.2f}")
            return
            
        # Stop existing fade if in progress
        if self.fade_thread and self.fade_thread.is_alive():
            # Let current thread finish naturally by continuing with new target
            pass
        
        print(f"Starting volume fade: {current_system_volume:.2f} → {self.target_volume:.2f}")
        
        # Start new fade from current system volume (not self.current_volume)
        # This ensures we're always starting from the actual current system state
        self.fade_thread = threading.Thread(
            target=self.fade_volume,
            args=(current_system_volume, self.target_volume, self.fade_duration, self.fade_steps)
        )
        self.fade_thread.daemon = True
        self.fade_thread.start()
    
    def restore_volume(self):
        """Restore original volume when closing the application"""
        # Set running to false to interrupt any ongoing fades
        self.running = False
        
        # Wait for any transition to complete
        if self.fade_thread and self.fade_thread.is_alive():
            self.fade_thread.join(timeout=0.5)
        
        # Reset to original volume immediately
        self.set_volume(self.original_volume)
    
    def set_fade_duration(self, seconds):
        """Configure the fade duration"""
        self.fade_duration = max(0.1, float(seconds))
    
    def set_volume_reduction(self, reduction_factor):
        """Configure the volume reduction factor (0.0-1.0)"""
        self.volume_reduction_factor = max(0.0, min(1.0, reduction_factor)) 