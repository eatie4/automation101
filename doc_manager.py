import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TaxCaddyClient:
    def __init__(self, auth_token=None):
        self.auth_token = auth_token or os.getenv('TAXCADDY_AUTH_TOKEN')
        self.base_url = os.getenv('TAXCADDY_BASE_URL')
        self.headers = {
            'AuthToken': self.auth_token,
            'Content-Type': 'application/json'
        }

    def download_document(self, user_email, document_id, output_file='document.zip'):
        url = os.path.join(self.base_url, 'DownloadDocument')
        data = {
            "UserEmail": user_email,
            "Documents": [{"documentID": document_id}]
        }

        try:
            response = requests.post(url, json=data, headers=self.headers, stream=True)
            
            if response.status_code == 200:
                file_path = os.path.join(os.getcwd(), output_file)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f'Download complete. File saved to: {file_path}')
                return file_path
            else:
                print(f'Failed to download documents: {response.status_code} - {response.json()}')
                return None
        
        except requests.exceptions.RequestException as e:
            print(f'Error occurred while downloading documents: {str(e)}')
            return None
