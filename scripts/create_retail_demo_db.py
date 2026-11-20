#!/usr/bin/env python3
"""Create a deterministic, fully synthetic Brazilian marketplace DuckDB demo."""

from __future__ import annotations

import argparse
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import duckdb

SEED = 20261119
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "sample_data" / "retail_demo.duckdb"
STATES = [
    ("SP", "São Paulo"),
    ("RJ", "Rio de Janeiro"),
    ("MG", "Belo Horizonte"),
    ("RS", "Porto Alegre"),
    ("PR", "Curitiba"),
    ("BA", "Salvador"),
    ("SC", "Florianópolis"),
    ("GO", "Goiânia"),
    ("PE", "Recife"),
    ("CE", "Fortaleza"),
]
CATEGORIES = [
    ("bed_bath", "Bed & Bath", 45.0, 650.0),
    ("computers", "Computers", 120.0, 4800.0),
    ("electronics", "Electronics", 35.0, 3200.0),
    ("fashion", "Fashion", 25.0, 550.0),
    ("furniture", "Furniture", 180.0, 5200.0),
    ("health_beauty", "Health & Beauty", 18.0, 750.0),
    ("home_decor", "Home Decor", 22.0, 1400.0),
    ("sports", "Sports & Leisure", 30.0, 1800.0),
    ("toys", "Toys", 20.0, 620.0),
    ("watches", "Watches & Gifts", 55.0, 2400.0),
]
PAYMENT_TYPES = ["credit_card", "boleto", "debit_card", "voucher"]
ORDER_STATUSES = ["delivered", "shipped", "canceled", "unavailable", "processing"]
STATUS_WEIGHTS = [0.925, 0.027, 0.026, 0.009, 0.013]
REVIEW_TEXT = [
    (5, "Tudo certo", "Produto chegou em boas condições e dentro do prazo."),
    (5, "Muito bom", "Compra simples e produto conforme a descrição."),
    (4, "Boa experiência", "Produto correto; a entrega poderia ser um pouco mais rápida."),
    (3, "Regular", "Atendeu ao esperado, embora a comunicação pudesse melhorar."),
    (2, "Atraso", "O pedido demorou mais que o previsto para chegar."),
    (1, "Problema com a entrega", "A experiência de entrega ficou abaixo do esperado."),
]


