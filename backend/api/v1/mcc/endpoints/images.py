from data.data_wrappers.wrappers import ImageWrapper
from fastapi import APIRouter

from api.v1.mcc.models.responses import ImageResponse

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
