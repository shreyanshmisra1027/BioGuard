"""
MJPEG Streaming server for BioGuard.

Provides Flask-based video streaming with health/status endpoints.
"""

import logging
from typing import Generator, Optional, Callable
from flask import Flask, Response, jsonify

logger = logging.getLogger(__name__)


class MJPEGStreamer:
    """
    Flask-based MJPEG video streamer.

    Provides:
    - / endpoint: Live MJPEG stream
    - /health endpoint: Health check
    - /status endpoint: Current status
    """

    def __init__(self, app: Flask, frame_generator: Callable[[], Optional[bytes]],
                 status_provider: Optional[Callable[[], dict]] = None):
        """
        Initialize MJPEG streamer.

        Args:
            app: Flask application instance
            frame_generator: Function that yields JPEG-encoded frames
            status_provider: Optional function returning status dict
        """
        self.app = app
        self.frame_generator = frame_generator
        self.status_provider = status_provider or (lambda: {})

        self._setup_routes()

    def _setup_routes(self) -> None:
        """Register Flask routes."""

        @self.app.route('/')
        def index():
            """Root endpoint - MJPEG stream."""
            return Response(
                self._generate_stream(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

        @self.app.route('/health')
        def health():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "service": "bioguard"
            })

        @self.app.route('/status')
        def status():
            """Status endpoint with current state."""
            status_data = self.status_provider()
            status_data["service"] = "bioguard"
            return jsonify(status_data)

    def _generate_stream(self) -> Generator[bytes, None, None]:
        """
        Generate MJPEG stream frames.

        Yields:
            JPEG frames formatted for MJPEG streaming
        """
        while True:
            try:
                frame_bytes = self.frame_generator()
                if frame_bytes:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # Yield empty frame on error
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            except GeneratorExit:
                logger.info("Client disconnected from stream")
                break
            except Exception as e:
                logger.error(f"Stream generation error: {e}")
                break

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """
        Run the Flask server.

        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        logger.info(f"Starting MJPEG streamer on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def create_app() -> Flask:
    """
    Create Flask application.

    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    return app


def encode_frame(frame, quality: int = 85) -> Optional[bytes]:
    """
    Encode OpenCV frame to JPEG bytes.

    Args:
        frame: BGR image frame (numpy array)
        quality: JPEG quality (1-100)

    Returns:
        JPEG encoded bytes or None on error
    """
    import cv2

    if frame is None:
        return None

    try:
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes()
    except Exception as e:
        logger.error(f"Frame encoding error: {e}")
        return None