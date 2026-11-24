"""
Hardware controller for BioGuard.

Manages LEDs, buzzer, and optional LCD display with safe cleanup on exit.
"""

from typing import Optional, Tuple
import logging

from gpiozero import OutputDevice, PWMOutputDevice
import importlib

logger = logging.getLogger(__name__)


class HardwareController:
    """
    Hardware controller managing GPIO outputs.

    Manages:
    - Green LED (GPIO 17) - Compliant indicator
    - Red LED (GPIO 22) - Violation indicator
    - Passive Buzzer (GPIO 18) - Audio alert
    - 16x2 I2C LCD (optional) - Status display

    All hardware is properly cleaned up on exit.
    """

    def __init__(self, enable_lcd: bool = False, lcd_address: int = 0x27,
                 lcd_cols: int = 16, lcd_rows: int = 2):
        """
        Initialize hardware controller.

        Args:
            enable_lcd: Whether to enable LCD output
            lcd_address: I2C address of LCD (PCF8574 backpack)
            lcd_cols: Number of LCD columns
            lcd_rows: Number of LCD rows
        """
        # LED devices - initially off
        self.green_led = OutputDevice(17, active_high=True, initial_value=False)
        self.red_led = OutputDevice(22, active_high=True, initial_value=False)

        # Buzzer - PWM output for tone generation
        self.buzzer = PWMOutputDevice(18, frequency=1000, initial_value=0)

        # LCD (optional)
        self.lcd = None
        self.enable_lcd = enable_lcd

        if enable_lcd:
            self._init_lcd(lcd_address, lcd_cols, lcd_rows)

        logger.info("Hardware controller initialized")

    def _init_lcd(self, address: int, cols: int, rows: int) -> None:
        """
        Initialize LCD with safe fallback.

        Args:
            address: I2C address of PCF8574 backpack
            cols: Number of columns
            rows: Number of rows
        """
        try:
            # Import RPLCD here to allow operation without it
            from RPLCD.i2c import CharLCD

            self.lcd = CharLCD(
                i2c_expander='PCF8574',
                address=address,
                cols=cols,
                rows=rows,
                charmap='A02',
                auto_linebreaks=True
            )
            self.clear_lcd()
            self.write_lcd("BioGuard Ready")
            logger.info(f"LCD initialized at address 0x{address:02X}")
        except Exception as e:
            logger.warning(f"LCD initialization failed: {e}")
            logger.warning("Continuing without LCD output")
            self.enable_lcd = False
            self.lcd = None

    def indicate_compliant(self) -> None:
        """Indicate compliance status with green LED."""
        self.green_led.on()
        self.red_led.off()

    def indicate_violation(self) -> None:
        """Indicate violation status with red LED."""
        self.green_led.off()
        self.red_led.on()

    def indicate_neutral(self) -> None:
        """Turn off both LEDs (neutral state)."""
        self.green_led.off()
        self.red_led.off()

    def alert(self, duration: float = 0.5, frequency: float = 2000) -> None:
        """
        Emit an audio alert via the buzzer.

        Args:
            duration: Alert duration in seconds
            frequency: Alert frequency in Hz
        """
        try:
            self.buzzer.frequency = frequency
            self.buzzer.value = 0.5  # 50% duty cycle
        except Exception as e:
            logger.warning(f"Buzzer alert failed: {e}")

    def alert_stop(self) -> None:
        """Immediately stop the buzzer."""
        self.buzzer.value = 0

    def clear_lcd(self) -> None:
        """Clear the LCD display."""
        if self.lcd:
            self.lcd.clear()

    def write_lcd(self, message: str, line: int = 0) -> None:
        """
        Write a message to the LCD.

        Args:
            message: Text to display
            line: Line number (0-indexed)
        """
        if self.lcd:
            try:
                if line == 0:
                    self.lcd.cursor_pos = (0, 0)
                else:
                    self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(message[:self.lcd.cols])
            except Exception as e:
                logger.warning(f"LCD write failed: {e}")

    def update_lcd(self, status_line1: str, status_line2: str = "") -> None:
        """
        Update LCD with two lines of status.

        Args:
            status_line1: First line text
            status_line2: Second line text (optional)
        """
        if self.enable_lcd and self.lcd:
            self.clear_lcd()
            self.write_lcd(status_line1[:16], 0)
            if status_line2:
                self.write_lcd(status_line2[:16], 1)

    def cleanup(self) -> None:
        """
        Clean up all hardware resources.

        Should be called on program exit (KeyboardInterrupt or normal shutdown).
        """
        logger.info("Cleaning up hardware resources")

        # Turn off LEDs
        self.green_led.off()
        self.red_led.off()

        # Silence buzzer
        self.buzzer.value = 0

        # Close LCD if open
        if self.lcd:
            try:
                self.lcd.clear()
            except Exception as e:
                logger.warning(f"LCD cleanup warning: {e}")

        # Close device handles
        self.green_led.close()
        self.red_led.close()
        self.buzzer.close()

        logger.info("Hardware cleanup complete")


def create_hardware_controller(**kwargs) -> HardwareController:
    """
    Factory function to create hardware controller.

    Args:
        **kwargs: Arguments passed to HardwareController constructor

    Returns:
        HardwareController instance
    """
    return HardwareController(**kwargs)