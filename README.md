# BioGuard - Raspberry Pi 5 Compliance Monitoring System

A modular compliance monitoring system for Raspberry Pi 5 using computer vision and hardware outputs.

## Features

- **Computer Vision**: Detects white/lab coat and yellow spectrum compliance using HSV color detection
- **Hardware Integration**: Controls Green LED (compliant), Red LED (violation), and Passive Buzzer
- **Web Interface**: MJPEG streaming server with health/status endpoints
- **LCD Display**: Optional 16x2 I2C LCD (PCF8574, 0x27) for status updates
- **Modular Design**: Clean separation of hardware, vision, streaming, and configuration

## Hardware Requirements

### Raspberry Pi 5 Setup

1. **Enable I2C Interface**:
   ```bash
   sudo raspi-config
   ```
   Navigate to Interface Options > I2C and enable it.

2. **Verify I2C Address**:
   ```bash
   sudo i2cdetect -y 1
   ```
   You should see `27` at address `0x27` if using the LCD.

### Installation

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv --system-site-packages .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Test Camera** (optional):
   ```bash
   rpicam-hello -t 3000
   ```

## Usage

### Hardware Test Server

Test hardware outputs without camera:

```bash
python hardware_test_server.py
```

Visit `http://<pi-ip>:5000` to test:
- `/test-compliant` - Green LED (compliant)
- `/test-violation` - Red LED (violation)
- `/test-buzzer` - Buzzer beep
- `/test-all-off` - Turn off all outputs

### Color Detection Modes

1. **White/Compliant Mode**:
   ```bash
   python white_detector.py
   ```
   - Detects white/lab coat compliance
   - Green LED ON when compliant, Red LED ON when violation

2. **Yellow Mode**:
   ```bash
   python yellow_detector.py
   ```
   - Detects yellow spectrum compliance
   - Green LED ON when yellow detected, Red LED ON when violation

3. **Yellow + LCD Mode**:
   ```bash
   python yellow_lcd_detector.py
   ```
   - Full pipeline with LCD status updates
   - Green LED ON when yellow detected, Red LED ON when violation

### Flask Server

The MJPEG stream is available at:
```
http://<pi-ip>:5000
```

Or with port forwarding via SSH:
```bash
ssh -o ServerAliveInterval=60 -L 5000:localhost:5000 <user>@<pi-ip>
```

## Configuration

All configuration is in `bioguard/config.py`:

- **GPIO Pins**: Green LED (17), Red LED (22), Buzzer (18)
- **Camera**: 640x480 RGB888 format
- **HSV Ranges**:
  - White/Lab Coat: H=0-180, S=0-30, V=180-255
  - Yellow: H=15-45, S=100-255, V=100-255
- **Flask**: Host `0.0.0.0`, Port `5000`

## Development

To run in development mode with debug output:

```bash
python -m pip install --upgrade pip
python -m flask --app bioguard/streamer:create_app run --debug
```

## Troubleshooting

- **GPIO busy error**: Run `sudo pkill -f "gpio|pigpio"` and retry
- **Camera not working**: Ensure `picamera2` is installed and camera is enabled
- **LCD not displaying**: Verify I2C address (0x27) and connections

## License

MIT License - see LICENSE file.

Co-Authored-By: Claude Code <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)