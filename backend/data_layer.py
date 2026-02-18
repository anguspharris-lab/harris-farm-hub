"""
Harris Farm Hub — Data Access Abstraction Layer
Provides a unified interface for data access across multiple backends.
All KPIs must be traceable to source data with ±0.01 precision.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import os


# ============================================================================
# ABSTRACT BASE CLASS
# ============================================================================

class DataSource(ABC):
    """
    Abstract base class for data access.
    All implementations must provide sales data and store lists.
    """

    @abstractmethod
    def get_sales_data(
        self,
        stores: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Retrieve aggregated sales data.

        Data grain: Store × Category × Day (rolled up from POS transactions)

        Args:
            stores: List of store names to filter by. None = all stores.
            categories: List of categories to filter by. None = all categories.
            date_from: Start date (inclusive). None = 90 days ago.
            date_to: End date (inclusive). None = today.

        Returns:
            DataFrame with columns:
                - date (datetime): Transaction date
                - store (str): Store name
                - category (str): Category name
                - revenue (float): Total revenue ($)
                - cogs (float): Cost of goods sold ($)
                - gross_profit (float): Gross profit ($)
                - margin_pct (float): Margin percentage (0-1 scale)
                - transactions (int): Number of transactions
                - avg_basket (float): Average basket value ($)
                - wastage_cost (float): Cost of wastage ($)
                - wastage_pct (float): Wastage percentage (0-100 scale)
                - oos_hours (float): Out-of-stock hours
                - oos_lost_sales (float): Estimated lost sales from OOS ($)
                - online_orders (int): Number of online orders
                - miss_picks (int): Number of miss-picks
        """
        pass

    @abstractmethod
    def get_store_list(self) -> List[str]:
        """
        Retrieve list of all store names.

        Returns:
            List of store names (21 Harris Farm Markets locations)
        """
        pass


# ============================================================================
# MOCK DATA SOURCE
# ============================================================================

