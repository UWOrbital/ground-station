from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.mcc.schemas.responses import ImageResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import ImageRepository

images_router = APIRouter(tags=["MCC", "Images"])


@images_router.get("/latest")
async def get_latest_image(
    images: Annotated[ImageRepository, Depends(DAL.get_repo(DAL.images))],
) -> ImageResponse | dict[str, str]:
    """
    Return the most recent image downlinked from the satellite.

    :param images: injected Image repository.
    :return: the latest Image, or a message if none exist.
    """
    image = await images.get_latest()
    if image is None:
        return {"message": "No images available"}
    return ImageResponse(id=image.id, data=image.data)
