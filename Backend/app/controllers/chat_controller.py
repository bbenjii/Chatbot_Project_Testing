# app/controllers/chat_controller.py
from flask import Blueprint, request, jsonify
from app.services.chatbot_service import ChatService
from app.controllers.base_controller import BaseController
from app.core.security import Security

chat_routes = Blueprint('chat', __name__)
chat_service = ChatService()

class ChatController(BaseController):
    @chat_routes.route('/api/chatbot', methods=['POST'])
    async def chat(self):
        try:
            data = request.json
            user_id = Security.get_current_user_id(request)
            thread_id = data.get('thread_id')
            message = data.get('message')

            if not message:
                return jsonify({'error': 'Message is required'}), 400

            response = await chat_service.process_message(
                user_id=user_id,
                thread_id=thread_id,
                message=message
            )

            return jsonify({
                'message': response
            }), 200

        except Exception as e:
            return ChatController.handle_error(e)