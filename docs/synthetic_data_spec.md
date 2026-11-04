# OpsIQ — Synthetic Data Specification

## 1. Purpose

Generate realistic, reproducible manufacturing data for OpsIQ development and testing.

## 2. Datasets

### Machines
- machine_id (PK)
- machine_name
- machine_type
- capacity_per_hour
- operating_cost_per_hour
- efficiency_factor

### Materials
- material_id (PK)
- material_name
- unit
- initial_stock
- reorder_point
- unit_cost
- lead_time_days

### Production Orders
- order_id (PK)
- machine_id (FK)
- product
- planned_qty
- actual_qty
- start_time
- end_time
- status

### Downtime Events
- downtime_id (PK)
- machine_id (FK)
- order_id (FK, nullable)
- start_time
- end_time
- duration_min
- downtime_type
- reason

### Quality Inspections
- inspection_id (PK)
- order_id (FK)
- inspected_qty
- defective_qty
- defect_type
- inspection_date

### Inventory Transactions
- transaction_id (PK)
- material_id (FK)
- order_id (FK, nullable)
- transaction_type
- quantity
- transaction_date

## 3. Generation Parameters

- Duration: 90 days
- Machines: 10
- Materials: 30
- Production orders: 1,000
- Products: 3 families
- Random seed: 42

## 4. Relationships

- Production Orders → Machines
- Downtime Events → Machines and Production Orders
- Quality Inspections → Production Orders
- Inventory Transactions → Materials and optionally Production Orders

## 5. Simulation Patterns

- Machine-specific efficiency differences
- Planned and unplanned downtime
- Variable defect rates
- Material consumption
- Inventory replenishment
- Different production volumes

## 6. Data Quality Rules

- Identifiers must be unique.
- Foreign keys must reference existing records.
- Quantities cannot be negative.
- Defective quantities cannot exceed inspected quantities.
- Downtime duration must be positive.
- End timestamps cannot precede start timestamps.
- Dates must fall within the defined simulation period.

## 7. Reproducibility

Use a fixed random seed of 42 so that the same configuration generates repeatable datasets.

## 8. Data Classification

All generated records are synthetic and must never be represented as verified factory data.