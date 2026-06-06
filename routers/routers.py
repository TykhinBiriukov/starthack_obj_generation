import logging

from pydantic import BaseModel
from fastapi import APIRouter

from services.image_processing import images_to_obj_processing


logger = logging.getLogger(__name__)
router = APIRouter()


class ImagesToObjRequest(BaseModel):
    zip_url: str



@router.post("/images-to-obj")
def image_router(request: ImagesToObjRequest):
    zip_url = request.zip_url
    logger.info("Received images-to-obj request for zip_url=%s", zip_url)
    response = images_to_obj_processing(zip_url)
    logger.info("Completed images-to-obj request for zip_url=%s", zip_url)
    return response


@router.post("/mesh-evaluation")
def mesh_evaluation_router(request: ImagesToObjRequest):
    logger.info("Received mesh-evaluation request")
    pass
