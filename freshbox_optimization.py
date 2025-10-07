"""FreshBox Logistics cost optimization analysis.

This script reproduces the Excel-based scenario in Python using only the
standard library. It calculates key metrics, optionally generates a trend
chart (if matplotlib is available), and surfaces optimization insights for the
FreshBox Logistics operations data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional, Sequence

import importlib.util


DATA = {
    "Month": ["April", "May", "June", "July", "August", "September"],
    "Fuel Cost ($)": [88500, 92000, 91200, 95800, 97500, 93000],
    "Truck Maintenance ($)": [24000, 22500, 26000, 28000, 30000, 27500],
    "Labor Cost ($)": [132000, 134500, 137000, 135000, 138500, 136000],
    "Warehouse Cost ($)": [76000, 78000, 80000, 82500, 85000, 83000],
    "Deliveries Made": [12300, 12800, 13000, 13400, 13700, 13100],
    "Avg. Delivery Time (hrs)": [2.5, 2.4, 2.6, 2.7, 2.8, 2.6],
    "% On-Time Deliveries": [0.94, 0.95, 0.93, 0.92, 0.91, 0.93],
}

@dataclass
class MonthRecord:
    month: str
    fuel_cost: float
    maintenance_cost: float
    labor_cost: float
    warehouse_cost: float
    deliveries_made: int
    avg_delivery_time: float
    on_time_rate: float
    total_operating_cost: float
    cost_per_delivery: float
    fuel_flag: bool
    on_time_flag: bool

    @classmethod
    def from_raw(cls, index: int, data: Dict[str, Sequence]) -> "MonthRecord":
        fuel_cost = data["Fuel Cost ($)"][index]
        maintenance_cost = data["Truck Maintenance ($)"][index]
        labor_cost = data["Labor Cost ($)"][index]
        warehouse_cost = data["Warehouse Cost ($)"][index]
        deliveries_made = data["Deliveries Made"][index]
        total_operating_cost = fuel_cost + maintenance_cost + labor_cost + warehouse_cost
        cost_per_delivery = total_operating_cost / deliveries_made
        on_time_rate = data["% On-Time Deliveries"][index]

        return cls(
            month=data["Month"][index],
            fuel_cost=fuel_cost,
            maintenance_cost=maintenance_cost,
            labor_cost=labor_cost,
            warehouse_cost=warehouse_cost,
            deliveries_made=deliveries_made,
            avg_delivery_time=data["Avg. Delivery Time (hrs)"][index],
            on_time_rate=on_time_rate,
            total_operating_cost=total_operating_cost,
            cost_per_delivery=cost_per_delivery,
            fuel_flag=fuel_cost > 95_000,
            on_time_flag=on_time_rate < 0.93,
        )


@dataclass
class AnalysisResults:
    records: List[MonthRecord]
    averages: Dict[str, float]
    optimization_target: str
    recommendation: str
    chart_path: Optional[Path]


def build_records(data: Dict[str, Sequence]) -> List[MonthRecord]:
    return [MonthRecord.from_raw(i, data) for i in range(len(data["Month"]))]


def generate_cost_trend_chart(records: Sequence[MonthRecord], output_dir: Path) -> Optional[Path]:
    if importlib.util.find_spec("matplotlib") is None:
        return None

    import matplotlib.pyplot as plt  # type: ignore

    months = [r.month for r in records]
    fuel = [r.fuel_cost for r in records]
    maintenance = [r.maintenance_cost for r in records]
    labor = [r.labor_cost for r in records]
    warehouse = [r.warehouse_cost for r in records]

    plt.figure(figsize=(10, 6))
    plt.plot(months, fuel, marker="o", label="Fuel Cost ($)")
    plt.plot(months, maintenance, marker="o", label="Truck Maintenance ($)")
    plt.plot(months, labor, marker="o", label="Labor Cost ($)")
    plt.plot(months, warehouse, marker="o", label="Warehouse Cost ($)")

    plt.title("FreshBox Logistics - Monthly Cost Trends")
    plt.xlabel("Month")
    plt.ylabel("Cost (USD)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "freshbox_cost_trends.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    return chart_path


def identify_highest_cost_per_delivery(records: Sequence[MonthRecord]) -> MonthRecord:
    return max(records, key=lambda r: r.cost_per_delivery)


def summarize_costs(records: Sequence[MonthRecord]) -> Dict[str, float]:
    return {
        "Fuel Cost ($)": mean(r.fuel_cost for r in records),
        "Truck Maintenance ($)": mean(r.maintenance_cost for r in records),
        "Labor Cost ($)": mean(r.labor_cost for r in records),
        "Warehouse Cost ($)": mean(r.warehouse_cost for r in records),
    }


def identify_optimization_target(records: Sequence[MonthRecord]) -> str:
    stats = {}
    for label, values in {
        "Fuel Cost ($)": [r.fuel_cost for r in records],
        "Truck Maintenance ($)": [r.maintenance_cost for r in records],
        "Labor Cost ($)": [r.labor_cost for r in records],
        "Warehouse Cost ($)": [r.warehouse_cost for r in records],
    }.items():
        avg = mean(values)
        variation = pstdev(values)
        coeff_var = variation / avg if avg else 0.0
        stats[label] = coeff_var
    return max(stats, key=stats.get)


def create_recommendation(target: str) -> str:
    if target == "Fuel Cost ($)":
        return (
            "Fuel costs show the highest volatility. Negotiate bulk fuel contracts, "
            "optimize routing, and increase driver coaching on fuel-efficient practices "
            "to stabilize spending."
        )
    if target == "Truck Maintenance ($)":
        return (
            "Maintenance expenses fluctuate notably. Implement predictive maintenance "
            "using telematics data and schedule off-peak service windows to reduce "
            "emergency repairs."
        )
    if target == "Labor Cost ($)":
        return (
            "Labor costs vary the most. Review staffing models, expand cross-training, "
            "and explore incentives tied to delivery efficiency to curb overtime."
        )
    if target == "Warehouse Cost ($)":
        return (
            "Warehouse spending has the highest variation. Optimize space utilization, "
            "negotiate energy rates, and pilot automation for repetitive handling tasks."
        )
    return "Focus on the identified category to develop targeted efficiency initiatives."


def run_analysis() -> AnalysisResults:
    records = build_records(DATA)
    chart_path = generate_cost_trend_chart(records, Path("outputs"))
    averages = summarize_costs(records)
    optimization_target = identify_optimization_target(records)
    recommendation = create_recommendation(optimization_target)
    return AnalysisResults(
        records=records,
        averages=averages,
        optimization_target=optimization_target,
        recommendation=recommendation,
        chart_path=chart_path,
    )


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.0%}"


def display_records(records: Sequence[MonthRecord]) -> None:
    headers = [
        "Month",
        "Fuel Cost ($)",
        "Truck Maintenance ($)",
        "Labor Cost ($)",
        "Warehouse Cost ($)",
        "Total Operating Cost ($)",
        "Deliveries Made",
        "Cost per Delivery ($)",
        "Avg. Delivery Time (hrs)",
        "% On-Time Deliveries",
        "Fuel Flag",
        "On-Time Flag",
    ]
    print(" ".join(h.ljust(22) for h in headers))
    for record in records:
        row = [
            record.month.ljust(22),
            format_currency(record.fuel_cost).ljust(22),
            format_currency(record.maintenance_cost).ljust(22),
            format_currency(record.labor_cost).ljust(22),
            format_currency(record.warehouse_cost).ljust(22),
            format_currency(record.total_operating_cost).ljust(22),
            str(record.deliveries_made).ljust(22),
            format_currency(record.cost_per_delivery).ljust(22),
            f"{record.avg_delivery_time:.1f}".ljust(22),
            format_percent(record.on_time_rate).ljust(22),
            str(record.fuel_flag).ljust(22),
            str(record.on_time_flag).ljust(22),
        ]
        print(" ".join(row))


def display_results(results: AnalysisResults) -> None:
    print("FreshBox Logistics - Cost Optimization Analysis\n")
    print("Monthly Metrics:")
    display_records(results.records)

    highest = identify_highest_cost_per_delivery(results.records)
    print("\nHighest Cost per Delivery:")
    print(f"Month: {highest.month}")
    print(f"Cost per Delivery: {format_currency(highest.cost_per_delivery)}")
    component_values = {
        "Fuel Cost ($)": highest.fuel_cost,
        "Truck Maintenance ($)": highest.maintenance_cost,
        "Labor Cost ($)": highest.labor_cost,
        "Warehouse Cost ($)": highest.warehouse_cost,
    }
    top_component = max(component_values, key=component_values.get)
    print(f"Top Cost Component: {top_component} ({format_currency(component_values[top_component])})")

    print("\nAverage Monthly Cost by Category:")
    for label, value in results.averages.items():
        print(f"{label}: {format_currency(value)}")

    print("\nOptimization Focus:")
    print(results.optimization_target)
    print(results.recommendation)

    if results.chart_path is None:
        print("\nmatplotlib is not available; skipping trend chart generation.")
    else:
        print(f"\nTrend chart saved to: {results.chart_path}")


if __name__ == "__main__":
    analysis_results = run_analysis()
    display_results(analysis_results)
