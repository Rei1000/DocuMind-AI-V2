"""
Seed Script - Erstellt Initial-Daten für DocuMind-AI V2

Erstellt:
- QMS Admin (Level 5) mit Level 4 in allen Groups
- 5 Interest Groups (QM, Produktion, Service, Einkauf, Vertrieb)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal, Base, engine
from app.models import User, InterestGroup, UserGroupMembership, DocumentTypeModel
import bcrypt
import json
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_database():
    """Seed the database with initial data"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"✅ Database already seeded ({existing_users} users exist)")
            return
        
        print("🌱 Seeding database...")
        
        # Create QMS Admin User (Level 5 - System Admin)
        admin_user = User(
            email="qms.admin@company.com",
            full_name="QMS Administrator",
            employee_id="QMS-001",
            organizational_unit="Quality Management",
            hashed_password=hash_password("Admin!234"),
            individual_permissions=json.dumps(["manage_users", "manage_groups", "manage_documents"]),
            is_qms_admin=True,  # Level 5 - System Admin
            cannot_be_deleted=True,  # Protection
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(admin_user)
        db.flush()  # Get admin_user.id for relationships
        
        # Create 5 Interest Groups (Start-Set)
        interest_groups_data = [
            ("Qualitätsmanagement", "QM", "Quality management and compliance"),
            ("Produktion", "PR", "Manufacturing and production"),
            ("Service", "SV", "Customer service and support"),
            ("Einkauf", "EK", "Procurement and supplier management"),
            ("Vertrieb", "VT", "Sales and customer relations"),
        ]
        
        created_groups = []
        for name, code, description in interest_groups_data:
            group = InterestGroup(
                name=name,
                code=code,
                description=description,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by_id=admin_user.id  # Created by QMS Admin
            )
            db.add(group)
            created_groups.append(group)
        
        db.flush()  # Get group IDs
        
        # Assign QMS Admin to ALL groups with Level 4 (for testing)
        for group in created_groups:
            membership = UserGroupMembership(
                user_id=admin_user.id,
                interest_group_id=group.id,
                role_in_group="QM Manager",
                approval_level=4,  # Level 4 in all groups for testing
                is_department_head=True,
                is_active=True,
                assigned_by_id=admin_user.id  # Self-assigned
            )
            db.add(membership)
        
        # ===== Document Types (Standard QMS-Dokumenttypen) =====
        
        document_types_data = [
            ("SOP", "STANDARD_SOP", "Standard Operating Procedure - Standardarbeitsanweisung", 
             [".pdf", ".docx"], 20, False, False, 10),
            ("Flussdiagramm", "FLOWCHART", "Prozess-Flussdiagramm für visuelle Prozessdarstellung", 
             [".pdf", ".png", ".jpg", ".jpeg", ".svg"], 10, False, True, 20),
            ("Arbeitsanweisung", "WORK_INSTRUCTION", "Detaillierte Arbeitsanweisung für spezifische Tätigkeiten", 
             [".pdf", ".docx"], 15, False, False, 30),
            ("Formular", "FORM", "QMS-Formular für Datenerfassung", 
             [".pdf", ".docx", ".xlsx"], 10, False, False, 40),
            ("Verfahrensanweisung", "PROCEDURE", "Verfahrensanweisung (PA) für übergeordnete Prozesse", 
             [".pdf", ".docx"], 20, False, False, 50),
            ("Prüfanweisung", "TEST_INSTRUCTION", "Anweisung für Qualitätsprüfungen", 
             [".pdf", ".docx"], 15, False, False, 60),
            ("Checkliste", "CHECKLIST", "Prüf- oder Audit-Checkliste", 
             [".pdf", ".docx", ".xlsx"], 10, False, False, 70),
        ]
        
        print("\n📄 Creating document types...")
        for name, code, description, file_types, max_size, ocr, vision, sort in document_types_data:
            # Check if document type already exists
            existing = db.query(DocumentTypeModel).filter(DocumentTypeModel.code == code).first()
            if not existing:
                doc_type = DocumentTypeModel(
                    name=name,
                    code=code,
                    description=description,
                    allowed_file_types=json.dumps(file_types),
                    max_file_size_mb=max_size,
                    requires_ocr=ocr,
                    requires_vision=vision,
                    created_by=admin_user.id,
                    is_active=True,
                    sort_order=sort,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(doc_type)
                print(f"   ✅ Created: {name} ({code})")
            else:
                print(f"   ⏭️  Exists: {name} ({code})")
        
        db.commit()
        
        print("\n✅ Database seeded successfully!")
        print(f"   - Created QMS Admin (qms.admin@company.com / Admin!234)")
        print(f"   - Created {len(interest_groups_data)} interest groups: {', '.join([g[0] for g in interest_groups_data])}")
        print(f"   - Created {len(document_types_data)} document types")
        print(f"   - QMS Admin has Level 4 in all groups (for testing)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
