from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import json
import os
from io import BytesIO
import time
import io
from comparator.report import checkRespectiveFolder
from comparator.compare_model.compare import compare
def get_compare_value(report):
    return report["compare"]

def compareText(service, summary):
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
        all_reports = []

        for list_files in list_all_files:
            if list_files["name"].startswith("data-"):
                latest_file_id = str(list_files["id"])

                existing_data = (
                    service.files().get_media(fileId=latest_file_id).execute()
                )
                existing_details = json.loads(existing_data.decode("utf-8"))
                file_name = list_files["name"]

                for json_data in existing_details:
                    print(summary)
                    value = compare(summary, json_data["summary"])
                    all_reports.append(
                        {
                            "id": json_data["id"],
                            "year": json_data["year"],
                            "drive": json_data["drive"],
                            "summary": json_data["summary"],
                            "category": json_data["category"],
                            "title": "",
                            "compare": value,
                        }
                    )
        sorted_reports = sorted(all_reports, key=get_compare_value, reverse=True)
        return sorted_reports

    except Exception as e:
        print(f"An error occurred: {str(e)}")
