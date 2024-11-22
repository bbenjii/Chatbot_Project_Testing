from flask import Flask, request, jsonify
from flask_cors import CORS

from controllers.azure_storage_controller import storage
from controllers.chatbot_controller import Chatbot
from controllers.vector_store_controller import VectorStoreController as VectorStore
from controllers.azure_storage_controller import AzureStorageController as AzureStorage
app = Flask(__name__)
CORS(app)
# Initialize controllers
chatbot = Chatbot()
vector_store = VectorStore()
azure_storage = AzureStorage()


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


# Route for uploading file
@app.route('/api/storage/files', methods=['POST'])
def upload_file():
    try:
        # Check if the file part is present in the request
        if 'file' not in request.files:
            print("No file part in the request")
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        file_name = request.form.get('name')  # Get the file name from the form data

        if file.filename == '':
            print("No file selected for uploading")

            return jsonify({'error': 'No file selected for uploading'}), 400

        if not file_name:
            print("No file name provided")

            return jsonify({'error': 'No file name provided'}), 400

        # Read the file content
        file_content = file.read()

        # Determine the content type
        content_type = file.content_type or 'application/octet-stream'

        # Call your modified add_file function
        file_url = storage.add_file(file_content, file_name, content_type)

        return jsonify({'message': 'File uploaded successfully', 'url': file_url}), 200

    except Exception as ex:
        return jsonify({'error': f"Error uploading file: {str(ex)}"}), 500


# Route for fetching documents from Azure Storage
@app.route('/api/storage/files', methods=['GET'])
def fetch_documents():
    try:
        response = azure_storage.list_files_with_urls()
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