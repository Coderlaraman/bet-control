-- Sistema de Control de Apuestas RushBet
-- Base de datos MySQL

-- Tabla de usuarios
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de configuración de bankroll
CREATE TABLE bankroll_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    initial_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    current_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    max_bet_percentage DECIMAL(5,2) DEFAULT 5.00, -- Máximo 5% del bankroll por apuesta
    min_bet_amount DECIMAL(10,2) DEFAULT 1.00,
    max_bet_amount DECIMAL(10,2) DEFAULT 1000.00,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de deportes
CREATE TABLE sports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabla de países
CREATE TABLE countries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(3) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabla de ligas/competiciones
CREATE TABLE leagues (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country_id INT,
    sport_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);

-- Tabla de tipos de apuesta
CREATE TABLE bet_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabla de mercados de apuesta
CREATE TABLE markets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    sport_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);

-- Tabla principal de apuestas
CREATE TABLE bets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    bet_type_id INT NOT NULL,
    sport_id INT NOT NULL,
    country_id INT,
    league_id INT,
    market_id INT,
    
    -- Información del evento
    event_name VARCHAR(200) NOT NULL,
    event_date DATETIME NOT NULL,
    event_time TIME,
    home_team VARCHAR(100),
    away_team VARCHAR(100),
    
    -- Detalles de la apuesta
    bet_description TEXT NOT NULL, -- Pick o descripción
    odds DECIMAL(8,2) NOT NULL, -- Cuota
    stake DECIMAL(10,2) NOT NULL, -- Monto apostado
    potential_win DECIMAL(12,2) NOT NULL, -- Ganancia potencial
    
    -- Estado y resultados
    status ENUM('pending', 'won', 'lost', 'void', 'half_won', 'half_lost') DEFAULT 'pending',
    result_amount DECIMAL(12,2), -- Monto final ganado/perdido
    settled_at TIMESTAMP NULL,
    
    -- Metadata
    bet_slip_id VARCHAR(50), -- ID de RushBet si está disponible
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bet_type_id) REFERENCES bet_types(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Tabla para apuestas combinadas (parlays)
CREATE TABLE parlay_bets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    bet_type_id INT NOT NULL,
    total_odds DECIMAL(8,2) NOT NULL,
    total_stake DECIMAL(10,2) NOT NULL,
    potential_win DECIMAL(12,2) NOT NULL,
    status ENUM('pending', 'won', 'lost', 'void') DEFAULT 'pending',
    result_amount DECIMAL(12,2),
    settled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bet_type_id) REFERENCES bet_types(id)
);

-- Tabla de selecciones para apuestas combinadas
CREATE TABLE parlay_selections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    parlay_id INT NOT NULL,
    sport_id INT NOT NULL,
    league_id INT,
    event_name VARCHAR(200) NOT NULL,
    event_date DATETIME NOT NULL,
    market_id INT,
    selection VARCHAR(200) NOT NULL,
    odds DECIMAL(8,2) NOT NULL,
    status ENUM('pending', 'won', 'lost', 'void') DEFAULT 'pending',
    FOREIGN KEY (parlay_id) REFERENCES parlay_bets(id) ON DELETE CASCADE,
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Tabla de transacciones de bankroll
CREATE TABLE bankroll_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    transaction_type ENUM('bet_placed', 'bet_won', 'bet_lost', 'bet_void', 'deposit', 'withdrawal', 'adjustment') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    balance_before DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,
    related_bet_id INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_bet_id) REFERENCES bets(id)
);

-- Tabla de estadísticas por deporte
CREATE TABLE sport_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    sport_id INT NOT NULL,
    total_bets INT DEFAULT 0,
    won_bets INT DEFAULT 0,
    lost_bets INT DEFAULT 0,
    void_bets INT DEFAULT 0,
    total_staked DECIMAL(15,2) DEFAULT 0.00,
    total_profit DECIMAL(15,2) DEFAULT 0.00,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    roi DECIMAL(5,2) DEFAULT 0.00, -- Return on Investment
    average_odds DECIMAL(6,2) DEFAULT 0.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    UNIQUE KEY unique_user_sport (user_id, sport_id)
);

-- Tabla de estadísticas por liga
CREATE TABLE league_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    league_id INT NOT NULL,
    total_bets INT DEFAULT 0,
    won_bets INT DEFAULT 0,
    lost_bets INT DEFAULT 0,
    void_bets INT DEFAULT 0,
    total_staked DECIMAL(15,2) DEFAULT 0.00,
    total_profit DECIMAL(15,2) DEFAULT 0.00,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    roi DECIMAL(5,2) DEFAULT 0.00,
    average_odds DECIMAL(6,2) DEFAULT 0.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    UNIQUE KEY unique_user_league (user_id, league_id)
);

-- Tabla de configuración de alertas y notificaciones
CREATE TABLE alert_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    threshold_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    notification_method VARCHAR(20) DEFAULT 'email',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Índices para optimización
CREATE INDEX idx_bets_user_status ON bets(user_id, status);
CREATE INDEX idx_bets_user_date ON bets(user_id, created_at);
CREATE INDEX idx_bets_sport ON bets(sport_id);
CREATE INDEX idx_bets_league ON bets(league_id);
CREATE INDEX idx_bankroll_transactions_user ON bankroll_transactions(user_id, created_at);
CREATE INDEX idx_parlay_selections_parlay ON parlay_selections(parlay_id);

-- Datos iniciales
INSERT INTO sports (name, code) VALUES 
('Fútbol', 'SOCCER'),
('Baloncesto', 'BASKETBALL'),
('Tenis', 'TENIS'),
('Béisbol', 'BASEBALL'),
('Fútbol Americano', 'AMERICAN_FOOTBALL'),
('Hockey', 'HOCKEY'),
('Boxeo', 'BOXING'),
('MMA', 'MMA'),
('eSports', 'ESPORTS'),
('Otros', 'OTHER');

INSERT INTO bet_types (name, description) VALUES 
('Sencilla', 'Apuesta individual'),
('Combinada', 'Múltiples selecciones en una apuesta'),
('Sistema', 'Combinación de apuestas múltiples'),
('Live', 'Apuesta en vivo'),
('Futuro', 'Apuesta a evento futuro');

INSERT INTO countries (name, code) VALUES 
('Colombia', 'COL'),
('Argentina', 'ARG'),
('Brasil', 'BRA'),
('Chile', 'CHL'),
('México', 'MEX'),
('España', 'ESP'),
('Inglaterra', 'ENG'),
('Italia', 'ITA'),
('Alemania', 'GER'),
('Francia', 'FRA'),
('Estados Unidos', 'USA'),
('Otros', 'OTH');