"""
Test-User Setup Script

Erstellt/aktualisiert alle Test-User für RBAC-Tests.
Alle Passwörter werden auf "123" gesetzt.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal
from backend.app.models import User, InterestGroup, UserGroupMembership
import bcrypt
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_or_create_user(db, email: str, full_name: str, is_qms_admin: bool = False, employee_id: str = None):
    """Holt existierenden User oder erstellt neuen"""
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        # Update existing user
        print(f"  ⚙️  Update existing user: {email}")
        user.full_name = full_name
        user.hashed_password = hash_password("123")  # Reset password to "123"
        user.is_qms_admin = is_qms_admin
        user.is_active = True
        if employee_id:
            user.employee_id = employee_id
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        print(f"  ✅ Create new user: {email}")
        user = User(
            email=email,
            full_name=full_name,
            employee_id=employee_id or email.split('@')[0].upper().replace('.', '-'),
            hashed_password=hash_password("123"),
            is_qms_admin=is_qms_admin,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
    
    db.flush()  # Get user.id
    return user


def get_interest_group(db, code: str):
    """Holt Interest Group anhand Code"""
    return db.query(InterestGroup).filter(InterestGroup.code == code).first()


def set_user_membership(db, user: User, group_code: str, approval_level: int, role_name: str = None):
    """Setzt oder aktualisiert UserGroupMembership"""
    group = get_interest_group(db, group_code)
    
    if not group:
        print(f"  ⚠️  WARNING: Interest Group '{group_code}' not found! Skipping membership.")
        return
    
    # Prüfe ob Membership bereits existiert
    membership = (
        db.query(UserGroupMembership)
        .filter(
            UserGroupMembership.user_id == user.id,
            UserGroupMembership.interest_group_id == group.id
        )
        .first()
    )
    
    if membership:
        # Update existing membership
        print(f"    ⚙️  Update membership: {group.name} (Level {approval_level})")
        membership.approval_level = approval_level
        membership.role_in_group = role_name or f"Level {approval_level}"
        membership.is_department_head = (approval_level >= 3)
        membership.is_active = True
        membership.updated_at = datetime.utcnow()
    else:
        # Create new membership
        print(f"    ✅ Create membership: {group.name} (Level {approval_level})")
        membership = UserGroupMembership(
            user_id=user.id,
            interest_group_id=group.id,
            approval_level=approval_level,
            role_in_group=role_name or f"Level {approval_level}",
            is_department_head=(approval_level >= 3),
            is_active=True,
            joined_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            assigned_by_id=1  # qms.admin
        )
        db.add(membership)


def setup_test_users():
    """Erstellt/aktualisiert alle Test-User"""
    
    db = SessionLocal()
    
    try:
        print("🔧 Setting up RBAC Test-Users...\n")
        print("📝 All passwords will be set to: '123'\n")
        
        # ========================================
        # Level 5: QMS Admin (bereits vorhanden)
        # ========================================
        print("1️⃣  Level 5: QMS Admin")
        admin_user = get_or_create_user(
            db, 
            "qms.admin@company.com",
            "QMS Administrator",
            is_qms_admin=True,
            employee_id="QMS-001"
        )
        print(f"    User ID: {admin_user.id}\n")
        
        # ========================================
        # Level 4: QM-Mitarbeiter
        # ========================================
        print("2️⃣  Level 4: QM-Mitarbeiter")
        qm_user = get_or_create_user(
            db,
            "qm.mitarbeiter@company.com",
            "QM Mitarbeiter",
            is_qms_admin=False,
            employee_id="QM-001"
        )
        set_user_membership(db, qm_user, "QM", 4, "QM-Manager")
        print(f"    User ID: {qm_user.id}\n")
        
        # ========================================
        # Level 3: Abteilungsleiter
        # ========================================
        print("3️⃣  Level 3: Abteilungsleiter")
        
        # Abteilungsleiter Service
        abt_service = get_or_create_user(
            db,
            "abteilungsleiter.service@company.com",
            "Abteilungsleiter Service",
            employee_id="SV-001"
        )
        set_user_membership(db, abt_service, "SV", 3, "Abteilungsleiter")
        print(f"    User ID: {abt_service.id}")
        
        # Abteilungsleiter Produktion
        abt_prod = get_or_create_user(
            db,
            "abteilungsleiter.produktion@company.com",
            "Abteilungsleiter Produktion",
            employee_id="PR-001"
        )
        set_user_membership(db, abt_prod, "PR", 3, "Abteilungsleiter")
        print(f"    User ID: {abt_prod.id}\n")
        
        # ========================================
        # Level 2: Teamleiter
        # ========================================
        print("4️⃣  Level 2: Teamleiter")
        
        # Teamleiter Service
        tl_service = get_or_create_user(
            db,
            "teamleiter.service@company.com",
            "Teamleiter Service",
            employee_id="SV-002"
        )
        set_user_membership(db, tl_service, "SV", 2, "Teamleiter")
        print(f"    User ID: {tl_service.id}")
        
        # Teamleiter IT
        tl_it = get_or_create_user(
            db,
            "teamleiter.it@company.com",
            "Teamleiter IT",
            employee_id="IT-001"
        )
        set_user_membership(db, tl_it, "IT", 2, "Teamleiter")
        print(f"    User ID: {tl_it.id}\n")
        
        # ========================================
        # Level 1: Mitarbeiter
        # ========================================
        print("5️⃣  Level 1: Mitarbeiter")
        
        # Mitarbeiter Service
        ma_service = get_or_create_user(
            db,
            "mitarbeiter.service@company.com",
            "Mitarbeiter Service",
            employee_id="SV-003"
        )
        set_user_membership(db, ma_service, "SV", 1, "Mitarbeiter")
        print(f"    User ID: {ma_service.id}")
        
        # Mitarbeiter IT
        ma_it = get_or_create_user(
            db,
            "mitarbeiter.it@company.com",
            "Mitarbeiter IT",
            employee_id="IT-002"
        )
        set_user_membership(db, ma_it, "IT", 1, "Mitarbeiter")
        print(f"    User ID: {ma_it.id}\n")
        
        # ========================================
        # Bestehender User: qm@company.com
        # ========================================
        print("6️⃣  Update existing user: qm@company.com")
        existing_qm = db.query(User).filter(User.email == "qm@company.com").first()
        if existing_qm:
            existing_qm.hashed_password = hash_password("123")
            existing_qm.updated_at = datetime.utcnow()
            print(f"    ✅ Password reset to '123'")
            print(f"    User ID: {existing_qm.id}")
            print(f"    Note: Existing memberships preserved\n")
        
        # Commit all changes
        db.commit()
        
        print("=" * 60)
        print("✅ Test-User Setup abgeschlossen!")
        print("=" * 60)
        print("\n📋 Zusammenfassung:")
        print("   - Alle Passwörter: '123'")
        print("   - Level 5: qms.admin@company.com")
        print("   - Level 4: qm.mitarbeiter@company.com")
        print("   - Level 3: abteilungsleiter.service@company.com, abteilungsleiter.produktion@company.com")
        print("   - Level 2: teamleiter.service@company.com, teamleiter.it@company.com")
        print("   - Level 1: mitarbeiter.service@company.com, mitarbeiter.it@company.com")
        print("   - Bestehend: qm@company.com (Passwort zurückgesetzt)")
        print("\n🎯 Du kannst jetzt mit allen Test-Usern einloggen (Passwort: 123)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_test_users()

