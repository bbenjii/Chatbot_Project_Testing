# app/main.py
from flask import Flask, jsonify
from flask_cors import CORS
import asyncio
import logging
from typing import Optional
import os
from dotenv import load_dotenv

# Import your components
from app.core.database import Database
from app.controllers.document_controller import document_routes
from app.controllers.chat_controller import chat_routes
from app.core.exceptions import AppException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_app()

    def setup_app(self):
        """Initialize Flask application with configurations and extensions."""
        # Enable CORS
        CORS(self.app)

        # Configure error handlers
        self.setup_error_handlers()

        # Register blueprints
        self.register_blueprints()

        # Setup database connection management
        self.setup_database_handlers()

    def setup_error_handlers(self):
        """Configure application-wide error handlers."""

        @self.app.errorhandler(AppException)
        def handle_app_exception(error):
            return jsonify({
                'error': error.message,
                'status': 'error'
            }), error.status_code

        @self.app.errorhandler(Exception)
        def handle_generic_error(error):
            logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
            return jsonify({
                'error': 'An unexpected error occurred',
                'status': 'error'
            }), 500

    def register_blueprints(self):
        """Register Flask blueprints."""
        self.app.register_blueprint(document_routes)
        self.app.register_blueprint(chat_routes)

    def setup_database_handlers(self):
        """Setup database connection lifecycle handlers."""

        @self.app.before_first_request
        async def init_db():
            try:
                await Database.connect(
                    mongodb_url=os.getenv('MONGODB_URL'),
                    db_name=os.getenv('DB_NAME')
                )
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise

        @self.app.teardown_appcontext
        async def shutdown_db(exception: Optional[Exception] = None):
            try:
                await Database.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")

    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the Flask application."""
        try:
            logger.info(f"Starting application on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise


def create_app() -> Flask:
    """Application factory function."""
    flask_app = FlaskApp()
    return flask_app.app


if __name__ == '__main__':
    # Get configuration from environment variables
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    try:
        # Create and run the application
        app = create_app()

        # Optional: Initialize any async tasks or setup
        loop = asyncio.get_event_loop()
        loop.run_until_complete(Database.connect(
            mongodb_url=os.getenv('MONGODB_URI'),
            db_name=os.getenv('DB_NAME')
        ))

        # Run the Flask application
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        print(f"Application failed to start: {e}")
        raise
    finally:
        # Cleanup
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(Database.close())
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
