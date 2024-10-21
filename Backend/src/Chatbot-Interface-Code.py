from flask import Flask, request, jsonify, render_template
import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

frontend = {
    "template":"../../Frontend/Widget-Interface/templates",
    "static":"../../Frontend/Widget-Interface/static"
}

folder = "Interface-1"
# folder = "Widget-Interface"


# app = Flask(__name__, template_folder=frontend["template"], static_folder=frontend["static"])

app = Flask(__name__, template_folder=(f"../../Frontend/{folder}/templates"), static_folder=f"../../Frontend/{folder}/static")


# _________________________SET UP CODE__________________________________________________________
load_dotenv() #load .env variables

api_endpoint = os.getenv('AZURE_OPENAI_API_KEY')
api_key = os.getenv('AZURE_OPENAI_ENDPOINT')
api_version = os.getenv('OPENAI_API_VERSION')
api_type = os.getenv('OPENAI_API_TYPE')
deployment_model = os.getenv('OPENAI_MODEL')
deployment_name = os.getenv('OPENAI_NAME')

llm = AzureChatOpenAI(
    azure_deployment=deployment_name,
    api_version=api_version,
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    model=deployment_model
)

messages = [
    ("system", "You are an AI assistant that helps people find information.")
]

# _________________________FLASK ROUTES________________________________________________________


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    messages.append(("human", user_message))
    response = llm.invoke(messages).content
    messages.append(("system", response))
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)