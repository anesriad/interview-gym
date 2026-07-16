-- Practice schema: a ride-hailing + streaming flavored dataset.
-- Realistic enough to support joins, window functions, cohort/retention,
-- funnel, and aggregation questions similar to real DS/DA interviews.

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS sessions_watch;
DROP TABLE IF EXISTS content;

CREATE TABLE users (
    user_id      INTEGER PRIMARY KEY,
    signup_date  DATE,
    city         VARCHAR,
    plan         VARCHAR      -- 'free', 'standard', 'premium'
);

CREATE TABLE trips (
    trip_id       INTEGER PRIMARY KEY,
    user_id       INTEGER,
    request_ts    TIMESTAMP,
    complete_ts   TIMESTAMP,   -- NULL if cancelled
    city          VARCHAR,
    distance_km   DOUBLE,
    fare_usd      DOUBLE,
    status        VARCHAR      -- 'completed', 'cancelled'
);

CREATE TABLE payments (
    payment_id   INTEGER PRIMARY KEY,
    user_id      INTEGER,
    trip_id      INTEGER,
    amount_usd   DOUBLE,
    paid_ts      TIMESTAMP,
    method       VARCHAR       -- 'card', 'wallet', 'cash'
);

CREATE TABLE content (
    content_id   INTEGER PRIMARY KEY,
    title        VARCHAR,
    genre        VARCHAR,
    release_date DATE,
    duration_min INTEGER
);

CREATE TABLE sessions_watch (
    session_id     INTEGER PRIMARY KEY,
    user_id        INTEGER,
    content_id     INTEGER,
    watch_ts       TIMESTAMP,
    minutes_watched INTEGER
);

-- SaaS subscriptions + billing flavored dataset (separate domain from the
-- ride-hailing/streaming tables above). Supports self-joins on plan history,
-- date bucketing on invoices, and window functions over account revenue.

DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS invoices;

CREATE TABLE accounts (
    account_id     INTEGER PRIMARY KEY,
    account_name   VARCHAR,
    industry       VARCHAR,     -- 'retail', 'fintech', 'healthcare', 'media', 'logistics'
    created_date   DATE
);

CREATE TABLE subscriptions (
    subscription_id  INTEGER PRIMARY KEY,
    account_id       INTEGER,
    plan             VARCHAR,   -- 'starter', 'growth', 'enterprise'
    start_date       DATE,
    end_date         DATE,      -- NULL if this is the account's current/active plan
    mrr_usd          DOUBLE     -- monthly recurring revenue for this plan stint
);

CREATE TABLE invoices (
    invoice_id      INTEGER PRIMARY KEY,
    account_id      INTEGER,
    issued_date     DATE,
    amount_usd      DOUBLE,
    paid_date       DATE,       -- NULL if unpaid/outstanding
    status           VARCHAR    -- 'paid', 'outstanding', 'refunded'
);
