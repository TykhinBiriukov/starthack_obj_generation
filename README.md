# HackathonStartVienna

FastAPI service for turning a zip archive of images into a 3D OBJ model through Epic Games RealityScan. The API can also receive and store uploaded zip files for later processing.

## Features

- Upload zip files through a REST endpoint.
- Download an image zip from an HTTP/HTTPS URL.
- Safely extract image files from zip archives.
- Run a local RealityScan batch pipeline.
- Return the generated `model.obj` file.
- Structured application logging for startup, requests, file handling, and RealityScan execution.

## Project Structure

```text
.
|-- main.py                    # FastAPI app factory and uvicorn entry point
|-- requirements.txt           # Python dependencies
|-- routers/
|   `-- routers.py             # API route definitions
|-- services/
|   |-- image_processing.py     # Zip handling and RealityScan orchestration
|   `-- mesh_evaluation.py      # Mesh evaluation placeholder
`-- scripts/
    `-- run.bat                # RealityScan command-line pipeline
```

## Requirements

- Python 3.10 or newer
- Windows
- Epic Games RealityScan installed locally
- RealityScan executable at:

```text
C:\Program Files\Epic Games\RealityScan_2.1\RealityScan.exe
```

Python dependencies are listed in [requirements.txt](requirements.txt).

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the API

Start the development server:

```powershell
python main.py
```

The API runs at:

```text
http://127.0.0.1:8000
```

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Upload a Zip File

```http
POST /api/upload-zip
```

Stores an uploaded `.zip` file in the configured upload folder.

Example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/upload-zip" `
  -F "file=@C:\path\to\images.zip"
```

Example response:

```json
{
  "message": "Zip file uploaded successfully",
  "filename": "images.zip",
  "path": "C:\\uploads\\images.zip",
  "size_bytes": 123456
}
```

### Generate an OBJ From a Zip URL

```http
POST /api/images-to-obj
```

Downloads a zip archive from `zip_url`, extracts image files, runs RealityScan, and returns the generated OBJ file.

Example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/images-to-obj" `
  -H "Content-Type: application/json" `
  -d "{\"zip_url\":\"https://example.com/images.zip\"}" `
  --output model.obj
```

Request body:

```json
{
  "zip_url": "https://example.com/images.zip"
}
```

### Mesh Evaluation

```http
POST /api/mesh-evaluation
```

This endpoint is currently registered but not implemented. The service module contains a placeholder for future mesh evaluation logic.

## Runtime Paths

The application currently uses these local paths:

```text
Uploaded zip files: C:\uploads
Python processing temp root: C:\temp
RealityScan input folder: C:\temp\input
RealityScan output folder: C:\temp\output
Generated model path: C:\temp\output\model.obj
```

Important: `services/image_processing.py` currently writes extracted images to `C:\temp`, while `scripts/run.bat` reads from `C:\temp`. These paths should be made consistent before relying on the end-to-end OBJ generation flow.

Recommended fix:

- Use one shared temp root, for example `C:\temp`.
- Update both `services/image_processing.py` and `scripts/run.bat` to use the same `input`, `output`, and `model.obj` paths.
- Prefer moving these paths into environment variables so they can be changed without editing code.

## Configuration

The app loads environment variables from `.env` through `python-dotenv`, but the current path values are hardcoded.

Suggested `.env` variables for future cleanup:

```env
UPLOAD_DIR=C:\uploads
PROCESSING_DIR=C:\temp
REALITYSCAN_EXE=C:\Program Files\Epic Games\RealityScan_2.1\RealityScan.exe
```

## Logging

The API uses Python's standard `logging` module with this format:

```text
timestamp level logger message
```

Logs include:

- App startup
- Router registration
- Incoming requests
- Zip validation and download
- File extraction
- RealityScan script start and finish
- RealityScan return code

## Development Notes

- Only image files with known image extensions are extracted from downloaded zip archives.
- Zip extraction skips absolute paths and parent-directory traversal paths.
- `python-multipart` is required for file upload endpoints.
- `open3d` and `matplotlib` are installed for future mesh evaluation work.
- The current RealityScan command is Windows-specific.

## Validation

Run a syntax check:

```powershell
python -m compileall main.py routers services
```

If Windows blocks writes to `__pycache__`, use a no-bytecode syntax check:

```powershell
python -c "import ast, pathlib; [ast.parse(path.read_text(), filename=str(path)) for path in [pathlib.Path('main.py'), pathlib.Path('routers/routers.py'), pathlib.Path('services/image_processing.py'), pathlib.Path('services/mesh_evaluation.py')]]; print('syntax_ok')"
```

## Known Limitations

- `POST /api/mesh-evaluation` is not implemented yet.
- Processing paths are not centralized.
- The RealityScan executable path is hardcoded in `scripts/run.bat`.
- End-to-end generation requires RealityScan to be installed and licensed on the host machine.
- The API currently processes one generation job at a time through shared local folders, so concurrent requests may conflict.

## License

No license file is currently included. Add a license before distributing or publishing the project.
