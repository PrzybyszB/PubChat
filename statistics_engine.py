import pandas as pd
from sqlalchemy import create_engine
from models import StatisticsResult

engine = create_engine(
    "postgresql://postgres:postgres@localhost:5432/diploma_db"
)

NUTRIENT_COLUMNS = {
    "fiber": "DR1TFIBE",
    "sodium": "DR1TSODI"
}

def calculate_statistics(nutrient: str, min_value: float, max_value: float, engine) -> StatisticsResult:

    column = NUTRIENT_COLUMNS[nutrient]

    query = f"""
    SELECT "{column}" AS nutrient_value
    FROM nhanes_gold 
    WHERE "{column}" IS NOT NULL
    """

    df = pd.read_sql(query, engine)

    values = df["nutrient_value"]

    mean_value = values.mean()
    median_value = values.median()
    p90_value = values.quantile(0.90)

    total = len(values)

    pct_low = ((values < min_value).sum()/ total)* 100
    pct_high = ((values > max_value).sum()/ total)* 100
    pct_normal = (((values >= min_value) & (values <= max_value)).sum()/ total)* 100

    problem= ("deficiency" if pct_low > pct_high else "excess")

    return StatisticsResult(
        mean_value = round(mean_value, 1),
        median_value = round(median_value, 1),
        p90_value = round(p90_value, 1),

        pct_low = round(pct_low, 1),
        pct_normal = round(pct_normal, 1),
        pct_high = round(pct_high, 1),

        problem = problem
    )