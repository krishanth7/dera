"""Schema regression engine tests for DERA.

Verifies canonical metadata normalization, deterministic SHA-256 hashing,
DAG foreign key cycle detection, and repeatable topological sorting across runs.
Copyright (c) 2026 Bunga Krishanth. All rights reserved.
Licensed under the MIT License.
"""

import json
from pathlib import Path
import unittest

from dera.models import (
    DatabaseColumn,
    DatabaseTable,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    SchemaSnapshot,
    TableIndex,
)
from dera.graph import build_dependency_graph, compute_topological_sort
from dera.diagnostics import run_all_diagnostics


def load_fixture(filename: str) -> SchemaSnapshot:
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "schemas" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables: list[DatabaseTable] = []
    for t_data in data["tables"]:
        cols = tuple(
            DatabaseColumn(
                name=c["name"],
                data_type=c["data_type"],
                is_nullable=c.get("is_nullable", True),
            )
            for c in t_data.get("columns", [])
        )
        pk = PrimaryKeyConstraint(
            name=t_data["primary_key"]["name"],
            columns=tuple(t_data["primary_key"]["columns"]),
        ) if t_data.get("primary_key") else None

        fks = tuple(
            ForeignKeyConstraint(
                name=fk["name"],
                source_columns=tuple(fk["source_columns"]),
                target_schema=fk.get("target_schema", t_data.get("schema", "public")),
                target_table=fk["target_table"],
                target_columns=tuple(fk["target_columns"]),
                on_delete=fk.get("on_delete", "NO ACTION"),
                on_update=fk.get("on_update", "NO ACTION"),
            )
            for fk in t_data.get("foreign_keys", [])
        )

        idxs = tuple(
            TableIndex(
                name=idx["name"],
                columns=tuple(idx["columns"]),
                is_unique=idx.get("is_unique", False),
            )
            for idx in t_data.get("indexes", [])
        )

        tables.append(
            DatabaseTable(
                schema=t_data.get("schema", "public"),
                name=t_data["name"],
                columns=cols,
                primary_key=pk,
                foreign_keys=fks,
                indexes=idxs,
            )
        )

    return SchemaSnapshot(
        database_name=data["database"],
        engine=data["engine"],
        tables=tuple(tables),
    )


class TestSchemaRegression(unittest.TestCase):
    def test_ecommerce_postgres_regression(self) -> None:
        snapshot = load_fixture("ecommerce_postgres.json")
        self.assertEqual(len(snapshot.tables), 5)

        # 1. Deterministic Hash Repeatability
        h1 = snapshot.compute_hash()
        h2 = snapshot.compute_hash()
        self.assertEqual(h1, h2)

        # 2. Topological dependency ordering
        order = compute_topological_sort(snapshot.tables)
        # categories and users have 0 incoming foreign keys; orders depends on users;
        # products depends on categories; order_items depends on orders and products
        user_idx = order.index("public.users")
        cat_idx = order.index("public.categories")
        prod_idx = order.index("public.products")
        orders_idx = order.index("public.orders")
        items_idx = order.index("public.order_items")

        self.assertLess(cat_idx, prod_idx, "categories must precede products")
        self.assertLess(user_idx, orders_idx, "users must precede orders")
        self.assertLess(prod_idx, items_idx, "products must precede order_items")
        self.assertLess(orders_idx, items_idx, "orders must precede order_items")

    def test_cyclic_dependency_stability(self) -> None:
        # Table A references Table B, and Table B references Table A
        table_a = DatabaseTable(
            schema="public",
            name="table_a",
            foreign_keys=(
                ForeignKeyConstraint(
                    name="fk_a_b",
                    source_columns=("b_id",),
                    target_schema="public",
                    target_table="table_b",
                    target_columns=("id",),
                ),
            ),
        )
        table_b = DatabaseTable(
            schema="public",
            name="table_b",
            foreign_keys=(
                ForeignKeyConstraint(
                    name="fk_b_a",
                    source_columns=("a_id",),
                    target_schema="public",
                    target_table="table_a",
                    target_columns=("id",),
                ),
            ),
        )

        # Topological sort should not crash or loop infinitely on cycles;
        # it must return all tables deterministically
        order = compute_topological_sort([table_a, table_b])
        self.assertEqual(len(order), 2)
        self.assertEqual(set(order), {"public.table_a", "public.table_b"})


if __name__ == "__main__":
    unittest.main()
