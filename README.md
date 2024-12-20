

# Intro
This repository is an environment to develop all things related to the chatbot, that includes: 
- frontend interfaces, chatbot classes, knowledge base dev, etc.

## Technology
As of right now, the main technologies and tools used are:
- Python: langchain framework for chatbot building
- AZURE OPENAI for the llm model api

Technologies to implement eventually:
- JS React for the frontend
- docker for build

### MongoDB
structure:
{
  "_id": ObjectId("..."),  
  "file_name": "support_doc.pdf",  
  "file_type": "pdf",  
  "content": "The text extracted from the PDF...",  
  "embedding": [0.1, 0.2, 0.3, ...],  // The vector embedding.   
  "uploaded_at": ISODate("2024-10-22T10:00:00Z"). 
}


# Installation
## BACKEND
1. clone repository onto your Python-Dev IDE that supports 
2. Activate virtual env:
- cd Backend
- python3 -m venv .venv
- source .venv/bin/activate

3. Install Dependencies/Requirements
  - cd src
  - pip install -r requirements.txt
3. Place the required .env file inside the Backend directory
4. start coding 

## FRONTEND
1. Clone/open repository onto your JS/TS Dev IDE
2. Navigate to chatbot-app directory
3. Install modules
- use the latest node version (currently v23.1.0) 
- nvm install node
- nvm use node
- npm install
4. run react app
- npm run dev

# TO-DO
- Try implementing Web Sockets
- try developing some tools / series of actions
- Structured Outputs
- API functions to start model, restart it
- knowledge base: embeddings, vector stores, etc
- https://langchain-ai.github.io/langgraph/ : important and useful tutorials!


# TroubleShooting 
### Pymongo issues:
- ssl certification issue: https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate
