CREATE TABLE cloud_cost_daily (
    usage_date DATE NOT NULL,
    account_id VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    environment VARCHAR(30) NOT NULL,
    service VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    usage_quantity DECIMAL(18, 2) NOT NULL,
    usage_unit VARCHAR(50) NOT NULL,
    blended_cost DECIMAL(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,
    owner_team VARCHAR(100) NOT NULL,
    cost_center VARCHAR(100) NOT NULL,
    PRIMARY KEY (usage_date, account_id, service, region)
);
