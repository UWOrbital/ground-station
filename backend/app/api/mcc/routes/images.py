from app.api.v1.mcc.schemas.responses import ImageResponse
from fastapi import APIRouter

from app.data.data_wrappers.wrappers import ImageWrapper

images_router = APIRouter(tags=["MCC", "Images"])


@images_router.get("/latest")
async def get_latest_image() -> ImageResponse | dict[str, str]:
    """
    Return the most recent image downlinked from the satellite.

    :return: the latest Image, or a message if none exist.
    """
    wrapper = ImageWrapper()
    image = wrapper.get_latest()
    if image is None:
        return {"message": "No images available"}
    return ImageResponse(id=image.id, data=image.data)
