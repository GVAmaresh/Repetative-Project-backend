import pickle
import os
import datetime
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import json

from comparator.compareSummerized import compareText

global API_VERSION, CLIENT_FILE_NAME, API_DRIVE, SCOPES 
CLIENT_FILE_NAME = "./token_operation/token_secret.json"
API_DRIVE = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# file_metadata = {
#     "name": "Token",
#     "mimeType": "application/vnd.google-apps.folder",
# }

def Create_Drive_Token():
    CLIENT_SECRET_FILE = CLIENT_FILE_NAME
    API_SERVICE_NAME = API_DRIVE
    # API_VERSION = API_VERSION
    # SCOPES = SCOPES

    cred = None
    pickle_file = f'./Drive_API.pickle'

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)

def Delete_Drive_Token():
    directory = os.getcwd()
    files = os.listdir(directory)
    for file in files:
        if "Drive_API" in file:
            try:
                os.remove(os.path.join(directory, file))
                print(f"File '{file}' deleted successfully.")
            except Exception as e:
                print(f"Error deleting file '{file}': {e}")
    print("No File named Drive_API was Found !!! ")
