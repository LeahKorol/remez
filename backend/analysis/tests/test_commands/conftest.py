import pytest
from pathlib import Path
import zipfile
import pandas as pd
from typing import Callable


@pytest.fixture
def create_zipped_csv() -> Callable[[pd.DataFrame, str, Path], Path]:
    def _create_zipped_csv(dataframe: pd.DataFrame, filename: str, path: Path) -> Path:
        """
        Create a temporary zipped CSV file from the given DataFrame.
        Yields the path to the zipped file.
        """
        csv_filename = f"{filename}.csv"
        csv_path = path / csv_filename
        zip_path = path / f"{csv_filename}.zip"

        dataframe.to_csv(csv_path, index=False)  # write the CSV file

        # Zip the CSV file
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(csv_path, arcname=csv_filename)

        csv_path.unlink()  # Delete the unzipped CSV

        return zip_path

    return _create_zipped_csv
