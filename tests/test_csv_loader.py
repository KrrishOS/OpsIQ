
from core.ingestion.csv_loader import load_csv


def test_load_machines():
    df = load_csv("data/synthetic/machines.csv")

    assert not df.empty
    assert len(df.columns) > 0

    print("\nMachines dataset loaded successfully!")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())


if __name__ == "__main__":
    test_load_machines()
