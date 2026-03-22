-- FinOps Lite SQL analysis queries
-- The sample table is a compact daily cost mart: one row per date, service,
-- account, and region. The queries stay intentionally practical and are meant
-- to read like analyst work rather than SQL exercises.

-- 1. Total cost by service
-- Analyst intent: identify the largest cost centers before deeper investigation.
SELECT
    service,
    ROUND(SUM(blended_cost), 2) AS total_cost,
    ROUND(
        SUM(blended_cost) * 100.0
        / NULLIF((SELECT SUM(blended_cost) FROM cloud_cost_daily), 0),
        1
    ) AS pct_of_total
FROM cloud_cost_daily
GROUP BY service
ORDER BY total_cost DESC;

-- 2. Daily spend trend
-- Analyst intent: show the shape of spend over time and spot abrupt changes.
SELECT
    usage_date,
    ROUND(SUM(blended_cost), 2) AS daily_spend
FROM cloud_cost_daily
GROUP BY usage_date
ORDER BY usage_date;

-- 3. Monthly spend trend
-- Analyst intent: roll service-level activity up to a finance-friendly reporting cadence.
SELECT
    SUBSTR(CAST(usage_date AS CHAR(10)), 1, 7) AS usage_month,
    ROUND(SUM(blended_cost), 2) AS monthly_spend
FROM cloud_cost_daily
GROUP BY SUBSTR(CAST(usage_date AS CHAR(10)), 1, 7)
ORDER BY usage_month;

-- 4. Top cost-driving services in the current review window
-- Analyst intent: focus attention on the services most responsible for the bill.
SELECT
    service,
    ROUND(SUM(blended_cost), 2) AS review_window_cost
FROM cloud_cost_daily
WHERE usage_date BETWEEN '2026-02-01' AND '2026-02-05'
GROUP BY service
ORDER BY review_window_cost DESC
LIMIT 5;

-- 5. Cost by region
-- Analyst intent: separate spend concentration by geography and deployment pattern.
SELECT
    region,
    ROUND(SUM(blended_cost), 2) AS total_cost
FROM cloud_cost_daily
GROUP BY region
ORDER BY total_cost DESC;

-- 6. Cost by account and environment
-- Analyst intent: connect spend to ownership boundaries that matter for review.
SELECT
    account_name,
    environment,
    ROUND(SUM(blended_cost), 2) AS total_cost
FROM cloud_cost_daily
GROUP BY account_name, environment
ORDER BY total_cost DESC, account_name;

-- 7. Environment and cost center breakdown
-- Analyst intent: show how infrastructure cost maps to budget context.
SELECT
    environment,
    cost_center,
    ROUND(SUM(blended_cost), 2) AS total_cost
FROM cloud_cost_daily
GROUP BY environment, cost_center
ORDER BY total_cost DESC, environment;

-- 8. Simple anomaly-style query for unusually high daily spend
-- Analyst intent: flag days where total spend moves materially above recent baseline.
WITH daily_totals AS (
    SELECT
        usage_date,
        ROUND(SUM(blended_cost), 2) AS daily_spend
    FROM cloud_cost_daily
    GROUP BY usage_date
),
baseline AS (
    SELECT AVG(daily_spend) AS average_daily_spend
    FROM daily_totals
)
SELECT
    dt.usage_date,
    ROUND(dt.daily_spend, 2) AS daily_spend,
    ROUND(b.average_daily_spend, 2) AS baseline_daily_spend,
    ROUND(dt.daily_spend - b.average_daily_spend, 2) AS dollars_above_baseline
FROM daily_totals dt
CROSS JOIN baseline b
WHERE dt.daily_spend > b.average_daily_spend * 1.20
ORDER BY dt.daily_spend DESC;

-- 9. Current vs prior period comparison by service
-- Analyst intent: compare a review window to the immediately preceding window of equal length.
WITH current_period AS (
    SELECT
        service,
        SUM(blended_cost) AS current_cost
    FROM cloud_cost_daily
    WHERE usage_date BETWEEN '2026-02-01' AND '2026-02-05'
    GROUP BY service
),
prior_period AS (
    SELECT
        service,
        SUM(blended_cost) AS prior_cost
    FROM cloud_cost_daily
    WHERE usage_date BETWEEN '2026-01-27' AND '2026-01-31'
    GROUP BY service
),
combined AS (
    SELECT
        c.service,
        c.current_cost,
        p.prior_cost
    FROM current_period c
    LEFT JOIN prior_period p
        ON c.service = p.service

    UNION ALL

    SELECT
        p.service,
        c.current_cost,
        p.prior_cost
    FROM prior_period p
    LEFT JOIN current_period c
        ON p.service = c.service
    WHERE c.service IS NULL
)
SELECT
    service,
    ROUND(COALESCE(current_cost, 0), 2) AS current_cost,
    ROUND(COALESCE(prior_cost, 0), 2) AS prior_cost,
    ROUND(COALESCE(current_cost, 0) - COALESCE(prior_cost, 0), 2) AS cost_delta,
    ROUND(
        (
            (COALESCE(current_cost, 0) - COALESCE(prior_cost, 0))
            * 100.0
            / NULLIF(COALESCE(prior_cost, 0), 0)
        ),
        1
    ) AS pct_delta
FROM combined
ORDER BY cost_delta DESC, service;
