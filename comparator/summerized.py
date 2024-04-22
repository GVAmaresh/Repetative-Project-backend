from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import json
import os
from io import BytesIO
import time
import io
from comparator.report import checkRespectiveFolder


def DeleteSummary(service, fileID):
    try:
        fake_folder_id = checkRespectiveFolder(service)
        result_folder_id = checkRespectiveFolder(
            service, path=fake_folder_id, Folder_Name="Result"
        )
        response = (
            service.files()
            .list(
                q="name contains 'data-'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        list_all_files = response.get("files", [])

        for list_files in list_all_files:
            if list_files["name"].startswith("data-"):
                latest_file_id = list_files["id"]

                existing_data = (
                    service.files().get_media(fileId=latest_file_id).execute()
                )
                existing_details = json.loads(existing_data.decode("utf-8"))

                updated_data = [
                    data for data in existing_details if data["id"] != fileID
                ]

                with open(list_files["name"], "w", encoding="utf-8") as json_file:
                    json.dump(updated_data, json_file, ensure_ascii=False)

                media = MediaFileUpload(list_files["name"], mimetype="application/json")

                service.files().update(
                    fileId=latest_file_id, media_body=media
                ).execute()
                return
        return
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def AddSummary(service, details):
    try:
        fake_folder_id = checkRespectiveFolder(service)
        result_folder_id = checkRespectiveFolder(
            service, path=fake_folder_id, Folder_Name="Result"
        )
        response = (
            service.files()
            .list(
                q="name contains 'data-'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        list_all_files = response.get("files", [])  

        is_selected = False
        file_name = ""

        for list_files in list_all_files:
            if list_files["name"].startswith("data-"):
                latest_file_id = str(list_files["id"])

                existing_data = service.files().get_media(fileId=latest_file_id).execute()

                if existing_data:  
                    existing_details = json.loads(existing_data.decode("utf-8"))

                    with open(list_files["name"], "w", encoding="utf-8") as json_file:
                        json.dump(existing_details, json_file, ensure_ascii=False)

                    if len(existing_details) < 100:
                        is_selected = True
                        file_name = list_files["name"]

                        with open(file_name, "r", encoding="utf-8") as json_file:
                            existing_data = json.load(json_file)

                        existing_data.append(details)

                        with open(file_name, "w", encoding="utf-8") as json_file:
                            json.dump(existing_data, json_file)

                        json_file.close()

                        file_metadata = {"name": file_name, "parents": [result_folder_id]}
                        media = MediaFileUpload(file_name, mimetype="application/json")

                        service.files().update(fileId=latest_file_id, media_body=media).execute()

                        return
            else:
                break

        if not is_selected:
            existing_details = [details]
            file_name = f"data-{len(list_all_files)}.json"
            json_data = json.dumps(existing_details)
            with open(file_name, "w") as f:
                f.write(json_data)
            file_metadata = {"name": file_name, "parents": [result_folder_id]}
            media = MediaFileUpload(
                file_name, mimetype="application/json", resumable=True
            )
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            return

    except Exception as e:
        print(f"An error occurred here: {str(e)}")
        
def Get_All_Reports(service):
    try:
        fake_folder_id = checkRespectiveFolder(service)
        result_folder_id = checkRespectiveFolder(
            service, path=fake_folder_id, Folder_Name="Result"
        )
        response = (
            service.files()
            .list(
                q="name contains 'data-'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        list_all_files = response["files"]
        all_reports = []
        
        for list_files in list_all_files:
            if list_files["name"].startswith("data-"):
                latest_file_id = str(list_files["id"])

                existing_data = (
                    service.files().get_media(fileId=latest_file_id).execute()
                )
                existing_details = json.loads(existing_data.decode("utf-8"))
                file_name = list_files["name"]

                with open(file_name, "w", encoding="utf-8") as json_file:
                    json.dump(existing_details, json_file, ensure_ascii=False)

                with open(file_name, "r", encoding="utf-8") as json_file:
                    existing_data = json.load(json_file)

                all_reports.extend(existing_details)
        return all_reports

    except Exception as e:
        print(f"An error occurred: {str(e)}")
