-- ============================================================
-- Crypto Bot Database Schema
-- ============================================================
-- Use these SQL scripts to set up your database tables
-- Works with PostgreSQL, MySQL (with minor syntax adjustments)

-- ============================================================
-- ADMIN SETUP (Run as postgres/root)
-- ============================================================

-- Create database
-- For PostgreSQL:
CREATE DATABASE crypto_database;

-- For MySQL:
-- CREATE DATABASE crypto_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create bot user with limited permissions
-- PostgreSQL:
CREATE USER botuser WITH PASSWORD 'YourSecurePassword123';
GRANT CONNECT ON DATABASE crypto_database TO botuser;

-- MySQL:
-- CREATE USER 'botuser'@'%' IDENTIFIED BY 'YourSecurePassword123';
-- GRANT ALL ON crypto_database.* TO 'botuser'@'%';
-- FLUSH PRIVILEGES;

-- ============================================================
-- SCHEMA (Run as botuser or in the database)
-- ============================================================

-- Connect to database
-- psql -U postgres crypto_database
-- Or: mysql -u root -p crypto_database

-- ============================================================
-- TABLE: crypto_prices (Real-time price data)
-- ============================================================

CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    price DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 2),
    change_24h DECIMAL(8, 2),
    market_cap DECIMAL(20, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),  -- 'coingecko', 'binance', 'coindesk', etc.
    
    -- Indexes for fast queries
    INDEX idx_symbol (symbol),
    INDEX idx_timestamp (timestamp),
    CONSTRAINT unique_price_per_source UNIQUE(symbol, source, timestamp)
);

-- ============================================================
-- TABLE: user_alerts (User's price alerts)
-- ============================================================

CREATE TABLE user_alerts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,  -- Telegram user ID
    chat_id BIGINT NOT NULL,  -- Telegram chat ID
    asset VARCHAR(20) NOT NULL,
    price_threshold DECIMAL(20, 8) NOT NULL,
    condition VARCHAR(20) NOT NULL,  -- 'above', 'below', 'equals'
    alert_type VARCHAR(20) DEFAULT 'price',  -- 'price', 'percentage_change', 'volume'
    is_active BOOLEAN DEFAULT TRUE,
    notify_count INT DEFAULT 0,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_asset (asset),
    INDEX idx_active (is_active)
);

-- ============================================================
-- TABLE: user_portfolios (User holdings)
-- ============================================================

CREATE TABLE user_portfolios (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    total_value DECIMAL(20, 2),
    total_invested DECIMAL(20, 2),
    profit_loss DECIMAL(20, 2),
    profit_loss_percent DECIMAL(8, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id)
);

-- ============================================================
-- TABLE: portfolio_holdings (Individual asset holdings)
-- ============================================================

CREATE TABLE portfolio_holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL,
    asset VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    average_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    total_cost DECIMAL(20, 2),
    current_value DECIMAL(20, 2),
    profit_loss DECIMAL(20, 2),
    profit_loss_percent DECIMAL(8, 2),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (portfolio_id) REFERENCES user_portfolios(id) ON DELETE CASCADE,
    INDEX idx_portfolio_id (portfolio_id),
    INDEX idx_asset (asset)
);

-- ============================================================
-- TABLE: user_transactions (Trade history)
-- ============================================================

CREATE TABLE user_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    asset VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,  -- 'buy', 'sell', 'stake', 'unstake'
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    total_amount DECIMAL(20, 2) NOT NULL,
    fee DECIMAL(20, 8),
    exchange VARCHAR(50),  -- 'binance', 'kraken', etc.
    notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_asset (asset),
    INDEX idx_timestamp (timestamp),
    INDEX idx_type (transaction_type)
);

-- ============================================================
-- TABLE: market_data (Historical market snapshots)
-- ============================================================

CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    btc_dominance DECIMAL(8, 2),
    total_market_cap DECIMAL(20, 2),
    total_volume_24h DECIMAL(20, 2),
    fear_greed_index INT,  -- 0-100
    eth_gas_price DECIMAL(20, 8),
    notes TEXT,
    
    INDEX idx_timestamp (timestamp)
);

-- ============================================================
-- TABLE: trading_signals (AI-generated signals)
-- ============================================================

CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    asset VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,  -- 'buy', 'sell', 'hold'
    confidence_score DECIMAL(5, 2),  -- 0-100
    reasoning TEXT,
    target_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_asset (asset),
    INDEX idx_active (is_active)
);

-- ============================================================
-- TABLE: user_settings (User preferences)
-- ============================================================

CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    username VARCHAR(100),
    notification_level VARCHAR(20) DEFAULT 'all',  -- 'all', 'important', 'none'
    preferred_currency VARCHAR(10) DEFAULT 'USD',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    theme VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_chat_id (chat_id)
);

-- ============================================================
-- TABLE: conversation_logs (For debugging/analysis)
-- ============================================================

CREATE TABLE conversation_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    chat_id BIGINT,
    user_message TEXT,
    ai_response TEXT,
    model_used VARCHAR(100),
    tokens_used INT,
    response_time_ms INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
);

-- ============================================================
-- PERMISSIONS (For botuser)
-- ============================================================

-- PostgreSQL:
GRANT USAGE ON SCHEMA public TO botuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO botuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO botuser;

-- MySQL: (if using separate user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crypto_database.* TO 'botuser'@'%';

-- ============================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================

INSERT INTO crypto_prices (symbol, name, price, volume_24h, change_24h, source)
VALUES 
    ('BTC', 'Bitcoin', 65000.00000000, 25000000000.00, 5.23, 'coingecko'),
    ('ETH', 'Ethereum', 3500.00000000, 15000000000.00, 3.45, 'coingecko'),
    ('SOL', 'Solana', 150.00000000, 2000000000.00, 8.12, 'coingecko');

INSERT INTO user_settings (user_id, chat_id, username)
VALUES
    (123456789, -999888777, 'cryptotrader');

-- ============================================================
-- USEFUL QUERIES (for your bot to use)
-- ============================================================

-- Get user's portfolio summary
-- SELECT u.user_id, SUM(ph.current_value) as total_value, 
--        SUM(ph.profit_loss) as total_profit
-- FROM portfolio_holdings ph
-- JOIN user_portfolios u ON ph.portfolio_id = u.id
-- WHERE u.user_id = ?
-- GROUP BY u.user_id;

-- Get latest prices for multiple assets
-- SELECT * FROM crypto_prices 
-- WHERE symbol IN ('BTC', 'ETH', 'SOL')
-- ORDER BY timestamp DESC
-- LIMIT 3;

-- Check active alerts
-- SELECT * FROM user_alerts 
-- WHERE user_id = ? AND is_active = TRUE
-- ORDER BY created_at DESC;
