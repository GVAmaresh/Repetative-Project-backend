from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import json
import os
from io import BytesIO
import time
import io

file_metadata = {
    "name": "Fake",
    "mimeType": "application/vnd.google-apps.folder",
}
file_result = {
    "name": "Result",
    "mimeType": "application/vnd.google-apps.folder",
}
file_report = {
    "name": "Report",
    "mimeType": "application/vnd.google-apps.folder",
}


def checkFake(service, path="root", Folder_Name="Fake"):
    resource = service.files()
    result = resource.list(
        q=f"mimeType = 'application/vnd.google-apps.folder' and '{path}' in parents",
        fields="nextPageToken, files(id, name)",
    ).execute()
    list_folders = result.get("files")
    fake_folder_id = None
    result_folder_id = None
    report_folder_id = None

    for folder in list_folders:
        if folder["name"] == Folder_Name:
            fake_folder_id = folder["id"]
            break

    if not fake_folder_id:
        fake_folder = service.files().create(body=file_metadata, fields="id").execute()
        fake_folder_id = fake_folder["id"]
        result_folder = (
            service.files()
            .create(
                body={
                    "name": "Result",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [fake_folder_id],
                    "type": "anyone",
                    "role": "reader",
                },
                fields="id",
            )
            .execute()
        )
        result_folder_id = result_folder["id"]

        report_folder = (
            service.files()
            .create(
                body={
                    "name": "Report",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [fake_folder_id],
                },
                fields="id",
            )
            .execute()
        )
        report_folder_id = report_folder["id"]

    return fake_folder_id, result_folder_id, report_folder_id


def checkRespectiveFolder(service, path="root", Folder_Name="Fake"):
    resource = service.files()
    result = resource.list(
        q=f"mimeType = 'application/vnd.google-apps.folder' and '{path}' in parents",
        fields="nextPageToken, files(id, name)",
    ).execute()
    list_folders = result.get("files")
    fake_folder_id = None
    for folder in list_folders:
        if folder["name"] == Folder_Name:
            fake_folder_id = folder["id"]
            break
    return fake_folder_id


def CheckFolders(service):
    fake_folder_id = checkFake(service)
    return "Folders created or already existed."

def AddReport(service, fileName, file):
    fake_folder_id = checkRespectiveFolder(service)
    report_folder_id = checkRespectiveFolder(
        service, path=fake_folder_id, Folder_Name="Report"
    )

    file_metadata = {"name": fileName, "parents": [report_folder_id]}
    media = MediaFileUpload(file, mimetype="application/pdf")
    newFile = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return newFile.get("id")

def DeleteReport(service, fileName):
    fake_folder_id = checkRespectiveFolder(service)
    report_folder_id = checkRespectiveFolder(
        service, path=fake_folder_id, Folder_Name="Report"
    )
    response = (
        service.files()
        .list(
            q="mimeType='application/pdf' and '" + report_folder_id + "' in parents",
            spaces="drive",
            fields="files(id, name)",
            pageToken=None,
        )
        .execute()
    )
    for i in response["files"]:
        if i["name"] == fileName:
            file_id = i["id"]
            service.files().delete(fileId=file_id).execute()
            break

