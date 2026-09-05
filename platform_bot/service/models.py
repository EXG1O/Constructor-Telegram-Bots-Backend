from pydantic import BaseModel, Field

from .enums import KeyboardButtonStyle


class ResponseObject(BaseModel):
    pass


class InitCheckoutResponse(ResponseObject):
    url: str


class RefundPayment(BaseModel):
    user_id: int = Field(serialization_alias='user_service_id')
    user_telegram_id: int
    invoice_id: int
    telegram_charge_id: str


class LinkPreviewOptions(BaseModel):
    is_disabled: bool
    url: str | None = None
    prefer_small_media: bool | None = None
    prefer_large_media: bool | None = None
    show_above_text: bool = False


class KeyboardButton(BaseModel):
    text: str
    style: KeyboardButtonStyle = KeyboardButtonStyle.DEFAULT


class Keyboard[T: KeyboardButton](BaseModel):
    rows: list[list[T]]


class DefaultKeyboardButton(KeyboardButton):
    pass


class DefaultKeyboard(Keyboard[DefaultKeyboardButton]):
    pass


class InlineKeyboardButton(KeyboardButton):
    url: str | None = None


class InlineKeyboard(Keyboard[InlineKeyboardButton]):
    pass
