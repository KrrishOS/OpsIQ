
"""
OpsIQ - Synthetic Manufacturing Data Generator
Version: 1.0
Purpose: Generate reproducible, connected manufacturing datasets.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# ==================================================
# 1. CONFIGURATION
# ==================================================

SEED = 42
TOTAL_ORDERS = 1000
TOTAL_DAYS = 90

START_DATE = pd.Timestamp("2026-01-01")

rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS = ["Staples", "Scissors", "Knives"]
MACHINE_IDS = [f"M{i:02d}" for i in range(1, 11)]
MATERIAL_IDS = [f"MAT{i:03d}" for i in range(1, 31)]


# ==================================================
# 2. MACHINE MASTER DATA
# ==================================================

machines = pd.DataFrame({
    "machine_id": MACHINE_IDS,
    "machine_name": [f"Machine {i}" for i in range(1, 11)],
    "machine_type": rng.choice(
        ["Press", "Cutting", "Assembly"], 10
    ),
    "capacity_per_hour": rng.integers(100, 181, 10),
    "operating_cost_per_hour": rng.integers(300, 801, 10),
    "efficiency_factor": [
        0.94, 0.92, 0.76, 0.96, 0.90,
        0.93, 0.84, 0.95, 0.91, 0.97
    ]
})

machine_lookup = machines.set_index("machine_id")


# ==================================================
# 3. MATERIAL MASTER DATA
# ==================================================

materials = pd.DataFrame({
    "material_id": MATERIAL_IDS,
    "material_name": [
        f"Material {i}" for i in range(1, 31)
    ],
    "unit": ["kg"] * 30,
    "initial_stock": rng.integers(3000, 6001, 30),
    "reorder_point": rng.integers(500, 1201, 30),
    "unit_cost": rng.integers(40, 301, 30),
    "lead_time_days": rng.integers(2, 11, 30)
})

material_lookup = materials.set_index("material_id")


# ==================================================
# 4. BILL OF MATERIALS
# ==================================================

bom_rows = []

for product_index, product in enumerate(PRODUCTS):

    for j in range(4):

        bom_rows.append({
            "product": product,
            "material_id": MATERIAL_IDS[
                product_index * 4 + j
            ],
            "quantity_per_unit": round(
                rng.uniform(0.01, 0.08), 3
            )
        })

bom = pd.DataFrame(bom_rows)

bom_lookup = {
    product: group.to_dict("records")
    for product, group in bom.groupby("product")
}


# ==================================================
# 5. PRODUCTION ORDERS
# ==================================================

production_rows = []
downtime_rows = []

for i in range(TOTAL_ORDERS):

    order_id = f"O{i + 1:04d}"

    machine_id = str(rng.choice(MACHINE_IDS))
    machine = machine_lookup.loc[machine_id]

    product = str(rng.choice(PRODUCTS))

    planned_qty = int(rng.integers(300, 701))

    order_date = START_DATE + pd.Timedelta(
        days=int(rng.integers(0, TOTAL_DAYS))
    )

    start_time = order_date + pd.Timedelta(
        minutes=int(rng.integers(420, 901))
    )

    # Machine-specific downtime probability
    downtime_probability = (
        0.45 if machine_id == "M03" else 0.25
    )

    has_downtime = rng.random() < downtime_probability

    downtime_min = (
        int(rng.integers(10, 91))
        if has_downtime else 0
    )

    capacity = machine["capacity_per_hour"]
    efficiency = machine["efficiency_factor"]

    run_minutes_estimate = (
        planned_qty / (capacity * efficiency) * 60
    )

    actual_qty = int(np.clip(
        planned_qty * efficiency
        - downtime_min * capacity / 60 * 0.4
        + rng.normal(0, planned_qty * 0.025),
        planned_qty * 0.65,
        planned_qty * 1.03
    ))

    run_minutes = (
        actual_qty / (capacity * efficiency) * 60
    )

    end_time = start_time + pd.Timedelta(
        minutes=run_minutes + downtime_min
    )

    production_rows.append({
        "order_id": order_id,
        "machine_id": machine_id,
        "product": product,
        "planned_qty": planned_qty,
        "actual_qty": actual_qty,
        "start_time": start_time,
        "end_time": end_time,
        "status": "Completed"
    })

    # Generate downtime event
    if downtime_min > 0:

        max_offset = max(0, run_minutes - downtime_min)

        offset = rng.uniform(0, max_offset)

        event_start = start_time + pd.Timedelta(
            minutes=offset
        )

        event_end = event_start + pd.Timedelta(
            minutes=downtime_min
        )

        downtime_rows.append({
            "downtime_id": f"D{len(downtime_rows) + 1:04d}",
            "machine_id": machine_id,
            "order_id": order_id,
            "start_time": event_start,
            "end_time": event_end,
            "duration_min": downtime_min,
            "downtime_type": str(rng.choice([
                "Mechanical", "Electrical", "Operational"
            ])),
            "reason": str(rng.choice([
                "Component failure",
                "Power issue",
                "Setup delay"
            ]))
        })


production = pd.DataFrame(production_rows)
downtime = pd.DataFrame(downtime_rows)


# ==================================================
# 6. QUALITY INSPECTIONS
# ==================================================

quality_rows = []

PRODUCT_DEFECT_RATES = {
    "Staples": 0.015,
    "Scissors": 0.020,
    "Knives": 0.025
}

for order in production_rows:

    base_rate = PRODUCT_DEFECT_RATES[order["product"]]

    machine_penalty = (
        0.018 if order["machine_id"] == "M03" else 0
    )

    defect_rate = min(base_rate + machine_penalty, 0.20)

    inspected_qty = order["actual_qty"]

    defective_qty = int(
        rng.binomial(inspected_qty, defect_rate)
    )

    quality_rows.append({
        "inspection_id": f"Q{len(quality_rows) + 1:04d}",
        "order_id": order["order_id"],
        "inspected_qty": inspected_qty,
        "defective_qty": defective_qty,
        "defect_type": (
            str(rng.choice([
                "Dimensional", "Surface", "Assembly"
            ]))
            if defective_qty > 0 else "No Defect"
        ),
        "inspection_date": order["end_time"]
    })

quality = pd.DataFrame(quality_rows)


# ==================================================
# 6.5. DEMAND-BASED INVENTORY POLICY
# ==================================================

# Estimate daily material demand from production orders and BOM.
demand_rows = []

for order in production_rows:

    order_date = pd.Timestamp(order["start_time"]).normalize()

    for component in bom_lookup[order["product"]]:

        demand_rows.append({
            "date": order_date,
            "material_id": component["material_id"],
            "demand": round(
                order["actual_qty"]
                * component["quantity_per_unit"], 2
            )
        })

daily_demand = pd.DataFrame(demand_rows)

daily_demand = daily_demand.groupby(
    ["date", "material_id"]
)["demand"].sum()

# Include days with zero consumption.
date_range = pd.date_range(
    START_DATE,
    START_DATE + pd.Timedelta(days=TOTAL_DAYS - 1),
    freq="D"
)

for index, material in materials.iterrows():

    material_id = material["material_id"]
    lead_time = int(material["lead_time_days"])

    try:
        demand_series = daily_demand.xs(
            material_id, level="material_id"
        )
    except KeyError:
        demand_series = pd.Series(dtype=float)

    demand_series = demand_series.reindex(
        date_range, fill_value=0
    )

    average_daily_demand = demand_series.mean()
    daily_demand_std = demand_series.std(ddof=0)
    maximum_daily_demand = demand_series.max()

    # 95% approximate service-level safety stock.
    safety_stock = (
        1.65 * daily_demand_std * np.sqrt(lead_time)
    )

    # Include a daily batch-demand buffer because production
    # orders can arrive in clusters.
    reorder_point = int(np.ceil(
        average_daily_demand * lead_time
        + safety_stock
        + maximum_daily_demand
    ))

    # Start with enough stock to cover the initial lead-time
    # protection period.
    initial_stock = max(
        int(material["initial_stock"]),
        int(np.ceil(
            reorder_point
            + average_daily_demand * lead_time
        ))
    )

    materials.loc[index, "reorder_point"] = reorder_point
    materials.loc[index, "initial_stock"] = initial_stock

# Refresh lookup because material values have changed.
material_lookup = materials.set_index("material_id")


#
# ==================================================
# 7. INVENTORY TRANSACTIONS - LEAD-TIME AWARE MODEL
# ==================================================

transactions = []

stock = {
    row.material_id: int(row.initial_stock)
    for row in materials.itertuples()
}

# Track one pending replenishment per material.
pending_orders = {}

# Opening stock transactions
for material in materials.itertuples():

    transactions.append({
        "transaction_id": f"T{len(transactions) + 1:05d}",
        "material_id": material.material_id,
        "order_id": None,
        "transaction_type": "Opening Receipt",
        "quantity": material.initial_stock,
        "transaction_date": START_DATE
    })


# Process production orders chronologically
sorted_orders = sorted(
    production_rows,
    key=lambda order: order["start_time"]
)

for order in sorted_orders:

    for component in bom_lookup[order["product"]]:

        material_id = component["material_id"]

        consumed_qty = round(
            order["actual_qty"]
            * component["quantity_per_unit"], 2
        )

        material = material_lookup.loc[material_id]

        # 1. Receive pending replenishment if delivery is due.
        pending = pending_orders.get(material_id)

        if pending and pending["delivery_date"] <= order["start_time"]:

            receipt_qty = pending["quantity"]

            transactions.append({
                "transaction_id": f"T{len(transactions) + 1:05d}",
                "material_id": material_id,
                "order_id": None,
                "transaction_type": "Replenishment",
                "quantity": receipt_qty,
                "transaction_date": pending["delivery_date"]
            })

            stock[material_id] += receipt_qty

            del pending_orders[material_id]

        # 2. Check whether sufficient material is available.
        if stock[material_id] < consumed_qty:

            raise ValueError(
                f"STOCKOUT: {material_id} | "
                f"Order: {order['order_id']} | "
                f"Available: {stock[material_id]} | "
                f"Required: {consumed_qty}"
            )

        # 3. Consume material.
        stock[material_id] -= consumed_qty

        transactions.append({
            "transaction_id": f"T{len(transactions) + 1:05d}",
            "material_id": material_id,
            "order_id": order["order_id"],
            "transaction_type": "Consumption",
            "quantity": -consumed_qty,
            "transaction_date": order["start_time"]
        })

        # 4. Place replenishment order if stock reaches reorder point.
        if (
            stock[material_id] <= material["reorder_point"]
            and material_id not in pending_orders
        ):

            receipt_qty = int(rng.integers(3000, 5001))

            delivery_date = (
                order["start_time"]
                + pd.Timedelta(days=int(material["lead_time_days"]))
            )

            pending_orders[material_id] = {
                "quantity": receipt_qty,
                "delivery_date": delivery_date
            }


# Record replenishments still in transit at the end
# of the production-order processing period.
for material_id, pending in pending_orders.items():

    transactions.append({
        "transaction_id": f"T{len(transactions) + 1:05d}",
        "material_id": material_id,
        "order_id": None,
        "transaction_type": "Replenishment",
        "quantity": pending["quantity"],
        "transaction_date": pending["delivery_date"]
    })


inventory = pd.DataFrame(transactions)



# ==================================================
# 8. DATA QUALITY VALIDATION
# ==================================================

# Primary key checks
assert machines["machine_id"].is_unique
assert materials["material_id"].is_unique
assert production["order_id"].is_unique
assert bom.set_index(
    ["product", "material_id"]
).index.is_unique

assert downtime["downtime_id"].is_unique
assert quality["inspection_id"].is_unique
assert inventory["transaction_id"].is_unique

# Foreign key checks
assert production["machine_id"].isin(
    machines["machine_id"]
).all()

assert downtime["machine_id"].isin(
    machines["machine_id"]
).all()

assert downtime["order_id"].isin(
    production["order_id"]
).all()

assert quality["order_id"].isin(
    production["order_id"]
).all()

assert bom["material_id"].isin(
    materials["material_id"]
).all()

assert inventory["material_id"].isin(
    materials["material_id"]
).all()

# Quantity checks
assert (production["planned_qty"] > 0).all()
assert (production["actual_qty"] > 0).all()

assert (
    quality["defective_qty"] <= quality["inspected_qty"]
).all()

assert (downtime["duration_min"] > 0).all()

# Timestamp checks
assert (
    production["end_time"] >= production["start_time"]
).all()

assert (
    downtime["end_time"] >= downtime["start_time"]
).all()

# Inventory transaction checks
consumption = inventory[
    inventory["transaction_type"] == "Consumption"
]

receipts = inventory[
    inventory["transaction_type"] != "Consumption"
]

assert (consumption["quantity"] < 0).all()
assert (receipts["quantity"] > 0).all()

# Inventory relationship validation

assert consumption["order_id"].notna().all()
assert receipts["order_id"].isna().all()

# Inventory reconciliation
for material_id in MATERIAL_IDS:

    ledger = inventory[
        inventory["material_id"] == material_id
    ].sort_values("transaction_date", kind="stable")

    balance = ledger["quantity"].cumsum()

    assert (balance >= 0).all(), (
        f"Negative stock detected: {material_id}"
    )

# One inspection per production order
assert len(quality) == len(production)

assert quality["order_id"].nunique() == len(production)


# ==================================================
# 9. EXPORT DATASETS
# ==================================================

datasets = {
    "machines": machines,
    "materials": materials,
    "bom": bom,
    "production_orders": production,
    "downtime": downtime,
    "quality_inspections": quality,
    "inventory_transactions": inventory
}

print("\n" + "=" * 45)
print("       OPSIQ DATA GENERATION REPORT")
print("=" * 45)

for name, dataframe in datasets.items():

    file_path = OUTPUT_DIR / f"{name}.csv"

    dataframe.to_csv(file_path, index=False)

    print(f"{name:<28} {len(dataframe):>7} records")

print("-" * 45)
print("All validation checks passed.")
print("All seven datasets exported successfully.")
print(f"Random seed: {SEED}")
print(f"Output: {OUTPUT_DIR}")
print("=" * 45)
