from pydantic import BaseModel


class CreditBalanceResponse(BaseModel):
    credits: int
