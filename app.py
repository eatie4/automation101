import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from celery import Celery
import requests
from doc_manager import TaxCaddyClient

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['ENV'] = os.getenv('FLASK_ENV')

# Initialize Celery
def make_celery(app_name=__name__):
    return Celery(
        app_name,
        broker=os.getenv('CELERY_BROKER_URL'),
        backend=os.getenv('CELERY_RESULT_BACKEND')
    )

celery_app = make_celery()

@celery_app.task
def upload_document_to_second_platform(file_path, upload_url, headers):
    with open(file_path, 'rb') as file_data:
        response = requests.post(upload_url, files={'file': file_data}, headers=headers)
        if response.status_code == 200:
            print('File successfully uploaded to the second platform.')
        else:
            print(f'Failed to upload file: {response.status_code} - {response.json()}')

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    event_type = data.get('eventType')
    if event_type == 'doc.uploaded':
        document_id = data['eventData']['data']['documentID']
        user_email = data['eventData']['data']['uploadedBy']

        # Download the document using TaxCaddyClient
        client = TaxCaddyClient(auth_token=os.getenv('AUTH_TOKEN'))
        file_path = client.download_document(user_email=user_email, document_id=document_id)

        if file_path:
            # Queue the file for upload to the second platform using Celery
            upload_document_to_second_platform.delay(
                file_path=file_path,
                upload_url=os.getenv('SECOND_PLATFORM_UPLOAD_URL'),
                headers={'Authorization': f'Bearer {os.getenv("SECOND_PLATFORM_AUTH_TOKEN")}'}
            )
        
        return jsonify({"status": "Webhook processed"}), 200
    else:
        return jsonify({"status": "Event type not handled"}), 400

if __name__ == '__main__':
    app.run(debug=True)
