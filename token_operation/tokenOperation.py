import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import json
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from datetime import datetime, timedelta
import gdown
from token_operation.driveToken import Create_Drive_Token

global API_VERSION, CLIENT_FILE_NAME, API_DRIVE, SCOPES 
CLIENT_FILE_NAME = "./client_secret.json"
API_DRIVE = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

file_metadata = {
    "name": "Token_Folder",
    "mimeType": "application/vnd.google-apps.folder",
}

# ///////////////////////// CHECK THE PATH OF TOKEN FOLDER /////////////////////////////////
def Check_Token_Folder(service, path="root", Folder_Name="Token"):
    resource = service.files()
    result = resource.list(
        q=f"mimeType = 'application/vnd.google-apps.folder' and '{path}' in parents",
        fields="nextPageToken, files(id, name)",
    ).execute()
    list_folders = result.get("files")
    token_folder_id = None
    for folder in list_folders:
        if folder["name"] == Folder_Name:
            token_folder_id = folder["id"]
            break
    if not token_folder_id:
        token_folder = service.files().create(body=file_metadata, fields="id").execute()
        token_folder_id= token_folder["id"]

        result_folder = (
            service.files()
            .create(
                body={
                    "name": Folder_Name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [token_folder_id],
                    "type": "anyone",
                    "role": "reader",
                },
                fields="id",
            )
            .execute()
        )
        token_folder_id = result_folder["id"]

    return token_folder_id


def Check_Token_Main_Folder(path="root",Folder_Name="Token_Folder"):
    service = Create_Drive_Token()
    resource = service.files()
    result = resource.list(
        q=f"mimeType = 'application/vnd.google-apps.folder' and '{path}' in parents",
        fields="nextPageToken, files(id, name)",
    ).execute()

    list_folders = result.get("files")
    token_main_folder_id = None
    token_folder_id = None

    for folder in list_folders:
        if folder["name"] == Folder_Name:
            token_main_folder_id = folder["id"]
            token_folder_id = Check_Token_Folder(service, path=token_main_folder_id, Folder_Name="Token") 
            break

    if not token_main_folder_id:
        token_main_folder = service.files().create(body=file_metadata, fields="id").execute()
        token_main_folder_id= token_main_folder["id"]

        result_folder = (
            service.files()
            .create(
                body={
                    "name": "Token",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [token_main_folder_id],
                    "type": "anyone",
                    "role": "reader",
                },
                fields="id",
            )
            .execute()
        )
        token_folder_id = result_folder["id"]
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(fileId=token_folder_id, body=permission).execute()

    return token_main_folder_id, token_folder_id

def Create_Token(name):
    CLIENT_SECRET_FILE = CLIENT_FILE_NAME
    API_SERVICE_NAME = API_DRIVE
    # API_VERSION = API_VERSION
    # SCOPES = SCOPES

    cred = None
    pickle_file = f'{name}.pickle'

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
        # service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        return cred
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None
    
# ///////////////////////////// FROM HERE IT STARTS //////////////////////////////////

