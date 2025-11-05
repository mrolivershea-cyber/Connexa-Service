#!/usr/bin/env python3
"""
Create large test dataset with 2336 PPTP nodes for comprehensive testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Node
from datetime import datetime
import random

def generate_ip():
    """Generate a realistic IP address"""
    # Use various IP ranges for realistic testing
    ranges = [
        (1, 126),    # Class A (skip 127.x.x.x)
        (128, 191),  # Class B  
        (192, 223),  # Class C
    ]
    
    range_choice = random.choice(ranges)
    first_octet = random.randint(range_choice[0], range_choice[1])
    
    # Avoid private IP ranges for more realistic testing
    if first_octet == 10:
        first_octet = random.randint(11, 126)
    elif first_octet == 172:
        second = random.randint(0, 15) if random.random() < 0.5 else random.randint(32, 255)
    elif first_octet == 192 and random.randint(0, 255) == 168:
        first_octet = random.randint(193, 223)
    
    return f"{first_octet}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def create_large_dataset():
    """Create 2336 test PPTP nodes"""
    db = SessionLocal()
    
    try:
        # Clear existing data first
        existing_count = db.query(Node).count()
        if existing_count > 0:
            print(f"Очистка существующих {existing_count} записей...")
            db.query(Node).delete()
            db.commit()
        
        # Provider lists for realistic data
        providers = [
            "DigitalOcean", "Linode", "Vultr", "AWS", "Hetzner", "OVH", 
            "Contabo", "Time4VPS", "Hostinger", "IONOS", "Scaleway",
            "UpCloud", "Kamatera", "Atlantic.net", "InMotion", "A2Hosting"
        ]
        
        countries = [
            "US", "UK", "DE", "FR", "NL", "SG", "JP", "CA", "AU", "SE",
            "NO", "DK", "FI", "CH", "AT", "BE", "IT", "ES", "PT", "PL"
        ]
        
        cities_by_country = {
            "US": ["New York", "Los Angeles", "Chicago", "Miami", "Seattle", "Dallas"],
            "UK": ["London", "Manchester", "Birmingham", "Leeds", "Liverpool"],  
            "DE": ["Frankfurt", "Berlin", "Munich", "Hamburg", "Stuttgart"],
            "FR": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
            "NL": ["Amsterdam", "Rotterdam", "Utrecht", "Eindhoven"],
            "SG": ["Singapore"],
            "JP": ["Tokyo", "Osaka", "Kyoto", "Nagoya"],
            "CA": ["Toronto", "Vancouver", "Montreal", "Calgary"],
            "AU": ["Sydney", "Melbourne", "Brisbane", "Perth"],
        }
        
        print(f"Создание {2336} тестовых PPTP узлов...")
        
        batch_size = 100
        created_count = 0
        
        for i in range(0, 2336, batch_size):
            batch_nodes = []
            batch_end = min(i + batch_size, 2336)
            
            for j in range(i, batch_end):
                country = random.choice(countries)
                city = random.choice(cities_by_country.get(country, ["Unknown"]))
                
                node = Node(
                    ip=generate_ip(),
                    port=1723,  # Standard PPTP port
                    login=f"user{j+1:04d}",
                    password=f"pass{random.randint(1000, 9999)}",
                    provider=random.choice(providers),
                    country=country,
                    city=city,
                    state=f"State{random.randint(1, 50)}" if country == "US" else "",
                    zipcode=f"{random.randint(10000, 99999)}" if random.random() > 0.3 else "",
                    protocol="pptp",
                    status="not_tested",
                    comment=f"Imported PPTP server #{j+1}",
                    last_update=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                batch_nodes.append(node)
            
            # Add batch to database
            db.add_all(batch_nodes)
            db.commit()
            
            created_count += len(batch_nodes)
            if created_count % 500 == 0:
                print(f"Создано {created_count} из 2336 узлов...")
        
        print(f"✅ Успешно создано {created_count} PPTP узлов")
        
        # Verify creation
        from sqlalchemy import func
        total_count = db.query(Node).count()
        status_counts = db.query(Node.status, func.count(Node.id)).group_by(Node.status).all()
        
        print(f"✅ Всего узлов в базе данных: {total_count}")
        print("✅ Распределение по статусам:")
        for status, count in status_counts:
            print(f"   {status}: {count}")
            
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых узлов: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_large_dataset()