"""

CODE TO CREATE A LOCAL FLASK APP WITH APIs TO TEST A CHATBOT WITH A FRONTEND INTERFACE

"""
from flask import Flask, request, jsonify, render_template
import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

from chatbot1_class import Chatbot1 as Chatbot

""" Either update the frontend dict to match the templates and folders """
# frontend = {
#     "template":"../../Frontend2/Widget-Interface/templates",
#     "static":"../../Frontend2/Widget-Interface/static"
# }
# app_old = Flask(__name__, template_folder=frontend["template"], static_folder=frontend["static"])

""" Or simply name the folder (works if the folder includes static and templates subfolders)"""
folder = "Interface-1"

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


# _________________________FLASK ROUTES________________________________________________________

#set the route in the script file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chatbot_no_memory():
    messages = [
        ("system", "You are an AI assistant that helps people find information.")
    ]
    user_message = request.json['message']
    messages.append(("human", user_message))
    response = llm.invoke(messages).content
    messages.append(("system", response))
    return jsonify({'response': response})




""" Route for Chatbot1 Class"""
systemPrompt = "You are an AI assistant that helps people find information."
Chatbot = Chatbot(systemPrompt=systemPrompt)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json['message']
    response = Chatbot.send_message(user_message)

    return jsonify({'response': response["messages"][-1].content})


if __name__ == '__main__':
    app.run(debug=True)