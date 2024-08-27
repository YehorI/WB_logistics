import datetime

from enum import Enum
from dataclasses import dataclass


@dataclass
class TimePeriod:
    start_date: datetime.datetime
    end_date: datetime.datetime


class DeliveryType(Enum):
    SUPERSAFE = 'Суперсейф'
    MONOPALLETS = 'Монопаллеты'
    BOXES = 'Короба'
    QR_DELIVERY_WITH_BOXES = 'QR-поставка с коробами'
