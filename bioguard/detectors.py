"""
Color detection modules for BioGuard.

Provides pluggable HSV color detectors for compliance monitoring.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional
import logging

import cv2
import numpy as np

from .config import Config, HSVConfig

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """
    Result of a detection operation.

    Attributes:
        is_compliant: True if target color detected (compliance met)
        annotated_frame: Frame with status overlay drawn
        pixel_count: Number of pixels matching target color
        bounding_box: Optional (x, y, w, h) of detected region
    """
    is_compliant: bool
    annotated_frame: np.ndarray
    pixel_count: int
    bounding_box: Optional[Tuple[int, int, int, int]] = None


class ColorDetector(ABC):
    """Abstract base class for color detectors."""

    def __init__(self, config: Config):
        """
        Initialize detector with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    @abstractmethod
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect target color in frame.

        Args:
            frame: BGR image frame from camera

        Returns:
            DetectionResult with compliance status and annotated frame
        """
        pass

    def _create_mask(self, frame_bgr: np.ndarray,
                     lower: Tuple[int, int, int],
                     upper: Tuple[int, int, int]) -> np.ndarray:
        """
        Create HSV color mask from BGR frame.

        Args:
            frame_bgr: Input frame in BGR color space
            lower: Lower HSV bounds
            upper: Upper HSV bounds

        Returns:
            Binary mask where target color pixels are white
        """
        # Convert BGR to HSV
        frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

        # Create mask
        mask = cv2.inRange(frame_hsv, lower, upper)

        # Morphological operations to clean up noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def _draw_status_overlay(self, frame: np.ndarray,
                              is_compliant: bool,
                              pixel_count: int,
                              label: str = "") -> np.ndarray:
        """
        Draw status overlay on frame.

        Args:
            frame: Frame to annotate
            is_compliant: Compliance status
            pixel_count: Number of detected pixels
            label: Optional custom label

        Returns:
            Annotated frame
        """
        annotated = frame.copy()

        # Status text
        status_text = "COMPLIANT" if is_compliant else "VIOLATION"
        color = (0, 255, 0) if is_compliant else (0, 0, 255)  # Green or Red

        # Draw status background
        cv2.rectangle(annotated, (5, 5), (300, 55), (0, 0, 0), -1)
        cv2.putText(annotated, status_text, (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

        # Draw pixel count
        count_text = f"Pixels: {pixel_count}"
        cv2.putText(annotated, count_text, (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Draw mode label if provided
        if label:
            cv2.putText(annotated, label, (10, annotated.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        return annotated


class WhiteDetector(ColorDetector):
    """
    White/Lab Coat detector.

    Detects high-value, low-saturation colors typical of white lab coats
    and white protective gear.
    """

    def __init__(self, config: Config):
        """Initialize white detector."""
        super().__init__(config)

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect white color in frame.

        Args:
            frame: BGR image frame from camera

        Returns:
            DetectionResult with compliance status and annotated frame
        """
        # Get HSV thresholds for white detection
        lower = self.config.hsv.white_lower
        upper = self.config.hsv.white_upper
        min_area = self.config.hsv.min_area_white

        # Create mask
        mask = self._create_mask(frame, lower, upper)

        # Count white pixels
        pixel_count = int(cv2.countNonZero(mask))

        # Check if compliant
        is_compliant = pixel_count >= min_area

        # Find bounding box of largest contour
        bounding_box = None
        if is_compliant:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                bounding_box = (x, y, w, h)
                # Draw bounding box on frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Draw overlay
        annotated = self._draw_status_overlay(frame, is_compliant, pixel_count, "Mode: White/Lab Coat")

        return DetectionResult(
            is_compliant=is_compliant,
            annotated_frame=annotated,
            pixel_count=pixel_count,
            bounding_box=bounding_box
        )


class YellowDetector(ColorDetector):
    """
    Yellow spectrum detector.

    Detects yellow colors covering pale lemon through deep gold/mustard.
    Broad HSV range for maximum yellow coverage.
    """

    def __init__(self, config: Config):
        """Initialize yellow detector."""
        super().__init__(config)

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect yellow color in frame.

        Args:
            frame: BGR image frame from camera

        Returns:
            DetectionResult with compliance status and annotated frame
        """
        # Get HSV thresholds for yellow detection
        lower = self.config.hsv.yellow_lower
        upper = self.config.hsv.yellow_upper
        min_area = self.config.hsv.min_area_yellow

        # Create mask
        mask = self._create_mask(frame, lower, upper)

        # Count yellow pixels
        pixel_count = int(cv2.countNonZero(mask))

        # Check if compliant (yellow detected = compliant)
        is_compliant = pixel_count >= min_area

        # Find bounding box of largest contour
        bounding_box = None
        if is_compliant:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                bounding_box = (x, y, w, h)
                # Draw bounding box on frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

        # Draw overlay
        annotated = self._draw_status_overlay(frame, is_compliant, pixel_count, "Mode: Yellow Spectrum")

        return DetectionResult(
            is_compliant=is_compliant,
            annotated_frame=annotated,
            pixel_count=pixel_count,
            bounding_box=bounding_box
        )


def create_detector(detector_type: str, config: Config) -> ColorDetector:
    """
    Factory function to create appropriate detector.

    Args:
        detector_type: Type of detector ('white' or 'yellow')
        config: Application configuration

    Returns:
        ColorDetector instance

    Raises:
        ValueError: If detector_type is unknown
    """
    if detector_type == "white":
        return WhiteDetector(config)
    elif detector_type == "yellow":
        return YellowDetector(config)
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")