from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
from pathlib import Path
import sys
import asyncio
from typing import List
import json

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Add the parent directory to sys.path to import the main processing module
sys.path.append(str(PROJECT_ROOT))

# Create necessary directories
REQUIRED_DIRS = ['uploads', 'outputs', 'images', 'docs']
for dir_name in REQUIRED_DIRS:
    dir_path = PROJECT_ROOT / dir_name
    dir_path.mkdir(parents=True, exist_ok=True)

from main import main
from config import PATHS

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://*.azurewebsites.net",  # Azure domains
        "https://*.azurestaticapps.net"  # Azure Static Web Apps
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return JSONResponse({
        "status": "success",
        "message": "Slide Whisperer API is running",
        "endpoints": {
            "upload": "/upload",
            "download": "/download/{filename}"
        }
    })

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save the uploaded file
    file_path = PATHS['uploads'] / file.filename
    print(f"📥 Saving uploaded file to: {file_path}")
    
    # Ensure the uploads directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Change to project root directory before processing
        original_dir = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # Process the document by calling main() with the uploaded file path
        print(f"🔄 Processing file: {file_path}")
        main(str(file_path))
        
        # Read the generated presentation data
        with open(PATHS['presentation_data'], 'r') as f:
            presentation_data = json.load(f)
            
        # Get the output presentation path
        output_filename = "slide_whisper3.pptx"
        output_path = PATHS['outputs'] / output_filename
            
        # Change back to original directory
        os.chdir(original_dir)
            
        return {
            "status": "success",
            "message": "File processed successfully",
            "data": presentation_data,
            "presentation_filename": output_filename
        }
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        # Change back to original directory even if there's an error
        os.chdir(original_dir)
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        # Clean up the uploaded file
        if file_path.exists():
            print(f"🧹 Cleaning up uploaded file: {file_path}")
            file_path.unlink()

@app.get("/download/{filename}")
async def download_file(filename: str):
    try:
        # Change to project root directory
        original_dir = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        file_path = PATHS['outputs'] / filename
        print(f"📥 Attempting to download file: {file_path}")
        
        if file_path.exists():
            # Change back to original directory
            os.chdir(original_dir)
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        else:
            print(f"❌ File not found: {file_path}")
            os.chdir(original_dir)
            return {"error": "File not found"}
    except Exception as e:
        print(f"❌ Error serving file: {str(e)}")
        os.chdir(original_dir)
        return {"error": str(e)}

@app.get("/test")
async def test():
    return JSONResponse({
        "status": "success",
        "message": "API is working",
        "project_root": str(PROJECT_ROOT),
        "directories": {
            dir_name: str(PROJECT_ROOT / dir_name) for dir_name in REQUIRED_DIRS
        }
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 