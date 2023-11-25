from typing import Optional, Union

from pydantic import BaseModel, Field, Json


class PaymentCallback(BaseModel):
    uuid: Optional[str] = None
    address_in: Optional[str] = None
    address_out: Optional[str] = None
    txid_in: Optional[str] = None
    txid_out: Optional[str] = None
    confirmations: Optional[int] = None
    value_coin: Optional[float] = None
    value_coin_convert: Optional[Union[dict, Json]] = None
    value_forwarded_coin: Optional[float] = None
    value_forwarded_coin_convert: Optional[Union[dict, Json]] = None
    fee_coin: Optional[float] = None
    coin: Optional[str] = None
    price: Optional[float] = None
    pending: Optional[int] = None
