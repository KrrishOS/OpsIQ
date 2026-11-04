# OpsIQ — Manufacturing Data Model

## 1. Purpose

Define the initial manufacturing dataset structure for OpsIQ's analytics, optimization, AI recommendation and simulation modules.

## 2. Dataset Definitions

| Dataset | Primary Identifier | Purpose |
|---|---|---|
| machines | machine_id | Machine specifications |
| production_orders | order_id | Planned and actual production |
| downtime | downtime_id | Machine stoppages |
| quality | inspection_id | Quality and defects |
| inventory | material_id | Material and stock information |

## 3. Relationships

- production_orders.machine_id → machines.machine_id
- downtime.machine_id → machines.machine_id
- downtime.order_id → production_orders.order_id
- quality.order_id → production_orders.order_id
- inventory.material_id → Material references in production records

## 4. Data Design Principles

- Use unique identifiers.
- Maintain consistent date and time formats.
- Avoid invalid quantities and negative values.
- Preserve relationships between datasets.
- Include realistic operational patterns.
- Make synthetic data reproducible using a fixed random seed.
- Distinguish generated data from verified operational data.

## 5. Intended Applications

- Production efficiency analysis
- Machine utilization
- Downtime analysis
- Defect analysis
- Inventory management
- Bottleneck detection
- Optimization
- Simulation-based validation