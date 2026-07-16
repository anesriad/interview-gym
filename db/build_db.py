"""Build db/practice.db from the schema + generated realistic data.

Run once (or anytime to reset):  python db/build_db.py

Uses a fixed random seed so the data is reproducible: the mentor's
"expected" answers stay stable across rebuilds.
"""
import os
import random
from datetime import date, datetime, timedelta

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "practice.db")
SCHEMA = os.path.join(HERE, "seed", "schema.sql")

random.seed(42)

CITIES = ["London", "Paris", "Berlin", "Madrid", "Lisbon"]
PLANS = ["free", "standard", "premium"]
METHODS = ["card", "wallet", "cash"]
GENRES = ["Drama", "Comedy", "Action", "Documentary", "Sci-Fi"]

INDUSTRIES = ["retail", "fintech", "healthcare", "media", "logistics"]
SUB_PLANS = ["starter", "growth", "enterprise"]
SUB_MRR = {"starter": 49.0, "growth": 199.0, "enterprise": 899.0}
INVOICE_STATUSES = ["paid", "outstanding", "refunded"]

START = date(2025, 1, 1)


def d(days_offset):
    return START + timedelta(days=days_offset)


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = duckdb.connect(DB_PATH)

    with open(SCHEMA) as f:
        con.execute(f.read())

    # ---- users: 500 users signing up across ~180 days ----
    users = []
    for uid in range(1, 501):
        signup = d(random.randint(0, 180))
        users.append((uid, signup, random.choice(CITIES),
                      random.choices(PLANS, weights=[5, 3, 2])[0]))
    con.executemany("INSERT INTO users VALUES (?,?,?,?)", users)

    # ---- trips: ~4000 trips, some cancelled ----
    trips, payments = [], []
    pid = 1
    for tid in range(1, 4001):
        uid = random.randint(1, 500)
        req = datetime(2025, 1, 1) + timedelta(
            days=random.randint(0, 200), minutes=random.randint(0, 1440))
        cancelled = random.random() < 0.12
        city = random.choice(CITIES)
        dist = round(random.uniform(0.8, 25.0), 2)
        fare = round(2.5 + dist * random.uniform(0.9, 1.8), 2)
        if cancelled:
            trips.append((tid, uid, req, None, city, dist, 0.0, "cancelled"))
        else:
            comp = req + timedelta(minutes=int(dist * random.uniform(2, 4)))
            trips.append((tid, uid, req, comp, city, dist, fare, "completed"))
            method = random.choice(METHODS)
            payments.append((pid, uid, tid, fare,
                             comp + timedelta(seconds=random.randint(1, 120)),
                             method))
            pid += 1
    con.executemany("INSERT INTO trips VALUES (?,?,?,?,?,?,?,?)", trips)
    con.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?)", payments)

    # ---- content: 60 titles ----
    content = []
    for cid in range(1, 61):
        content.append((cid, f"Title {cid}", random.choice(GENRES),
                        d(random.randint(-400, 150)),
                        random.randint(20, 160)))
    con.executemany("INSERT INTO content VALUES (?,?,?,?,?)", content)

    # ---- watch sessions: ~6000 ----
    watch = []
    for sid in range(1, 6001):
        uid = random.randint(1, 500)
        cid = random.randint(1, 60)
        ts = datetime(2025, 1, 1) + timedelta(
            days=random.randint(0, 200), minutes=random.randint(0, 1440))
        watch.append((sid, uid, cid, ts, random.randint(1, 160)))
    con.executemany("INSERT INTO sessions_watch VALUES (?,?,?,?,?)", watch)

    # ---- accounts: 200 SaaS accounts signing up across ~500 days ----
    accounts = []
    for aid in range(1, 201):
        created = d(random.randint(0, 500))
        accounts.append((aid, f"Account {aid}", random.choice(INDUSTRIES), created))
    con.executemany("INSERT INTO accounts VALUES (?,?,?,?)", accounts)

    # ---- subscriptions: each account has 1-3 plan stints (upgrades/downgrades) ----
    # exactly one stint per account has end_date = NULL (the current plan).
    subscriptions = []
    account_plan_windows = {}  # account_id -> list of (start_date, end_date_or_None)
    sub_id = 1
    for aid, _, _, created in accounts:
        n_stints = random.choices([1, 2, 3], weights=[5, 3, 2])[0]
        cursor = created
        plan_idx = random.randint(0, len(SUB_PLANS) - 1)
        windows = []
        for i in range(n_stints):
            plan = SUB_PLANS[min(plan_idx, len(SUB_PLANS) - 1)]
            stint_days = random.randint(30, 180)
            is_last = (i == n_stints - 1)
            end = None if is_last else cursor + timedelta(days=stint_days)
            mrr = SUB_MRR[plan] * random.uniform(0.95, 1.05)
            subscriptions.append((sub_id, aid, plan, cursor,
                                  end, round(mrr, 2)))
            windows.append((cursor, end))
            sub_id += 1
            if end is not None:
                cursor = end + timedelta(days=1)
            plan_idx += 1  # tends to upgrade over successive stints
        account_plan_windows[aid] = windows
    con.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?)", subscriptions)

    # ---- invoices: ~monthly invoices per account since signup, tied to whichever
    # plan/mrr was active at issue time; some outstanding or refunded ----
    invoices = []
    inv_id = 1
    today = d(500)
    for aid, _, _, created in accounts:
        cursor = created + timedelta(days=30)
        while cursor <= today:
            # find the mrr active on this date from this account's subscriptions
            active_mrr = None
            for sub in subscriptions:
                if sub[1] == aid and sub[3] <= cursor and (sub[4] is None or sub[4] >= cursor):
                    active_mrr = sub[5]
                    break
            if active_mrr is None:
                cursor += timedelta(days=30)
                continue
            roll = random.random()
            if roll < 0.85:
                status = "paid"
                paid = cursor + timedelta(days=random.randint(0, 5))
            elif roll < 0.95:
                status = "outstanding"
                paid = None
            else:
                status = "refunded"
                paid = cursor + timedelta(days=random.randint(0, 5))
            invoices.append((inv_id, aid, cursor, active_mrr, paid, status))
            inv_id += 1
            cursor += timedelta(days=30)
    con.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?)", invoices)

    con.close()
    print(f"Built {DB_PATH}")
    print("Tables: users(500), trips(4000), payments, content(60), sessions_watch(6000),")
    print(f"        accounts(200), subscriptions({len(subscriptions)}), invoices({len(invoices)})")


if __name__ == "__main__":
    build()
