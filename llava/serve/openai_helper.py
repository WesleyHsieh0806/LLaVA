from typing import List, Optional, Literal, Union
from pydantic import BaseModel
from PIL import Image
import requests

from llava.utils import (
    build_logger,
    server_error_msg,
    violates_moderation,
    moderation_msg,
)


from llava.mm_utils import load_image_from_base64


from llava.conversation import SeparatorStyle, conv_templates, default_conversation

logger = build_logger("openai-api", f"openai-api.log")


class TextMessage(BaseModel):
    type: Literal["text"]
    text: str


class ImageURL(BaseModel):
    url: str


class ImageURLMessage(BaseModel):
    type: Literal["image_url"]
    image_url: ImageURL


class AssistantMessage(BaseModel):
    content: str


class GPTVMessage(BaseModel):
    role: str
    content: Union[List[Union[TextMessage, ImageURLMessage]], str]


class GPTVChatCompletionRequest(BaseModel):
    model: str
    messages: Union[str, List[GPTVMessage]]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    top_k: Optional[int] = -1
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None


def get_template(model_name):
    if "llava" in model_name.lower():
        if "llama-2" in model_name.lower():
            template_name = "llava_llama_2"
        elif "v1" in model_name.lower():
            if "mmtag" in model_name.lower():
                template_name = "v1_mmtag"
            elif "plain" in model_name.lower() and "finetune" not in model_name.lower():
                template_name = "v1_mmtag"
            else:
                template_name = "llava_v1"
        elif "mpt" in model_name.lower():
            template_name = "mpt"
        else:
            if "mmtag" in model_name.lower():
                template_name = "v0_mmtag"
            elif "plain" in model_name.lower() and "finetune" not in model_name.lower():
                template_name = "v0_mmtag"
            else:
                template_name = "llava_v0"
    elif "mpt" in model_name:
        template_name = "mpt_text"
    elif "llama-2" in model_name:
        template_name = "llama_2"
    else:
        template_name = "vicuna_v1"

    return conv_templates[template_name].copy()


def load_image_from_url(image_url):
    if image_url.startswith("http"):
        img = Image.open(requests.get(image_url, stream=True).raw)
        img.save("debug.jpg")
    elif image_url.startwith("data:image"):
        img = load_image_from_base64(image_url)

    return img


def safe_append(history, text, image, image_process_mode="Default"):
    if len(text) <= 0 and image is None:
        history.skip_next = True
        return history

    text = text[:1536]  # Hard cut-off
    if image is not None:
        text = text[:1200]  # Hard cut-off for images
        if "<image>" not in text:
            text = text + "\n<image>"
        text = (text, image, image_process_mode)
        if len(state.get_images(return_pil=True)) > 0:
            history = default_conversation.copy()
    history.append_message(history.roles[0], text)
    history.skip_next = False

    return history