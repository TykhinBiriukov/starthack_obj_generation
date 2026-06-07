import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable
from urllib.parse import urlparse
from zipfile import BadZipFile, ZipFile

import requests
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance, ImageFilter, ImageStat, UnidentifiedImageError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
UPLOAD_DIR = Path(r"C:\uploads")
BLUR_THRESHOLD = 18.0
CONTRAST_FACTOR = 1.15
SHARPNESS_FACTOR = 1.10
logger = logging.getLogger(__name__)


def download_image(link: str, directory: Path):
    logger.info("Downloading image from %s", link)
    response = requests.get(link)
    response.raise_for_status()
    logger.info("Downloaded image response with %s bytes", len(response.content))

    # Try to get filename from URL
    filename = link.split("/")[-1].split("?")[0]

    # Fallback filename if URL does not contain a proper file name
    if not filename or "." not in filename:
        filename = "downloaded_image.jpg"

    # Full path where image will be saved
    file_path = os.path.join(directory, filename)

    # Save image
    with open(file_path, "wb") as file:
        file.write(response.content)
    logger.info("Saved image to %s", file_path)


def clear_images(directory: Path):
    if not directory.exists():
        logger.info("Image directory does not exist: %s", directory)
        return {"message": "No images found to process"}
    # Clear images from this run
    logger.info("Clearing images from %s", directory)
    for file in os.listdir(directory):
        os.remove(os.path.join(directory, file))
        logger.info("Deleted image file %s", file)


