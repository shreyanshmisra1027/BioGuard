#!/usr/bin/env python3
"""
BioGuard Yellow + LCD Detector

Full integrated pipeline combining broad yellow detection, Flask live stream,
LEDs/buzzer, and 16x2 I2C LCD (0x27) two-line status updates.

Run: python yellow_lcd_detector.py

Controls:
- Green LED: ON when yellow detected (compliant)
- Red LED: ON when no yellow detected (violation)
- Buzzer: Alert on violation
- LCD: Two-line status display showing mode and compliance
- Stream available at http://<pi-ip>:5000
"""

import sys
import signal
import logging
import cv2
import numpy as np
from picamera2 import Picamera2

from bioguard.config import Config
from bioguard.detectors import YellowDetector, create_detector, DetectionResult
from bioguard.hardware import HardwareController
from bioguard.streamer import MJPEGStreamer, create_app, encode_frame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
picam2: Picamera2 = None
hardware: HardwareController = None
detector: YellowDetector = None
streamer: MJPEGStreamer = None
running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    logger.info("Shutdown signal received")
    running = False


def init_hardware(config: Config):
    """Initialize hardware controller with LCD."""
    global hardware
    try:
        hardware = HardwareController(enable_lcd=True, lcd_address=0x27,
                                       lcd_cols=16, lcd_rows=2)
        logger.info("Hardware initialized with LCD")
    except Exception as e:
        logger.error(f"Failed to initialize hardware: {e}")
        raise


def init_camera() -> Picamera2:
    """Initialize Picamera2."""
    global picam2
    picam2 = Picamera2()
    config_cam = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config_cam)
    picam2.start()
    logger.info("Camera started")
    return picam2


def init_detector(config: Config) -> YellowDetector:
    """Initialize color detector."""
    global detector
    detector = YellowDetector(config)
    logger.info("Yellow detector initialized")


def init_streamer(config: Config) -> MJPEGStreamer:
    """Initialize MJPEG streamer with hardware status updates."""
    app = create_app()

    # LCD update function
    def update_lcd(status_line1: str, status_line2: str = "") -> None:
        if hardware and hardware.lcd:
            hardware.update_lcd(status_line1, status_line2)

    def frame_generator():
        """Generate frames from camera."""
        while running:
            try:
                # Capture frame from camera
                frame = picam2.capture_array()

                # Convert RGB to BGR for OpenCV (CRITICAL for correct color detection)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Run detection
                result: DetectionResult = detector.detect(frame_bgr)

                # Update LCD
                if result.is_compliant:
                    update_lcd("COMPLIANT", "Yellow Detected")
                    hardware.indicate_compliant()
                else:
                    update_lcd("VIOLATION", "No Yellow")
                    hardware.indicate_violation()
                    hardware.alert(frequency=800, duration=0.3)

                # Encode to JPEG
                jpeg_bytes = encode_frame(result.annotated_frame)

                # Return JPEG bytes
                return jpeg_bytes
            except Exception as e:
                logger.error(f"Frame generation error: {e}")
                return None

    def status_provider():
        """Provide current status."""
        return {
            "mode": "yellow-lcd",
            "is_compliant": detector is not None,
            "config_mode": config.mode
        }

    return MJPEGStreamer(app, frame_generator, status_provider)


def main():
    """Main entry point."""
    global running

    # Parse config
    config = Config.from_args(mode="yellow-lcd", use_lcd=True)

    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize hardware (with LCD)
        init_hardware(config)

        # Initialize camera
        init_camera()

        # Initialize detector
        init_detector(config)

        # Initialize streamer
        streamer = init_streamer(config)

        # Run streamer
        logger.info("Starting yellow LCD detector streamer on http://0.0.0.0:5000")
        streamer.run(host="0.0.0.0", port=5000, debug=False)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        # Clean up
        logger.info("Cleaning up resources")
        running = False

        if picam2:
            picam2.stop()
            picam2.close()

        if hardware:
            hardware.cleanup()


if __name__ == '__main__':
    main()