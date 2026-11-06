
from pathlib import Path

import pandas as pd


def load_csv(
    file_path: str | Path,
    required_columns: list[str] | None = None,
    allow_empty: bool = False,
) -> pd.DataFrame:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Provided path is not a file: {path}")

    df = pd.read_csv(path)

    if df.empty and not allow_empty:
        raise ValueError(f"CSV file is empty: {path}")

    if required_columns:
        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

    return df
