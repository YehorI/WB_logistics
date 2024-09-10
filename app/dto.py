import datetime

from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict


DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class TimePeriod:
    start_date: datetime.datetime
    end_date: datetime.datetime


class DeliveryType(Enum):
    SUPERSAFE = 'Суперсейф'
    MONOPALLETS = 'Монопаллеты'
    BOXES = 'Короба'
    QR_DELIVERY_WITH_BOXES = 'QR-поставка с коробами'


class WarehouseShort(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(frozen=False)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, WarehouseShort):
            return self.id == other.id
        return False


class Warehouse(WarehouseShort):
    address: str
    wopk_time: str
    acceptsQR: bool


class Coefficient(BaseModel):
    date: str
    coefficient: int

    warehouse_id: int
    warehouse_name: str

    box_type_name: str
    box_type_id: int | None


class RightDate:
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, date: datetime.datetime):
        self.date = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

    @classmethod
    def from_string(cls, date_string: str) -> 'RightDate':
        date = datetime.datetime.strptime(date_string, cls.DATE_FORMAT)
        return cls(date)

    def to_string(self) -> str:
        return self.date.strftime(self.DATE_FORMAT)

    def display_date(self) -> str:
        return self.date.strftime('%d.%m')

    def __eq__(self, other):
        if isinstance(other, RightDate):
            return self.date == other.date
        return False

    def __lt__(self, other):
        if isinstance(other, RightDate):
            return self.date < other.date
        return NotImplemented

    def __add__(self, days: int):
        return RightDate(self.date + datetime.timedelta(days=days))

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return f"RightDate({self.to_string()})"

