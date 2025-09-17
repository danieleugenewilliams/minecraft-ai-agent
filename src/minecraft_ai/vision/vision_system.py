"""
Vision analysis module for Minecraft AI agent.
Handles screen capture and object detection.
"""
import mss
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VisionResult:
    """Result of vision analysis."""
    total_coverage: float
    region_coverage: Dict[str, float]
    features_detected: List[str]
    confidence: float


class ScreenCapture:
    """Handles screen capture functionality."""
    
    def __init__(self, monitor_index: int = 1):
        self.monitor_index = monitor_index
        self.sct = mss.mss()
    
    def capture(self) -> Optional[Image.Image]:
        """Capture the current screen."""
        try:
            monitor = self.sct.monitors[self.monitor_index]
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            print(f"Screen capture failed: {e}")
            return None


class FeatureDetector:
    """Detects features in captured images."""
    
    # Water color ranges (RGB)
    WATER_COLORS = [
        [(30, 100, 150), (100, 180, 255)],     # Light blue water
        [(20, 60, 120), (80, 120, 200)],       # Deeper blue water
        [(60, 140, 180), (120, 200, 255)],     # Bright water surface
    ]
    
    # Tree color ranges (RGB)
    TREE_COLORS = [
        [(20, 80, 20), (100, 180, 100)],       # Green leaves
        [(40, 120, 40), (120, 200, 120)],      # Bright green foliage
        [(60, 100, 30), (120, 160, 80)],       # Yellowish green
        [(80, 60, 30), (140, 120, 80)],        # Brown tree trunks
    ]
    
    def __init__(self):
        pass
    
    def detect_water(self, img: Image.Image) -> VisionResult:
        """Detect water in the image."""
        return self._detect_feature(img, self.WATER_COLORS, "water")
    
    def detect_trees(self, img: Image.Image) -> VisionResult:
        """Detect trees in the image."""
        return self._detect_feature(img, self.TREE_COLORS, "tree")
    
    def _detect_feature(self, img: Image.Image, color_ranges: List[List], feature_type: str) -> VisionResult:
        """Generic feature detection using color ranges."""
        img_array = np.array(img)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        
        # Calculate total coverage
        total_coverage = 0
        for lower, upper in color_ranges:
            mask = np.all((img_array >= lower) & (img_array <= upper), axis=2)
            total_coverage += np.sum(mask) / total_pixels
        
        # Calculate region coverage
        region_coverage = self._calculate_region_coverage(img_array, color_ranges)
        
        # Determine confidence and features
        confidence = min(total_coverage * 10, 1.0)  # Scale coverage to confidence
        features_detected = []
        if total_coverage > 0.01:
            features_detected.append(feature_type)
        
        return VisionResult(
            total_coverage=total_coverage,
            region_coverage=region_coverage,
            features_detected=features_detected,
            confidence=confidence
        )
    
    def _calculate_region_coverage(self, img_array: np.ndarray, color_ranges: List[List]) -> Dict[str, float]:
        """Calculate coverage for different screen regions."""
        height, width = img_array.shape[:2]
        
        regions = {
            'left': img_array[:, :width//3],
            'center': img_array[:, width//3:2*width//3],
            'right': img_array[:, 2*width//3:],
            'top': img_array[:height//3, :],
            'middle': img_array[height//3:2*height//3, :],
            'bottom': img_array[2*height//3:, :],
        }
        
        region_coverage = {}
        for region_name, region_img in regions.items():
            region_pixels = region_img.shape[0] * region_img.shape[1]
            coverage = 0
            for lower, upper in color_ranges:
                mask = np.all((region_img >= lower) & (region_img <= upper), axis=2)
                coverage += np.sum(mask) / region_pixels
            region_coverage[region_name] = coverage
        
        return region_coverage


class VisionSystem:
    """Main vision system combining capture and detection."""
    
    def __init__(self, monitor_index: int = 1):
        self.capture = ScreenCapture(monitor_index)
        self.detector = FeatureDetector()
    
    def analyze_for_water(self) -> Optional[VisionResult]:
        """Capture screen and analyze for water."""
        img = self.capture.capture()
        if img is None:
            return None
        return self.detector.detect_water(img)
    
    def analyze_for_trees(self) -> Optional[VisionResult]:
        """Capture screen and analyze for trees."""
        img = self.capture.capture()
        if img is None:
            return None
        return self.detector.detect_trees(img)
    
    def analyze_for_feature(self, feature_type: str) -> Optional[VisionResult]:
        """Analyze for a specific feature type."""
        if feature_type.lower() == "water":
            return self.analyze_for_water()
        elif feature_type.lower() == "tree":
            return self.analyze_for_trees()
        else:
            return None