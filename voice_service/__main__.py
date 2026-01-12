"""
Entry point for Voice Service.

Runs the voice call service as a FastAPI server.
"""
import logging
import click
import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from voice_service.voice_service.config import VOICE_SERVICE_PORT

try:
    import uvicorn
    from voice_service.voice_service.routes import app
    FASTAPI_AVAILABLE = True
except ImportError as e:
    FASTAPI_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to.")
@click.option("--port", default=VOICE_SERVICE_PORT, help="Port to bind the server to.")
def main(host:str, port: int):
    """Runs the Voice Service as a FastAPI server."""
    if not FASTAPI_AVAILABLE:
        logger.warning(f"FastAPI dependencies not found ({missing_dep})")
        return

    logger.info("Starting Voice Service FastAPI server...")
    logger.info(f"Listening on http://{host}:{port}")
    
    try:
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to start Voice Service: {e}")
        raise


if __name__ == "__main__":
    main()
