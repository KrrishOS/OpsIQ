import pandas as pd
from pathlib import Path

p = Path("data/synthetic")

orders = pd.read_csv(p / "production_orders.csv")
downtime = pd.read_csv(p / "downtime.csv")
quality = pd.read_csv(p / "quality_inspections.csv")

checks = {
    "Planned production is positive":
        (orders["planned_qty"] > 0).all(),

    "Actual production is positive":
        (orders["actual_qty"] > 0).all(),

    "Actual production does not exceed 103% of plan":
        (orders["actual_qty"] <= orders["planned_qty"] * 1.03).all(),

    "Production start precedes production end":
        (pd.to_datetime(orders["start_time"]) <
         pd.to_datetime(orders["end_time"])).all(),

    "Defective quantity does not exceed inspected quantity":
        (quality["defective_qty"] <= quality["inspected_qty"]).all(),

    "Defective quantity is not negative":
        (quality["defective_qty"] >= 0).all(),

    "Downtime duration is positive":
        (downtime["duration_min"] > 0).all(),

    "Downtime timestamps are valid":
        (pd.to_datetime(downtime["start_time"]) <
         pd.to_datetime(downtime["end_time"])).all(),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} | {name}")

print("\nOverall:",
      "ALL PASSED" if all(checks.values()) else "CHECK FAILED")

      
# INVENTORY MODEL VALIDATION

inventory = pd.read_csv(p / "inventory_transactions.csv")
materials = pd.read_csv(p / "materials.csv")

print("\nINVENTORY MODEL REPORT")

print("\nTransaction types:")
print(inventory["transaction_type"].value_counts())

print("\nReplenishment quantity:")
print(
    inventory[
        inventory["transaction_type"] == "Replenishment"
    ]["quantity"].describe()
)

print("\nInventory balance validation:")

for material_id in materials["material_id"]:

    ledger = inventory[
        inventory["material_id"] == material_id
    ].copy()

    ledger["transaction_date"] = pd.to_datetime(
        ledger["transaction_date"]
    )

    ledger = ledger.sort_values(
        "transaction_date", kind="stable"
    )

    balance = ledger["quantity"].cumsum()

    assert (balance >= 0).all(), (
        f"Negative inventory: {material_id}"
    )

print("PASS | No negative inventory balances")

print("\nMaterial policy:")
print(
    materials[
        ["material_id", "initial_stock",
         "reorder_point", "lead_time_days"]
    ].head(10).to_string(index=False)
) 