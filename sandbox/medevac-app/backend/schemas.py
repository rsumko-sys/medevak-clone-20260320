from typing import List

from pydantic import BaseModel


class InventoryItemBase(BaseModel):
    item_name: str
    qty: int


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemOut(InventoryItemBase):
    id: int

    class Config:
        from_attributes = True


class PositionCreate(BaseModel):
    name: str
    x: float
    y: float
    items: List[InventoryItemCreate]


class PositionOut(BaseModel):
    id: int
    name: str
    x: float
    y: float
    items: List[InventoryItemOut]

    class Config:
        from_attributes = True


class CaseNeedBase(BaseModel):
    item_name: str
    qty: int


class CaseNeedCreate(CaseNeedBase):
    pass


class CaseCreate(BaseModel):
    x: float
    y: float
    needs: List[CaseNeedCreate]


class CaseOut(BaseModel):
    id: int
    x: float
    y: float
    status: str
    needs: List[CaseNeedBase]

    class Config:
        from_attributes = True
