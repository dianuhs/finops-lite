# SQL Analysis

This SQL layer exists to show the analysis side of the same FinOps work the rest of the repository covers in code and CLI flows.

It uses a compact, realistic cloud cost dataset to answer the kinds of questions a financial analyst, business analyst, FinOps analyst, or cloud cost analyst would be expected to ask:

- What services are driving the bill?
- How is spend moving day over day and month over month?
- Which regions and environments concentrate cost?
- Which days look abnormal against baseline?
- How does the current review window compare with the prior one?

## Dataset

[`cloud_cost_sample.csv`](./cloud_cost_sample.csv) is a daily service-level cost rollup modeled after a lightweight cloud cost reporting table. Each row includes:

- date
- service
- account
- region
- usage quantity and unit
- blended cost
- environment
- team / cost center context

The sample stays intentionally small so the logic is easy to review, but the values are shaped like believable AWS spend patterns: EC2 is the main cost driver, storage is steady, development spend stays modest, and one review day shows a clear spike.

The schema and query style stay close to portable SQL so the same analysis can be lifted into SQLite, DuckDB, or PostgreSQL-style workflows with minimal adjustment.

## Files

- [`schema.sql`](./schema.sql): portable table definition for the sample dataset
- [`queries.sql`](./queries.sql): practical analyst-style SQL for cost visibility, trend review, anomaly detection, and period comparison
- [`cloud_cost_sample.csv`](./cloud_cost_sample.csv): compact sample data for the queries

## How to read it as a reviewer

The point of this folder is not to present a standalone SQL tutorial. It is to make a specific skill set visible:

- translating cloud billing data into a clean analytical table
- asking practical cost, ownership, and variance questions in SQL
- explaining cost behavior in a finance-friendly way
- connecting engineering infrastructure usage to budgeting and operational review

## Why it fits this repository

FinOps Lite already shows cost reasoning in CLI form. This SQL layer makes the underlying analytical skill more explicit: structured data modeling, cost slicing, period comparisons, and finance-oriented interpretation.

The goal is not to present a disconnected SQL exercise. The goal is to show the same cloud cost domain from another angle:

- FinOps Lite CLI: operational cost inspection and machine-readable outputs
- SQL analysis layer: analyst-style interrogation of normalized cost data

That combination is the practical signal. It shows comfort with cost data as both an engineering workflow and an analysis workflow.
