"""
Centralized configuration for BioGuard.

All GPIO pins use BCM numbering. HSV values are for OpenCV's HSV color space.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional


@dataclass
class GPIOConfig:
    """GPIO pin configuration (BCM numbering)."""

    # LED pins
    green_led_pin: int = 17  # GPIO 17 - Compliant (Green LED)
    red_led_pin: int = 22    # GPIO 22 - Violation (Red LED)

    # Buzzer pin
    buzzer_pin: int = 18     # GPIO 18 - Passive Buzzer (PWM)

    # I2C pins for LCD (hardware default on Raspberry Pi)
    i2c_sda_pin: int = 2     # GPIO 2 - I2C SDA
    i2c_scl_pin: int = 3     # GPIO 3 - I2C SCL


@dataclass
class LCDConfig:
    """LCD display configuration."""

    enabled: bool = True           # Enable/disable LCD functionality
    address: int = 0x27            # PCF8574 I2C address
    cols: int = 16                 # LCD columns
    rows: int = 2                  # LCD rows
    charmap: str = "A02"            # Character map for PCF8574


@dataclass
class CameraConfig:
    """Camera configuration."""

    width: int = 640                 # Video frame width
    height: int = 480                # Video frame height
    framerate: int = 30              # Target framerate
    format: str = "RGB888"           # Camera output format


@dataclass
class HSVConfig:
    """HSV color detection configuration."""

    # White/Lab Coat mode - high value, low saturation
    # These colors represent lab coats/faces with white protective gear
    white_lower: Tuple[int, int, int] = (0, 0, 180)      # H=0-180, S=0-30, V=180-255
    white_upper: Tuple[int, int, int] = (180, 30, 255)

    # Yellow spectrum mode - covers pale lemon through deep gold/mustard
    yellow_lower: Tuple[int, int, int] = (15, 100, 100)  # H=15-45, S=100-255, V=100-255
    yellow_upper: Tuple[int, int, int] = (45, 255, 255)

    # Minimum pixel area threshold for detection (in pixels)
    min_area_white: int = 5000       # Minimum area for white detection
    min_area_yellow: int = 3000      # Minimum area for yellow detection


@dataclass
class FlaskConfig:
    """Flask server configuration."""

    host: str = "0.0.0.0"            # Bind to all interfaces
    port: int = 5000                 # Server port
    debug: bool = False              # Debug mode


@dataclass
class Config:
    """Main configuration container."""

    gpio: GPIOConfig = field(default_factory=GPIOConfig)
    lcd: LCDConfig = field(default_factory=LCDConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    hsv: HSVConfig = field(default_factory=HSVConfig)
    flask: FlaskConfig = field(default_factory=FlaskConfig)

    # Detection mode
    # 'white' - for lab coat compliance
    # 'yellow' - for detecting yellow caution items
    mode: str = "white"

    @classmethod
    def from_args(cls, mode: str = "white", use_lcd: Optional[bool] = None) -> "Config":
        """
        Create config from command-line arguments.

        Args:
            mode: Detection mode ('white', 'yellow', 'yellow-lcd')
            use_lcd: Override LCD enable flag (None = auto-detect from mode)

        Returns:
            Configured Config instance
        """
        config = cls()
        config.mode = mode

        if use_lcd is not None:
            config.lcd.enabled = use_lcd
        elif mode == "yellow-lcd":
            config.lcd.enabled = True
        else:
            config.lcd.enabled = False

        return config

    def get_detector_type(self) -> str:
        """Get the detector type based on mode."""
        if "lcd" in self.mode:
            return "yellow"
        if self.mode == "yellow":
            return "yellow"
        return "white"