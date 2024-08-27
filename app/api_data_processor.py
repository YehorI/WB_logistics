import datetime

import pandas as pd

from app.dto import DeliveryType, TimePeriod


class WildberriesSupplyDataProcessor:

    def __init__(self):
        ...

    async def coef_list2pdDF(coefs: list) -> pd.DataFrame:
        df = pd.DataFrame(coefs)
        
        df["date"] = pd.to_datetime(df["date"])

        return df

    async def apply_filters(self,
        df: pd,DataFrame,
        dates: list[datetime.datetime] | TimePeriod | None,
        warehouse_names: list[str] | None,
        box_type_names: list[DeliveryType] | None,
        coefficient_less: int | None,
        remove_unavailable: bool =False
    ) -> pd.DataFrame:
        if dates is not None:
            if isinstance(dates, list):
                df = df[df['date'].isin(dates)]
            else:
                df = df[(df['date'] >= dates[0]) & (df['date'] <= dates[-1])]

        if warehouse_names is not None:
            df = df[df['warehouse_name'].isin(warehouse_names)]
        
        if box_type_names is not None:
            df = df[df['box_type'].isin([bt.value for bt in box_type_names])]
        
        if coefficient_less is not None:
            df = df[df['coefficient'] < coefficient_less]
        
        if remove_unavailable is True:
            df = df[df["coefficient"] != -1]  

        return df
