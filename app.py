from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated
import os
import shutil
from typing import List
from pydantic import BaseModel
from api_connection.apiConnection import Create_Service
from comparator.report import (
    AddReport,
    CheckFolders,
    DeleteReport,
)
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from api_connection.apiConnection import token_file_exists
from comparator.summerized import AddSummary, DeleteSummary, Get_All_Reports

from api_connection.apiConnection import removeAccount
import uuid
from comparator.text_summerizer.summerize2 import Summerized_Text
from comparator.extract.extract import extract_text_from_pdf

from comparator.compareSummerized import compareText

from token_operation.driveToken import Delete_Drive_Token, Create_Drive_Token
from token_operation.tokenOperation import Create_Token_Drive, Delete_Token_File, Expire_Token_File

from pydantic import BaseModel
class AccountInfo(BaseModel):
    oldName: str
    newName: str


"""
Folder Path in drive would be:
    Fake/reports
    Fake/summerized
    
"""

class IDRequest(BaseModel):
    ids: List[str]

global API_VERSION, CLIENT_FILE_NAME, API_DRIVE, SCOPES 
CLIENT_FILE_NAME = "./client_secret.json"
API_DRIVE = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class AccountCheck(BaseModel):
    name: str

@app.post("/api/isLogin")
async def is_login(request: AccountCheck):
    try:
        global services
        services, name = Create_Token_Drive(request.name)
        if services:
            return {"message": "Successfully logged in", "data": name, "status":"success"}
        else:
            return {"message": "Failed to login", "data": False, "status":"failed"}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": "Failed to login", "data": False, "status":"failed"}
    
@app.get()
def check_working():
    return {"message": "Message working Successfully",  "status":"success"}

async def process_file(file):
    try:
        summerized_id = str(uuid.uuid4())
        file_contents = await file.read()
        directory = "./delete"
        os.makedirs(directory, exist_ok=True) 
        path = os.path.join(directory, file.filename) 
        path = f"./delete/{file.filename}"
        with open(path, "wb") as f:
            f.write(file_contents)
        text = extract_text_from_pdf(path)
        summary = Summerized_Text(text)
        report_id = AddReport(services, summerized_id, path)
        AddSummary(
            services,
            {
                "id": summerized_id,
                "project": "",
                "summary": summary,
                "drive": f"https://drive.google.com/file/d/{report_id}/view?usp=sharing",
                "year": "2023",
                "category": ["wanna check"],
            },
        )
        os.remove(path)
        return {
            "message": f"Successfully added Report and Summary for {file.filename}",
            "data": {
                "id": summerized_id,
                "compare": "",
                "title": "",
                "summary": summary,
                "drive": f"https://drive.google.com/file/d/{report_id}/view?usp=sharing",
                "year": "2023",
                "category": ["wanna check"],
            },
            "success": True,
        }
    except Exception as e:
        return {
            "message": f"Error processing {file.filename}: {str(e)}",
            "status": "failed",
        }

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            responses = await asyncio.gather(*[loop.run_in_executor(pool, process_file, file) for file in files])
        print("Uploaded Successfully")
        return {"data": [await response for response in responses], "status": "success"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to Upload files", "data": False, "status": "failed"}
    

@app.post("/api/delete")
async def delete_files(request: IDRequest):
    try:
        for report_name in request.ids:
            DeleteSummary(services, report_name)
            DeleteReport(services, report_name)
            try:
                directory = "."
                for filename in os.listdir(directory):
                    if filename.startswith("data-"):
                        file_path = "./" + filename
                        os.remove(file_path)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
        return {"message": "Successfully Deleted Summary and Report", "success": True}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to login", "data": False, "status":"failed"}



@app.post("/api/logout")
async def delete_account(request: AccountInfo):
    try:
        Delete_Token_File(request.oldName)
        global services  
        services, name = Create_Token_Drive(request.newName)
        return {"message": "Successfully Deleted Account", "data": name, "success": True}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to login", "data": False, "status":"failed"}


@app.get("/api/getReports")
async def get_reports():
    try:
        data = Get_All_Reports(services)
        if len(data) == 0:
            return {"data": None, "status": "failed" }
        try:
            directory = "."
            for filename in os.listdir(directory):
                if filename.startswith("data-"):
                    file_path = "./" + filename
                    os.remove(file_path)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        return {"data": data, "success": True}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to login", "data": False, "status":"failed"}



@app.post("/api/compare")
async def compare(file: UploadFile = File(...)):
    try:
        CheckFolders(services)
        summerized_id = str(uuid.uuid4())
        file_contents = await file.read()
        path = f"./delete/{file.filename}"
        with open(path, "wb") as f:
            f.write(file_contents)
        text = extract_text_from_pdf(path)
        summary = Summerized_Text(text)
        path = f"./delete/{file.filename}"
        with open(path, "wb") as f:
            f.write(file_contents)
        data = compareText(services, summary)
        try:
            directory = "."
            for filename in os.listdir(directory):
                if filename.startswith("data-"):
                    file_path = "./" + filename
                    os.remove(file_path)
                if filename.startswith("delete"):
                    file_path = path
                    os.remove(file_path)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        return {"summary": summary, "data": data, "success": True}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to login", "data": False, "status":"failed"}

@app.get("/api/Check-Expired")
async def checkExpired():
    try:
        Expire_Token_File()
        return {"message": "Successfully Expired", "status": "success"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to Check Expired Tokens", "data": False, "status":"failed"}


@app.post("/api/New-Drive")
async def NewDrive():
    try:
        Delete_Drive_Token()
        Create_Drive_Token()
        return {"message": "Successfully Created a new drive", "status": "success"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"message": "Failed to login", "data": False, "status":"failed"}


if __name__ == "__main__":
    global services
    Create_Drive_Token()
    uvicorn.run(app, host="0.0.0.0", port=8000)