class MockDataSource(DataSource):
    """
    Mock data source using deterministic seeded random generation.
    Replicates the data generation logic from sales_dashboard.py.
    Seed 42 for consistency across sessions.
    """

    # Harris Farm Markets store network (21 locations)
    STORES = [
        "Allambie Heights", "Bondi Beach", "Bondi Junction", "Brookvale",
        "Castle Hill", "Crows Nest", "Double Bay", "Drummoyne",
        "Edgecliff", "Gladesville", "Hornsby", "Leichhardt",
        "Lindfield", "Manly", "Miranda", "Neutral Bay",
        "North Sydney", "Parramatta", "Richmond", "Rozelle",
        "Willoughby",
    ]

    CATEGORIES = [
        "Fresh Produce", "Dairy", "Meat & Seafood",
        "Bakery", "Grocery", "Deli",
    ]

    # Base daily revenue per store per category (avg store, weekday)
    BASE_REVENUE = {
        "Fresh Produce": 4200,
        "Dairy": 1800,
        "Meat & Seafood": 3200,
        "Bakery": 1400,
        "Grocery": 2800,
        "Deli": 1600,
    }

    # Gross margin % by category
    BASE_MARGIN = {
        "Fresh Produce": 0.32,
        "Dairy": 0.22,
        "Meat & Seafood": 0.28,
        "Bakery": 0.45,
        "Grocery": 0.25,
        "Deli": 0.38,
    }

    # Wastage rate (% of COGS lost to spoilage/markdowns)
    BASE_WASTAGE_RATE = {
        "Fresh Produce": 0.08,
        "Dairy": 0.04,
        "Meat & Seafood": 0.06,
        "Bakery": 0.12,
        "Grocery": 0.01,
        "Deli": 0.07,
    }

    def __init__(self, seed: int = 42):
        """
        Initialize mock data source with deterministic seed.

        Args:
            seed: Random seed for reproducibility (default 42)
        """
        self.seed = seed
        self._data_cache = None

    def get_store_list(self) -> List[str]:
        """Return list of all Harris Farm Markets stores."""
        return self.STORES.copy()

    def get_sales_data(
        self,
        stores: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Generate mock aggregated transaction data.

        Source: simulated POS register data, aggregated to store/category/day grain.
        Seed 42 for deterministic results across sessions.
        All KPIs derived from these aggregates — no separate data sources.
        """
        # Generate full dataset if not cached
        if self._data_cache is None:
            self._data_cache = self._generate_full_dataset()

        df = self._data_cache.copy()

        # Apply date filters
        if date_to is None:
            date_to = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if date_from is None:
            date_from = date_to - timedelta(days=89)  # 90 days total

        df = df[(df['date'] >= date_from) & (df['date'] <= date_to)]

        # Apply store filter
        if stores is not None:
            if len(stores) == 0:
                # Empty list means no stores selected -> return empty DataFrame
                return pd.DataFrame(columns=df.columns)
            df = df[df['store'].isin(stores)]

        # Apply category filter
        if categories is not None:
            if len(categories) == 0:
                # Empty list means no categories selected -> return empty DataFrame
                return pd.DataFrame(columns=df.columns)
            df = df[df['category'].isin(categories)]

        return df.reset_index(drop=True)

    def _generate_full_dataset(self) -> pd.DataFrame:
        """
        Generate the complete mock dataset for 90 days.
        Each row = 1 store × 1 category × 1 day, rolled up from individual baskets.
        """
        rng = np.random.RandomState(self.seed)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dates = pd.date_range(end=today, periods=90, freq='D')

        # Store size multiplier (relative trading volume)
        store_size = {}
        for s in self.STORES:
            store_size[s] = rng.uniform(0.7, 1.3)

        # Flagship/high-traffic stores get higher multipliers
        for big in ["Bondi Beach", "Crows Nest", "Manly", "Castle Hill", "Leichhardt"]:
            if big in store_size:
                store_size[big] = rng.uniform(1.2, 1.5)

        data = []
        for date in dates:
            dow = date.dayofweek
            weekend_mult = 1.35 if dow >= 5 else 1.0
            trend_mult = 1.0 + (date - dates[0]).days * 0.001  # ~0.1%/day growth

            for store in self.STORES:
                for category in self.CATEGORIES:
                    base_rev = self.BASE_REVENUE[category]
                    sm = store_size[store]

                    # Calculate revenue
                    revenue = base_rev * sm * weekend_mult * trend_mult
                    revenue += rng.normal(0, revenue * 0.12)
                    revenue = max(0, round(revenue, 2))

                    # Calculate margin
                    margin_pct = self.BASE_MARGIN[category] + rng.normal(0, 0.03)
                    margin_pct = max(0.05, min(0.55, margin_pct))

                    # Calculate COGS and profit
                    cogs = revenue * (1 - margin_pct)
                    gross_profit = revenue - cogs

                    # Calculate transactions and basket size
                    transactions = max(1, int(revenue / rng.uniform(35, 55)))

                    # Wastage: cost of spoiled/discarded product
                    wastage_rate = self.BASE_WASTAGE_RATE[category] + rng.normal(0, 0.02)
                    wastage_rate = max(0, min(0.25, wastage_rate))
                    wastage_cost = cogs * wastage_rate

                    # Out-of-stock: hours a shelf was empty (15% chance per store/cat/day)
                    oos_hours = 0.0
                    if rng.random() < 0.15:
                        oos_hours = min(24.0, rng.exponential(4))
                    oos_lost_sales = oos_hours * (revenue / 14)  # ~14 trading hrs/day

                    # Online orders (subset of transactions) and miss-picks
                    online_orders = max(0, int(transactions * rng.uniform(0.08, 0.18)))
                    miss_picks = 0
                    if online_orders > 0:
                        miss_pick_rate = rng.uniform(0.02, 0.07)
                        miss_picks = int(online_orders * miss_pick_rate)

                    data.append({
                        "date": date,
                        "store": store,
                        "category": category,
                        "revenue": revenue,
                        "cogs": round(cogs, 2),
                        "gross_profit": round(gross_profit, 2),
                        "margin_pct": round(margin_pct, 4),
                        "transactions": transactions,
                        "avg_basket": round(revenue / transactions, 2) if transactions > 0 else 0,
                        "wastage_cost": round(wastage_cost, 2),
                        "wastage_pct": round(wastage_rate * 100, 1),
                        "oos_hours": round(oos_hours, 1),
                        "oos_lost_sales": round(oos_lost_sales, 2),
                        "online_orders": online_orders,
                        "miss_picks": miss_picks,
                    })

        return pd.DataFrame(data)


# ============================================================================
# MICROSOFT FABRIC DATA SOURCE
# ============================================================================

class FabricDataSource(DataSource):
    """
    Microsoft Fabric data source for production deployment.
    Connects to Azure Data Lake via Fabric APIs.
    Not yet implemented — stub for future integration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Fabric data source.

        Args:
            config: Configuration dictionary with connection details
                    (workspace_id, lakehouse_id, etc.)
        """
        self.config = config or {}

    def get_sales_data(
        self,
        stores: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Retrieve sales data from Microsoft Fabric.
        NOT YET IMPLEMENTED.
        """
        raise NotImplementedError(
            "FabricDataSource.get_sales_data() is not yet implemented. "
            "This is a placeholder for future Fabric integration."
        )

    def get_store_list(self) -> List[str]:
        """
        Retrieve store list from Microsoft Fabric.
        NOT YET IMPLEMENTED.
        """
        raise NotImplementedError(
            "FabricDataSource.get_store_list() is not yet implemented. "
            "This is a placeholder for future Fabric integration."
        )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_data_source(db_type: Optional[str] = None) -> DataSource:
    """
    Factory function to create appropriate data source.

    Args:
        db_type: Data source type. Options:
                 - "mock" (default): MockDataSource with seed 42
                 - "fabric": FabricDataSource (not yet implemented)
                 If None, reads from DB_TYPE environment variable.

    Returns:
        DataSource instance

    Raises:
        ValueError: If db_type is not recognized

    Example:
        >>> source = get_data_source()  # defaults to mock
        >>> df = source.get_sales_data(
        ...     stores=["Bondi Beach", "Manly"],
        ...     categories=["Fresh Produce"],
        ...     date_from=datetime(2024, 1, 1),
        ...     date_to=datetime(2024, 1, 31)
        ... )
    """
    if db_type is None:
        db_type = os.environ.get("DB_TYPE", "mock").lower()
    else:
        db_type = db_type.lower()

    if db_type == "mock":
        return MockDataSource(seed=42)
    elif db_type == "fabric":
        return FabricDataSource()
    else:
        raise ValueError(
            f"Unknown DB_TYPE: {db_type}. "
            f"Valid options: 'mock', 'fabric'"
        )