def _is_image_file(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def _safe_zip_members(zip_file: ZipFile) -> Iterable[str]:
    for member in zip_file.namelist():
        member_path = Path(member)
        if member.endswith("/") or member_path.is_absolute() or ".." in member_path.parts:
            continue
        if _is_image_file(member):
            yield member


def _iter_image_paths(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if path.is_file() and _is_image_file(path.name):
            yield path


def _image_edge_variance(image: Image.Image) -> float:
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges).var[0]


def _save_processed_image(image: Image.Image, path: Path) -> None:
    image_format = Image.registered_extensions().get(path.suffix.lower())
    save_kwargs = {}
    if image_format == "JPEG":
        save_kwargs = {"quality": 95, "optimize": True}
        if image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")

    image.save(path, format=image_format, **save_kwargs)


def remove_blurry_images(directory: Path, blur_threshold: float = BLUR_THRESHOLD) -> int:
    removed_count = 0
    for image_path in _iter_image_paths(directory):
        try:
            with Image.open(image_path) as image:
                edge_variance = _image_edge_variance(image)
        except (OSError, UnidentifiedImageError) as exc:
            logger.warning("Could not inspect image %s: %s", image_path, exc)
            continue

        if edge_variance < blur_threshold:
            image_path.unlink()
            removed_count += 1
            logger.info("Removed blurry image %s with edge variance %.2f", image_path, edge_variance)

    logger.info("Removed %s blurry images from %s", removed_count, directory)
    return removed_count


def add_contrast(directory: Path, factor: float = CONTRAST_FACTOR) -> int:
    processed_count = 0
    for image_path in _iter_image_paths(directory):
        try:
            with Image.open(image_path) as image:
                image.load()
                enhanced_image = ImageEnhance.Contrast(image).enhance(factor)
                _save_processed_image(enhanced_image, image_path)
        except (OSError, UnidentifiedImageError) as exc:
            logger.warning("Could not add contrast to image %s: %s", image_path, exc)
            continue

        processed_count += 1
        logger.info("Added contrast to image %s", image_path)

    logger.info("Added contrast to %s images in %s", processed_count, directory)
    return processed_count


def add_sharpening(directory: Path, factor: float = SHARPNESS_FACTOR) -> int:
    processed_count = 0
    for image_path in _iter_image_paths(directory):
        try:
            with Image.open(image_path) as image:
                image.load()
                sharpened_image = ImageEnhance.Sharpness(image).enhance(factor)
                _save_processed_image(sharpened_image, image_path)
        except (OSError, UnidentifiedImageError) as exc:
            logger.warning("Could not sharpen image %s: %s", image_path, exc)
            continue

        processed_count += 1
        logger.info("Sharpened image %s", image_path)

    logger.info("Sharpened %s images in %s", processed_count, directory)
    return processed_count


def preprocess_images(directory: Path) -> dict:
    logger.info("Starting image preprocessing in %s", directory)
    removed_blurry = remove_blurry_images(directory)
    contrast_added = add_contrast(directory)
    sharpened = add_sharpening(directory)
    return {
        "removed_blurry": removed_blurry,
        "contrast_added": contrast_added,
        "sharpened": sharpened,
    }


def _download_zip(zip_url: str, zip_path: Path) -> None:
    logger.info("Downloading zip from %s to %s", zip_url, zip_path)
    try:
        with requests.get(zip_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with zip_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
        logger.info("Downloaded zip to %s", zip_path)
    except requests.RequestException as exc:
        logger.exception("Could not download zip file from %s", zip_url)
        raise HTTPException(status_code=400, detail=f"Could not download zip file: {exc}") from exc


def save_uploaded_zip(file: UploadFile, upload_dir: Path = UPLOAD_DIR) -> dict:
    filename = Path(file.filename or "uploaded.zip").name
    if Path(filename).suffix.lower() != ".zip":
        logger.warning("Rejected uploaded file with non-zip filename: %s", filename)
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip file")

    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured zip upload directory exists: %s", upload_dir)

    destination = upload_dir / filename
    logger.info("Saving uploaded zip to %s", destination)
    try:
        with destination.open("wb") as output_file:
            shutil.copyfileobj(file.file, output_file)
    finally:
        file.file.close()

    file_size = destination.stat().st_size
    logger.info("Saved uploaded zip to %s with %s bytes", destination, file_size)
    return {
        "message": "Zip file uploaded successfully",
        "filename": filename,
        "path": str(destination),
        "size_bytes": file_size,
    }


def images_to_obj_processing(zip_url: str, print_paths: bool = False) -> FileResponse:
    logger.info("Starting image-to-obj processing")
    parsed_url = urlparse(zip_url)
    if parsed_url.scheme not in {"http", "https"}:
        logger.warning("Rejected zip_url with invalid scheme: %s", zip_url)
        raise HTTPException(status_code=400, detail="zip_url must be an HTTP or HTTPS URL")
    logger.info("Validated zip_url scheme: %s", parsed_url.scheme)

    temp_root = Path(r"C:\temp")
    if temp_root.exists():
        logger.info("Removing existing temporary directory: %s", temp_root)
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True, exist_ok=True)
    logger.info("Created temporary root directory: %s", temp_root)
    input_dir = temp_root / "input"
    output_dir = temp_root / "output"
    zip_path = temp_root / "source.zip"

    try:
        input_dir.mkdir()
        logger.info("Created input directory: %s", input_dir)
        output_dir.mkdir()
        logger.info("Created output directory: %s", output_dir)
        _download_zip(zip_url, zip_path)

        with ZipFile(zip_path) as zip_file:
            image_members = list(_safe_zip_members(zip_file))
            logger.info("Found %s safe image files in zip", len(image_members))
            for member in image_members:
                zip_file.extract(member, input_dir)
                logger.info("Extracted image member: %s", member)

        preprocessing_result = preprocess_images(input_dir)
        logger.info("Image preprocessing result: %s", preprocessing_result)

        script_path = Path(__file__).resolve().parent.parent / "scripts" / "run.bat"
        logger.info("Starting RealityScan script: %s", script_path)
        return_code = subprocess.Popen(script_path).wait()
        logger.info("RealityScan script finished with return code %s", return_code)
        if return_code != 0:
            raise HTTPException(status_code=500, detail=f"RealityScan script failed with code {return_code}")

        model_path = output_dir / "model.obj"
        logger.info("Returning generated model file: %s", model_path)
        return FileResponse(
            path=model_path,
            media_type="model/obj",
            filename="model.obj",
        )
    except BadZipFile as exc:
        logger.exception("Downloaded file is not a valid zip file: %s", zip_path)
        raise HTTPException(status_code=400, detail="Downloaded file is not a valid zip file") from exc