def timestamp(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


def make_database(output: Path, order_count: int, seed: int) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing database: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    con = duckdb.connect(str(output))
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute(
            """
            CREATE TABLE customers (
                customer_id VARCHAR PRIMARY KEY,
                customer_unique_id VARCHAR NOT NULL UNIQUE,
                city VARCHAR NOT NULL,
                state VARCHAR NOT NULL
            );
            CREATE TABLE sellers (
                seller_id VARCHAR PRIMARY KEY,
                city VARCHAR NOT NULL,
                state VARCHAR NOT NULL
            );
            CREATE TABLE products (
                product_id VARCHAR PRIMARY KEY,
                category VARCHAR NOT NULL,
                category_name VARCHAR NOT NULL,
                weight_g INTEGER NOT NULL,
                price_brl DECIMAL(12, 2) NOT NULL
            );
            CREATE TABLE orders (
                order_id VARCHAR PRIMARY KEY,
                customer_id VARCHAR NOT NULL REFERENCES customers(customer_id),
                order_status VARCHAR NOT NULL,
                purchase_timestamp TIMESTAMP NOT NULL,
                approved_at TIMESTAMP,
                carrier_pickup_at TIMESTAMP,
                delivered_at TIMESTAMP,
                estimated_delivery_at TIMESTAMP NOT NULL,
                total_amount_brl DECIMAL(12, 2) NOT NULL
            );
            CREATE TABLE order_items (
                order_id VARCHAR NOT NULL REFERENCES orders(order_id),
                order_item_id INTEGER NOT NULL,
                product_id VARCHAR NOT NULL REFERENCES products(product_id),
                seller_id VARCHAR NOT NULL REFERENCES sellers(seller_id),
                shipping_limit_at TIMESTAMP NOT NULL,
                price_brl DECIMAL(12, 2) NOT NULL,
                freight_value_brl DECIMAL(12, 2) NOT NULL,
                PRIMARY KEY (order_id, order_item_id)
            );
            CREATE TABLE payments (
                order_id VARCHAR NOT NULL REFERENCES orders(order_id),
                payment_sequential INTEGER NOT NULL,
                payment_type VARCHAR NOT NULL,
                installments INTEGER NOT NULL,
                payment_value_brl DECIMAL(12, 2) NOT NULL,
                payment_status VARCHAR NOT NULL,
                PRIMARY KEY (order_id, payment_sequential)
            );
            CREATE TABLE reviews (
                review_id VARCHAR PRIMARY KEY,
                order_id VARCHAR NOT NULL UNIQUE REFERENCES orders(order_id),
                review_score INTEGER NOT NULL,
                review_title VARCHAR NOT NULL,
                review_message VARCHAR NOT NULL,
                review_created_at TIMESTAMP NOT NULL
            );
            """
        )

        customer_count = max(1, min(7000, round(order_count * 0.68)))
        customers = []
        for i in range(1, customer_count + 1):
            state, city = rng.choice(STATES)
            customers.append((f"cust_{i:06d}", f"buyer_{i:06d}", city, state))
        con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

        seller_count = max(30, min(100, order_count // 100))
        sellers = []
        for i in range(1, seller_count + 1):
            state, city = rng.choice(STATES)
            sellers.append((f"seller_{i:04d}", city, state))
        con.executemany("INSERT INTO sellers VALUES (?, ?, ?)", sellers)

        product_count = max(100, min(500, order_count // 20))
        products = []
        for i in range(1, product_count + 1):
            category, category_name, low, high = rng.choice(CATEGORIES)
            price = round(rng.triangular(low, high, low * 1.8), 2)
            products.append((f"prod_{i:05d}", category, category_name, rng.randint(100, 18000), price))
        con.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

        customers_by_id = [row[0] for row in customers]
        sellers_by_id = [row[0] for row in sellers]
        order_rows = []
        item_rows = []
        payment_rows = []
        review_rows = []
        start_day = date(2017, 1, 1)
        span_days = 608  # 2017-01 through 2018-08, consistent with the public reference period.

        for i in range(1, order_count + 1):
            order_id = f"order_{i:07d}"
            customer_id = rng.choice(customers_by_id)
            purchase_day = start_day + timedelta(days=rng.randrange(span_days))
            purchase_at = timestamp(purchase_day, rng.randrange(24), rng.randrange(60))
            approved_at = purchase_at + timedelta(hours=rng.randint(1, 20))
            status = rng.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
            estimated_at = timestamp(purchase_day + timedelta(days=rng.randint(8, 32)), 18)
            carrier_at = None
            delivered_at = None

            if status in {"shipped", "delivered"}:
                carrier_at = approved_at + timedelta(days=rng.randint(1, 4))
            if status == "delivered":
                delivered_at = carrier_at + timedelta(days=rng.randint(1, 24))

            item_count = rng.choices([1, 2, 3, 4], weights=[0.70, 0.22, 0.065, 0.015], k=1)[0]
            order_total = 0.0
            for item_n in range(1, item_count + 1):
                product = rng.choice(products)
                price = round(product[4] * rng.uniform(0.88, 1.12), 2)
                freight = round(rng.uniform(7.0, 62.0) + product[3] / 2500.0, 2)
                order_total += price + freight
                item_rows.append(
                    (
                        order_id,
                        item_n,
                        product[0],
                        rng.choice(sellers_by_id),
                        approved_at + timedelta(days=rng.randint(1, 5)),
                        price,
                        freight,
                    )
                )
            order_total = round(order_total, 2)
            order_rows.append(
                (
                    order_id,
                    customer_id,
                    status,
                    purchase_at,
                    approved_at,
                    carrier_at,
                    delivered_at,
                    estimated_at,
                    order_total,
                )
            )

            # Split a small share across two payment methods; every order's
            # payment total exactly matches its item and freight total.
            split_payment = order_total >= 100 and rng.random() < 0.07
            first_value = round(order_total * rng.uniform(0.25, 0.75), 2) if split_payment else order_total
            values = [first_value, round(order_total - first_value, 2)] if split_payment else [order_total]
            for seq, value in enumerate(values, 1):
                payment_rows.append(
                    (
                        order_id,
                        seq,
                        rng.choices(PAYMENT_TYPES, weights=[0.72, 0.17, 0.08, 0.03], k=1)[0],
                        rng.randint(1, 10) if rng.random() < 0.52 else 1,
                        value,
                        "refunded" if status in {"canceled", "unavailable"} else "captured",
                    )
                )

            if status == "delivered" and rng.random() < 0.76:
                late = delivered_at.date() > estimated_at.date()
                possible_reviews = [row for row in REVIEW_TEXT if (row[0] <= 3) == late]
                score, title, message = rng.choice(possible_reviews)
                review_rows.append(
                    (
                        f"review_{i:07d}",
                        order_id,
                        score,
                        title,
                        message,
                        delivered_at + timedelta(days=rng.randint(1, 14)),
                    )
                )

        con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", order_rows)
        con.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?)", item_rows)
        con.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)", payment_rows)
        con.executemany("INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?)", review_rows)
        con.execute("COMMIT")

        checks = {
            "orders": con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == order_count,
            "item totals": con.execute(
                """
                SELECT COUNT(*) FROM orders o
                WHERE ABS(o.total_amount_brl - (
                    SELECT SUM(i.price_brl + i.freight_value_brl)
                    FROM order_items i WHERE i.order_id = o.order_id
                )) > 0.001
                """
            ).fetchone()[0]
            == 0,
            "payment totals": con.execute(
                """
                SELECT COUNT(*) FROM orders o
                WHERE ABS(o.total_amount_brl - (
                    SELECT SUM(p.payment_value_brl)
                    FROM payments p WHERE p.order_id = o.order_id
                )) > 0.001
                """
            ).fetchone()[0]
            == 0,
            "delivery timestamps": con.execute(
                """
                SELECT COUNT(*) FROM orders
                WHERE (order_status = 'delivered' AND delivered_at IS NULL)
                   OR (order_status <> 'delivered' AND delivered_at IS NOT NULL)
                   OR (delivered_at IS NOT NULL AND delivered_at < carrier_pickup_at)
                """
            ).fetchone()[0]
            == 0,
            "foreign keys": con.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM order_items i LEFT JOIN products p USING (product_id) WHERE p.product_id IS NULL)
                  + (SELECT COUNT(*) FROM order_items i LEFT JOIN sellers s USING (seller_id) WHERE s.seller_id IS NULL)
                  + (SELECT COUNT(*) FROM orders o LEFT JOIN customers c USING (customer_id) WHERE c.customer_id IS NULL)
                """
            ).fetchone()[0]
            == 0,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise RuntimeError("Data validation failed: " + ", ".join(failed))

        print(f"Created {output}")
        for table, in con.execute("SHOW TABLES").fetchall():
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(f"{table}: {count:,} rows")
        print(f"Validation passed: {', '.join(checks)}")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        con.close()
        output.unlink(missing_ok=True)
        raise
    finally:
        try:
            con.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--orders", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if args.orders < 1:
        parser.error("--orders must be greater than zero")
    make_database(args.output.expanduser().resolve(), args.orders, args.seed)


if __name__ == "__main__":
    main()
