"""
Screen capture and vision processing for Minecraft AI Agent
"""

import time
import numpy as np
from typing import Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import mss
    from PIL import Image
    import cv2
except ImportError:
    # Graceful fallback for when dependencies aren't installed
    mss = None
    Image = None
    cv2 = None


class ScreenCapture(ABC):
    """Abstract base class for screen capture"""
    
    @abstractmethod
    def capture(self, region: Optional[Dict[str, int]] = None) -> np.ndarray:
        """Capture screen region as numpy array"""
        pass
    
    @abstractmethod
    def find_window(self, window_title: str) -> Optional[Dict[str, int]]:
        """Find window bounds by title"""
        pass


class MSSSScreenCapture(ScreenCapture):
    """Screen capture using MSS library for fast screenshots"""
    
    def __init__(self, monitor_index: int = 0):
        if mss is None:
            raise ImportError("mss is required for screen capture")
        
        self.sct = mss.mss()
        self.monitor_index = monitor_index
        self.monitor = self.sct.monitors[monitor_index + 1]  # 0 is all monitors
    
    def capture(self, region: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Capture screen region as numpy array
        
        Args:
            region: Dict with 'left', 'top', 'width', 'height' keys
                   If None, captures entire monitor
        
        Returns:
            Captured image as numpy array (BGR format)
        """
        if region is None:
            capture_region = self.monitor
        else:
            capture_region = {
                'left': region['left'],
                'top': region['top'],
                'width': region['width'],
                'height': region['height']
            }
        
        # Capture screenshot
        screenshot = self.sct.grab(capture_region)
        
        # Convert to numpy array
        img_array = np.array(screenshot)
        
        # Convert BGRA to BGR (remove alpha channel)
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        
        # MSS returns BGR, OpenCV expects BGR, so we're good
        return img_array
    
    def find_window(self, window_title: str) -> Optional[Dict[str, int]]:
        """
        Find window bounds by title (basic implementation)
        Note: This is a simplified version. Real implementation would
        need platform-specific window management APIs.
        """
        # For now, return None - would need platform-specific implementation
        return None
    
    def get_monitor_info(self) -> Dict[str, Any]:
        """Get monitor information"""
        return {
            'width': self.monitor['width'],
            'height': self.monitor['height'],
            'left': self.monitor['left'],
            'top': self.monitor['top']
        }


class ImageProcessor:
    """Image processing utilities for Minecraft vision"""
    
    @staticmethod
    def resize_image(image: np.ndarray, scale: float) -> np.ndarray:
        """Resize image by scale factor"""
        if cv2 is None:
            raise ImportError("opencv-python is required for image processing")
        
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale), int(width * scale)
        return cv2.resize(image, (new_width, new_height))
    
    @staticmethod
    def convert_color_space(image: np.ndarray, target: str = 'RGB') -> np.ndarray:
        """Convert image color space"""
        if cv2 is None:
            raise ImportError("opencv-python is required for image processing")
        
        if target == 'RGB':
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif target == 'HSV':
            return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        elif target == 'GRAY':
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            return image
    
    @staticmethod
    def save_image(image: np.ndarray, filepath: str) -> None:
        """Save image to file"""
        if cv2 is None:
            raise ImportError("opencv-python is required for image processing")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(filepath, image)
    
    @staticmethod
    def detect_colors(image: np.ndarray, color_ranges: Dict[str, Tuple]) -> Dict[str, np.ndarray]:
        """
        Detect specific colors in image
        
        Args:
            image: Input image (BGR format)
            color_ranges: Dict mapping color names to (lower, upper) HSV ranges
        
        Returns:
            Dict mapping color names to binary masks
        """
        if cv2 is None:
            raise ImportError("opencv-python is required for image processing")
        
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        masks = {}
        
        for color_name, (lower, upper) in color_ranges.items():
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv_image, lower_np, upper_np)
            masks[color_name] = mask
        
        return masks


class MinecraftVision:
    """High-level vision system for Minecraft"""
    
    def __init__(self, screen_capture: ScreenCapture, 
                 image_scale: float = 0.5,
                 color_space: str = 'RGB'):
        self.screen_capture = screen_capture
        self.image_scale = image_scale
        self.color_space = color_space
        self.processor = ImageProcessor()
        
        # Define Minecraft-specific color ranges (HSV) - updated for real Minecraft
        self.minecraft_colors = {
            'grass': ((35, 30, 30), (85, 255, 255)),     # Broader green range for grass blocks
            'leaves': ((30, 25, 25), (90, 255, 255)),    # Tree leaves (green)
            'wood': ((8, 50, 50), (30, 255, 200)),       # Tree trunks/logs (brown/orange)
            'sky': ((90, 20, 80), (130, 255, 255)),      # Sky/night sky (blue range)
            'dirt': ((0, 30, 30), (25, 255, 180)),       # Dirt blocks (brown)
            'stone': ((0, 0, 40), (180, 25, 120)),       # Stone/gray blocks
        }
    
    def get_current_view(self, region: Optional[Dict[str, int]] = None) -> np.ndarray:
        """Get current processed view of Minecraft"""
        # Capture screen
        raw_image = self.screen_capture.capture(region)
        
        # Resize if needed
        if self.image_scale != 1.0:
            raw_image = self.processor.resize_image(raw_image, self.image_scale)
        
        # Convert color space
        processed_image = self.processor.convert_color_space(raw_image, self.color_space)
        
        return processed_image
    
    def analyze_environment(self, region: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Analyze current Minecraft environment"""
        image = self.get_current_view(region)
        
        # Convert back to BGR for color detection
        if self.color_space == 'RGB':
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if cv2 else image
        else:
            bgr_image = image
        
        # Detect Minecraft elements
        color_masks = self.processor.detect_colors(bgr_image, self.minecraft_colors)
        
        # Calculate coverage percentages
        total_pixels = image.shape[0] * image.shape[1]
        coverage = {}
        for color_name, mask in color_masks.items():
            white_pixels = np.sum(mask == 255)
            coverage[color_name] = white_pixels / total_pixels
        
        return {
            'image_shape': image.shape,
            'color_coverage': coverage,
            'timestamp': time.time()
        }


def create_screen_capture(capture_type: str = 'mss', **kwargs) -> ScreenCapture:
    """Factory function to create screen capture instance"""
    if capture_type == 'mss':
        return MSSSScreenCapture(**kwargs)
    else:
        raise ValueError(f"Unknown capture type: {capture_type}")