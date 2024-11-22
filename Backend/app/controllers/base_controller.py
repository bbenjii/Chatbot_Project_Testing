# app/controllers/base_controller.py
from flask import jsonify
from app.core.exceptions import AppException
import logging

logger = logging.getLogger(__name__)

class BaseController:
    @staticmethod
    def handle_error(e: Exception):
        if isinstance(e, AppException):
            return jsonify({"error": e.message}), e.status_code
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
