from flask import Flask, request, jsonify
from flask_cors import CORS
from controllers.chatbot_controller import Chatbot
from controllers.vector_store_controller import vectorStore_controller as VectorStore

app = Flask(__name__)
CORS(app)
# Initialize controllers
chatbot = Chatbot()
vector_store = VectorStore()


# Route for chatbot interaction
@app.route('/api/chatbot', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data['message']
        response = chatbot.send_message(user_input)
        # print(response)
        return response, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for adding documents to the knowledge base
@app.route('/api/knowledge-base/add', methods=['POST'])
def add_document():
    try:
        data = request.json
        sources = data['sources']
        sources_types = data['sources_types']
        vector_store.insert_data(sources, sources_types)
        return jsonify({"message": "Documents added successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for removing documents from the knowledge base
@app.route('/api/knowledge-base/remove', methods=['POST'])
def remove_document():
    try:
        data = request.json
        # Implement logic to remove specific documents based on identifiers
        # For simplicity, we'll clear all documents
        vector_store.delete_all_documents()
        return jsonify({"message": "Documents removed successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)