def Create_Token_Drive(name="current"):
    service = Create_Drive_Token()
    token_main_folder_id, token_folder_id = Check_Token_Main_Folder()
    try:
        response = (
            service.files()
        .list(
            q=f"'{token_main_folder_id}' in parents and name contains 'token_json'",
            spaces="drive",
            fields="files(id, name)",
        )
            .execute()
        )
        list_all_files = response.get("files", [])  
        is_selected = False
        file_name = ""
        for list_files in list_all_files:
            print("List Files = ", list_files["name"])
            if list_files["name"].startswith("token_json"):
                latest_file_id = str(list_files["id"])
                existing_data = service.files().get_media(fileId=latest_file_id).execute()
                if existing_data:  
                    existing_details = json.loads(existing_data.decode("utf-8"))
                    with open(list_files["name"], "w", encoding="utf-8") as json_file:
                        json.dump(existing_details, json_file, ensure_ascii=False)
                    if existing_details.get(name):
                        is_selected = True
                        token_id = existing_details[name]["token_file_id"]
                        url = f"https://drive.google.com/file/d/{token_id}/view?usp=sharing"
                        output = "current_token.pickle"
                        gdown.download(url=url, output=output, fuzzy=True)
                        with open(output, "rb") as cred:
                            creds = pickle.load(cred)
                            service = build(API_DRIVE, API_VERSION, credentials=creds)
                        os.remove(output)
                        return service, existing_details[name]["token_name"]
                    
                    else:
      
                        is_selected = True
                        token_file = Create_Token(name)
                        token_file_path = f'{name}.pickle' 
                        file_metadata = {"name": name, "parents": [token_folder_id]}
                        media = MediaFileUpload(token_file_path, mimetype="application/pdf")
                        newFile = (
                            service.files()
                            .create(body=file_metadata, media_body=media, fields="id")
                            .execute()
                        )
                        token_id = newFile.get("id")
                        expiry_time = datetime.now() + timedelta(hours=24)
                        existing_details[name]={
                            "token_name": name,
                            "token_file_id": token_id,
                            "expires_at": expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                        file_name = list_files["name"] 
                        with open(file_name, "w", encoding="utf-8") as json_file:
                            json.dump(existing_details, json_file)
                        json_file.close()
                        file_metadata = {"name": file_name, "parents": [token_main_folder_id]}
                        media = MediaFileUpload(file_name, mimetype="application/json")
                        service.files().update(fileId=latest_file_id, media_body=media).execute()
                        token_id = existing_details[name]["token_file_id"]
                        url = f"https://drive.google.com/file/d/{token_id}/view?usp=sharing"
                        output = "current_token.pickle"
                        gdown.download(url=url, output=output, fuzzy=True)
                        with open(output, "rb") as cred:
                            creds = pickle.load(cred)
                            service = build(API_DRIVE, API_VERSION, credentials=creds)
                        os.remove(output)
                        os.remove(token_file_path)
                        return service, existing_details[name]["token_name"]

        if not is_selected:
            token_file = Create_Token(name)
            file_metadata = {"name": name, "parents": [token_folder_id]}
            token_file_path = f'{name}.pickle' 
            media = MediaFileUpload(token_file_path, mimetype="application/pdf")
            # media = MediaFileUpload(token_file, mimetype="application/pdf")
            newFile = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            token_id = newFile.get("id")
            expiry_time = datetime.now() + timedelta(hours=24)
            existing_details = {}
            existing_details[name]={
                "token_name": name,
                "token_file_id": token_id,
                "expires_at": expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            file_name = f"token_json.json"
            json_data = json.dumps(existing_details)
            with open(file_name, "w") as f:
                f.write(json_data)
            file_metadata = {"name": file_name, "parents": [token_main_folder_id]}
            media = MediaFileUpload(
                file_name, mimetype="application/json", resumable=True
            )
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            token_id = existing_details[name]["token_file_id"]
            url = f"https://drive.google.com/file/d/{token_id}/view?usp=sharing"
            output = "current_token.pickle"
            gdown.download(url=url, output=output, fuzzy=True)

            with open(output, "rb") as cred:
                service = build(API_DRIVE, API_VERSION, credentials=cred)
            os.remove(output)
            os.remove(file_name)
            return service, existing_details[name]["token_name"]

    except Exception as e:
        print(f"An error occurred here: {str(e)}")

def Expire_Token_File():
    service = Create_Drive_Token()
    token_main_folder_id, token_folder_id = Check_Token_Main_Folder()
    try:
        response = (
            service.files()
            .list(
            q=f"'{token_main_folder_id}' in parents and name contains 'token_json'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        list_all_files = response.get("files", [])
        for list_files in list_all_files:
            if list_files["name"].startswith("token_json"):
                latest_file_id = str(list_files["id"])
                existing_data = service.files().get_media(fileId=latest_file_id).execute()
                if existing_data:  
                    existing_details = json.loads(existing_data.decode("utf-8"))
                    
                    with open(list_files["name"], "w", encoding="utf-8") as json_file:
                        json.dump(existing_details, json_file, ensure_ascii=False)
                    
                    for details in existing_details:
                        if datetime.strptime(details["expires_at"], "%Y-%m-%dT%H:%M:%SZ") < datetime.now():
                            drive_id = details["token_file_id"]
                            service.files().delete(fileId=details["token_file_id"]).execute()
                            del existing_details[details["token_name"]]
                            service.files().delete(fileId=drive_id).execute()
                            return True
        return False
    except Exception as e:
        print(f"An error occurred here: {str(e)}")

def Delete_Token_File(name):
    service = Create_Drive_Token()
    token_main_folder_id, token_folder_id = Check_Token_Main_Folder()
    try:
        response = (
            service.files()
            .list(
                q=f"'{token_main_folder_id}' in parents and name contains 'token_json'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        list_all_files = response.get("files", [])
        for list_files in list_all_files:
            if list_files["name"].startswith("token_json"):
                latest_file_id = str(list_files["id"])
                existing_data = service.files().get_media(fileId=latest_file_id).execute()
                if existing_data:  
                    existing_details = json.loads(existing_data.decode("utf-8"))
                    
                    with open(list_files["name"], "w", encoding="utf-8") as json_file:
                        json.dump(existing_details, json_file, ensure_ascii=False)
                    
                    for details in existing_details:
                        if details[name] == name:
                            drive_id = details["token_file_id"]
                            service.files().delete(fileId=details["token_file_id"]).execute()
                            del existing_details[details["token_name"]]
                            service.files().delete(fileId=drive_id).execute()
                            return True
        return False
    except Exception as e:
        print(f"An error occurred here: {str(e)}")