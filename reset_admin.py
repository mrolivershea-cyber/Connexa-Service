#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/backend')

from database import get_db, User, hash_password, create_tables
from sqlalchemy.orm import Session

def reset_admin_password():
    # Create tables first
    create_tables()
    print("✅ Tables created")
    
    db = next(get_db())
    
    # Find admin user
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        # Reset password to 'admin'
        admin_user.password = hash_password("admin")
        db.commit()
        print("✅ Admin password reset to 'admin'")
    else:
        # Create new admin user
        admin_user = User(
            username="admin",
            password=hash_password("admin")
        )
        db.add(admin_user)
        db.commit()
        print("✅ New admin user created with password 'admin'")
    
    db.close()

if __name__ == "__main__":
    reset_admin_password()