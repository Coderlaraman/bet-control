#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, init_db
from app.models.user import User
from app.models.bankroll import BankrollConfig, BankrollTransaction, TransactionType
from app.models.bet import Bet, BetType, Market, ParlayBet, ParlaySelection
from app.models.sport import Sport, Country, League
from app.core.security import get_password_hash


def create_test_user(db, username, email, password, full_name, role):
    """Crear usuario de prueba con rol específico"""
    from app.models.user import UserRole
    
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_bankroll_config(db, user_id, initial_amount):
    """Crear configuración de bankroll"""
    config = BankrollConfig(
        user_id=user_id,
        initial_amount=Decimal(str(initial_amount)),
        current_amount=Decimal(str(initial_amount)),
        max_bet_percentage=Decimal("5.00"),
        min_bet_amount=Decimal("10.00"),
        max_bet_amount=Decimal("500.00"),
        currency="USD"
    )
    db.add(config)
    db.commit()
    return config


def create_sports_data(db):
    """Crear datos de deportes"""
    sports = [
        Sport(name="Soccer", code="SOC"),
        Sport(name="Basketball", code="BAS"),
        Sport(name="Tennis", code="TEN"),
        Sport(name="Baseball", code="BASE"),
        Sport(name="American Football", code="AMF"),
    ]
    
    for sport in sports:
        db.add(sport)
    db.commit()
    return sports


def create_markets_data(db):
    """Crear datos de mercados"""
    markets = [
        Market(name="Match Winner", code="MW", description="Match winner market"),
        Market(name="Over/Under", code="OU", description="Over/Under goals/points"),
        Market(name="Handicap", code="AH", description="Asian Handicap"),
        Market(name="Both Teams to Score", code="BTTS", description="Both teams to score"),
        Market(name="Correct Score", code="CS", description="Correct score"),
        Market(name="Double Chance", code="DC", description="Double chance"),
    ]
    
    for market in markets:
        db.add(market)
    db.commit()
    return markets


def create_bet_types_data(db):
    """Crear tipos de apuesta"""
    bet_types = [
        BetType(name="Single", description="Single bet"),
        BetType(name="Parlay", description="Parlay/Accumulator bet"),
        BetType(name="System", description="System bet"),
    ]
    
    for bet_type in bet_types:
        db.add(bet_type)
    db.commit()
    return bet_types


def create_countries_and_leagues(db):
    """Crear países y ligas"""
    countries = [
        Country(name="Spain", code="ES"),
        Country(name="England", code="GB"),
        Country(name="Italy", code="IT"),
        Country(name="Germany", code="DE"),
        Country(name="France", code="FR"),
        Country(name="USA", code="US"),
    ]
    
    for country in countries:
        db.add(country)
    db.commit()
    
    leagues = [
        League(name="La Liga", country_id=countries[0].id, sport_id=1),
        League(name="Premier League", country_id=countries[1].id, sport_id=1),
        League(name="Serie A", country_id=countries[2].id, sport_id=1),
        League(name="Bundesliga", country_id=countries[3].id, sport_id=1),
        League(name="Ligue 1", country_id=countries[4].id, sport_id=1),
        League(name="NBA", country_id=countries[5].id, sport_id=2),
    ]
    
    for league in leagues:
        db.add(league)
    db.commit()
    
    return countries, leagues


def create_sample_bets(db, user_id, sports, markets, bet_types):
    """Crear apuestas de muestra"""
    sample_bets = [
        {
            "event_name": "Real Madrid vs Barcelona",
            "event_date": datetime.now() + timedelta(days=1),
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "bet_description": "Real Madrid to win",
            "odds": Decimal("2.10"),
            "stake": Decimal("50.00"),
            "status": "pending"
        },
        {
            "event_name": "Manchester United vs Liverpool",
            "event_date": datetime.now() - timedelta(days=2),
            "home_team": "Manchester United",
            "away_team": "Liverpool",
            "bet_description": "Over 2.5 goals",
            "odds": Decimal("1.80"),
            "stake": Decimal("30.00"),
            "status": "won",
            "result_amount": Decimal("54.00")
        },
        {
            "event_name": "Juventus vs AC Milan",
            "event_date": datetime.now() - timedelta(days=1),
            "home_team": "Juventus",
            "away_team": "AC Milan",
            "bet_description": "Both teams to score",
            "odds": Decimal("1.90"),
            "stake": Decimal("25.00"),
            "status": "lost",
            "result_amount": Decimal("0.00")
        },
        {
            "event_name": "Bayern Munich vs Dortmund",
            "event_date": datetime.now() - timedelta(days=3),
            "home_team": "Bayern Munich",
            "away_team": "Dortmund",
            "bet_description": "Bayern -1 handicap",
            "odds": Decimal("2.30"),
            "stake": Decimal("40.00"),
            "status": "won",
            "result_amount": Decimal("92.00")
        },
        {
            "event_name": "Lakers vs Warriors",
            "event_date": datetime.now() + timedelta(days=2),
            "home_team": "Lakers",
            "away_team": "Warriors",
            "bet_description": "Warriors to win",
            "odds": Decimal("1.75"),
            "stake": Decimal("35.00"),
            "status": "pending"
        },
    ]
    
    for bet_data in sample_bets:
        bet = Bet(
            user_id=user_id,
            bet_type_id=bet_types[0].id,  # Single
            sport_id=sports[0].id,  # Soccer
            market_id=markets[0].id,  # Match Winner
            event_name=bet_data["event_name"],
            event_date=bet_data["event_date"],
            home_team=bet_data["home_team"],
            away_team=bet_data["away_team"],
            bet_description=bet_data["bet_description"],
            odds=bet_data["odds"],
            stake=bet_data["stake"],
            potential_win=bet_data["stake"] * bet_data["odds"],
            status=bet_data["status"],
            result_amount=bet_data.get("result_amount"),
            bet_slip_id=f"SLIP{hash(bet_data['event_name']) % 10000}"
        )
        db.add(bet)
    
    db.commit()


