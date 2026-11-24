#!/usr/bin/env python3
"""
BioGuard Hardware Test Server

Lightweight Flask server to test hardware outputs (LEDs, buzzer) without camera.
Run: python hardware_test_server.py

Endpoints:
- GET  /          - Status page with test buttons
- GET  /test-compliant  - Turn on green LED, turn off red LED
- GET  /test-violation  - Turn on red LED, turn off green LED
- GET  /test-buzzer     - Emit test beep
- GET  /test-all-off    - Turn off all outputs
"""

import logging
import signal
import sys
from flask import Flask, render_template_string, jsonify

from bioguard.hardware import HardwareController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global hardware controller
hardware: HardwareController = None
app = Flask(__name__)

# HTML template for test page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BioGuard Hardware Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 2rem auto; padding: 1rem; }
        h1 { color: #333; }
        .button-group { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }
        button {
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.8; }
        .btn-compliant { background: #28a745; color: white; }
        .btn-violation { background: #dc3545; color: white; }
        .btn-buzzer { background: #ffc107; color: black; }
        .btn-off { background: #6c757d; color: white; }
        .status { padding: 1rem; border-radius: 4px; margin: 1rem 0; }
        .status-ok { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <h1>BioGuard Hardware Test</h1>
    <div id="status" class="status status-ok">Hardware ready</div>
    <div class="button-group">
        <button class="btn-compliant" onclick="testCompliant()">Test Compliant (Green LED)</button>
        <button class="btn-violation" onclick="testViolation()">Test Violation (Red LED)</button>
        <button class="btn-buzzer" onclick="testBuzzer()">Test Buzzer</button>
        <button class="btn-off" onclick="testAllOff()">All Off</button>
    </div>
    <p><small>GPIO Pins: Green=17, Red=22, Buzzer=18 (PWM)</small></p>

    <script>
        async function call(endpoint) {
            const status = document.getElementById('status');
            try {
                const resp = await fetch(endpoint);
                const data = await resp.json();
                status.className = 'status ' + (data.success ? 'status-ok' : 'status-error');
                status.textContent = data.message;
            } catch (e) {
                status.className = 'status status-error';
                status.textContent = 'Error: ' + e.message;
            }
        }
        function testCompliant() { call('/test-compliant'); }
        function testViolation() { call('/test-violation'); }
        function testBuzzer() { call('/test-buzzer'); }
        function testAllOff() { call('/test-all-off'); }
    </script>
</body>
</html>
"""


def init_hardware():
    """Initialize hardware controller."""
    global hardware
    try:
        hardware = HardwareController(enable_lcd=False)
        logger.info("Hardware initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize hardware: {e}")
        return False


def cleanup_hardware():
    """Clean up hardware on exit."""
    global hardware
    if hardware:
        hardware.cleanup()
        logger.info("Hardware cleaned up")


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    cleanup_hardware()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.route('/')
def index():
    """Serve test page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/test-compliant')
def test_compliant():
    """Test compliant indicator (green LED)."""
    try:
        hardware.indicate_compliant()
        return jsonify({"success": True, "message": "Green LED ON, Red LED OFF"})
    except Exception as e:
        logger.error(f"Test compliant failed: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/test-violation')
def test_violation():
    """Test violation indicator (red LED)."""
    try:
        hardware.indicate_violation()
        return jsonify({"success": True, "message": "Red LED ON, Green LED OFF"})
    except Exception as e:
        logger.error(f"Test violation failed: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/test-buzzer')
def test_buzzer():
    """Test buzzer."""
    try:
        hardware.alert(duration=0.5, frequency=2000)
        return jsonify({"success": True, "message": "Buzzer beep emitted"})
    except Exception as e:
        logger.error(f"Test buzzer failed: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/test-all-off')
def test_all_off():
    """Turn off all outputs."""
    try:
        hardware.indicate_neutral()
        hardware.alert_stop()
        return jsonify({"success": True, "message": "All outputs OFF"})
    except Exception as e:
        logger.error(f"Test all off failed: {e}")
        return jsonify({"success": False, "message": str(e)})


if __name__ == '__main__':
    if init_hardware():
        try:
            logger.info("Starting hardware test server on 0.0.0.0:5000")
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        finally:
            cleanup_hardware()
    else:
        logger.error("Failed to start - hardware initialization failed")
        sys.exit(1)