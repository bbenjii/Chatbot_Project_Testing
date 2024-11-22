# app/controllers/document_controller.py
from flask import Blueprint, request, jsonify
from app.services.document_service import DocumentService
from app.controllers.base_controller import BaseController
from app.core.security import Security

document_routes = Blueprint('documents', __name__)
document_service = DocumentService()


class DocumentController(BaseController):
    @document_routes.route('/api/storage/files', methods=['POST'])
    async def upload_file(self):
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            # Get user_id from auth token
            user_id = Security.get_current_user_id(request)

            result = await document_service.upload_document(
                user_id=user_id,
                file_content=file.read(),
                filename=file.filename,
                content_type=file.content_type
            )

            return jsonify(result), 200

        except Exception as e:
            return DocumentController.handle_error(e)

    @document_routes.route('/api/storage/files', methods=['GET'])
    async def list_files(self):
        try:
            user_id = Security.get_current_user_id(request)
            documents = await document_service.get_user_documents(user_id)
            return jsonify(documents), 200

        except Exception as e:
            return DocumentController.handle_error(e)