def create_sample_transactions(db, user_id, config):
    """Crear transacciones de muestra"""
    transactions = [
        BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("1000.00"),
            balance_before=Decimal("0.00"),
            balance_after=Decimal("1000.00"),
            description="Initial deposit"
        ),
        BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_PLACED,
            amount=Decimal("-50.00"),
            balance_before=Decimal("1000.00"),
            balance_after=Decimal("950.00"),
            description="Bet placed: Real Madrid vs Barcelona",
            related_bet_id=1
        ),
        BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_WON,
            amount=Decimal("54.00"),
            balance_before=Decimal("950.00"),
            balance_after=Decimal("1004.00"),
            description="Bet won: Manchester United vs Liverpool",
            related_bet_id=2
        ),
        BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_PLACED,
            amount=Decimal("-25.00"),
            balance_before=Decimal("1004.00"),
            balance_after=Decimal("979.00"),
            description="Bet placed: Juventus vs AC Milan",
            related_bet_id=3
        ),
        BankrollTransaction(
            user_id=user_id,
            transaction_type=TransactionType.BET_WON,
            amount=Decimal("92.00"),
            balance_before=Decimal("979.00"),
            balance_after=Decimal("1071.00"),
            description="Bet won: Bayern Munich vs Dortmund",
            related_bet_id=4
        ),
    ]
    
    for transaction in transactions:
        db.add(transaction)
    
    # Actualizar el balance actual
    config.current_amount = Decimal("1071.00")
    db.commit()


def main():
    """Función principal"""
    from app.models.user import UserRole
    
    print("🚀 Inicializando base de datos de BetControl...")
    
    # Inicializar base de datos
    init_db()
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Crear usuario administrador
        print("\n👤 Creando usuario ADMINISTRADOR...")
        admin_user = create_test_user(
            db, 
            username="admin", 
            email="admin@betcontrol.com", 
            password="Admin123!",  # Contraseña robusta
            full_name="Administrator",
            role=UserRole.ADMIN
        )
        print(f"✅ Usuario admin creado: {admin_user.username} (Role: {admin_user.role})")
        
        # Crear usuario normal
        print("\n👤 Creando usuario NORMAL...")
        normal_user = create_test_user(
            db,
            username="usuario",
            email="usuario@betcontrol.com",
            password="Usuario123!",  # Contraseña robusta
            full_name="Usuario Normal",
            role=UserRole.USER
        )
        print(f"✅ Usuario normal creado: {normal_user.username} (Role: {normal_user.role})")
        
        # Crear configuración de bankroll para admin
        print("\n💰 Creando configuración de bankroll para admin...")
        admin_config = create_bankroll_config(db, admin_user.id, 1000.00)
        print(f"✅ Bankroll inicial admin: ${admin_config.initial_amount}")
        
        # Crear configuración de bankroll para usuario normal
        print("💰 Creando configuración de bankroll para usuario normal...")
        user_config = create_bankroll_config(db, normal_user.id, 500.00)
        print(f"✅ Bankroll inicial usuario: ${user_config.initial_amount}")
        
        # Crear datos de deportes
        print("\n⚽ Creando datos de deportes...")
        sports = create_sports_data(db)
        print(f"✅ {len(sports)} deportes creados")
        
        # Crear datos de mercados
        print("\n📊 Creando datos de mercados...")
        markets = create_markets_data(db)
        print(f"✅ {len(markets)} mercados creados")
        
        # Crear tipos de apuesta
        print("\n🎯 Creando tipos de apuesta...")
        bet_types = create_bet_types_data(db)
        print(f"✅ {len(bet_types)} tipos de apuesta creados")
        
        # Crear países y ligas
        print("\n🌍 Creando países y ligas...")
        countries, leagues = create_countries_and_leagues(db)
        print(f"✅ {len(countries)} países y {len(leagues)} ligas creadas")
        
        # Crear apuestas de muestra para admin
        print("\n🎲 Creando apuestas de muestra para admin...")
        create_sample_bets(db, admin_user.id, sports, markets, bet_types)
        print("✅ Apuestas de muestra creadas")
        
        # Crear transacciones de muestra para admin
        print("\n💳 Creando transacciones de muestra para admin...")
        create_sample_transactions(db, admin_user.id, admin_config)
        print("✅ Transacciones de muestra creadas")
        
        print("\n" + "="*60)
        print("🎉 Base de datos inicializada exitosamente!")
        print("="*60)
        print("\n📋 CREDENCIALES DE ACCESO:\n")
        print("👨‍💼 Usuario Administrador:")
        print(f"   Usuario: admin")
        print(f"   Contraseña: Admin123!")
        print(f"   Email: admin@betcontrol.com")
        print(f"   Rol: ADMIN\n")
        print("👤 Usuario Normal:")
        print(f"   Usuario: usuario")
        print(f"   Contraseña: Usuario123!")
        print(f"   Email: usuario@betcontrol.com")
        print(f"   Rol: USER\n")
        print("="*60)
        print("\n🌐 Acceso a la aplicación:")
        print(f"   Frontend: http://localhost:3000")
        print(f"   API Docs: http://localhost:8075/docs")
        print(f"   Backend: http://localhost:8075\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()