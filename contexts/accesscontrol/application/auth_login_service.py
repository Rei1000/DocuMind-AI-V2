"""
DDD Auth Login Service
Spiegelt das Legacy-Auth-Verhalten exakt für DDD-Modus
"""

import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from contexts.accesscontrol.domain.entities import User
from contexts.accesscontrol.domain.repositories import UserRepository


@dataclass
class LoginResult:
    """Ergebnis eines Login-Versuchs"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AuthLoginService:
    """Service für Authentifizierung im DDD-Modus"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = os.getenv("SECRET_KEY", "test-secret-123")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    def login(self, email: str, password: str) -> LoginResult:
        """
        Authentifiziert einen Benutzer und gibt JWT-Token zurück.
        Spiegelt das Legacy-Verhalten exakt.
        
        Args:
            email: Benutzer-E-Mail
            password: Benutzer-Passwort
            
        Returns:
            LoginResult mit Status-Code und Daten
        """
        try:
            # 1. Benutzer laden
            user = self.user_repository.find_by_email(email)
            if not user:
                print(f"[DDD-AUTH] login failed: user not found email={email}")
                return LoginResult(
                    success=False,
                    status_code=401,
                    error_message="Invalid credentials"
                )
            
            # 2. Prüfe ob Benutzer aktiv ist
            if not user.is_active:
                print(f"[DDD-AUTH] login failed: user inactive email={email}")
                return LoginResult(
                    success=False,
                    status_code=403,
                    error_message="User account is inactive"
                )
            
            # 3. Passwort verifizieren
            if not self._verify_password(password, user.hashed_password):
                print(f"[DDD-AUTH] login failed: invalid password email={email}")
                return LoginResult(
                    success=False,
                    status_code=401,
                    error_message="Invalid credentials"
                )
            
            # 3.1. Transparentes Rehash bei Legacy-Hash
            if self._is_legacy_hash(user.hashed_password):
                print(f"[DDD-AUTH] legacy hash detected, upgrading to DDD policy")
                new_hash = self._hash_password_ddd_policy(password)
                if new_hash:
                    self._update_user_password(user.id, new_hash)
                    print(f"[DDD-AUTH] password rehash upgraded for user={email}")
                else:
                    print(f"[DDD-AUTH] warning: rehash failed for user={email}")
            
            # 4. JWT-Token erstellen
            token_data = self._create_token_data(user)
            access_token = self._create_jwt_token(token_data)
            
            # 5. Legacy-kompatible Antwort zusammenstellen
            response_data = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user_id": user.id,
                "user_name": user.full_name,
                "groups": self._get_user_groups(user),
                "permissions": self._get_user_permissions(user)
            }
            
            print(f"[DDD-AUTH] login ok: user={email} user_id={user.id}")
            return LoginResult(
                success=True,
                status_code=200,
                data=response_data
            )
            
        except Exception as e:
            print(f"[DDD-AUTH] login error: {e}")
            return LoginResult(
                success=False,
                status_code=500,
                error_message="Internal server error"
            )
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Multi-Hash-Verifier: Unterstützt Legacy- und DDD-Hash-Formate"""
        try:
            # Hash-Typ erkennen und entsprechend verifizieren
            if self._is_bcrypt_hash(hashed_password):
                print(f"[DDD-AUTH] verifying bcrypt hash")
                return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            elif self._is_sha256_hash(hashed_password):
                print(f"[DDD-AUTH] verifying SHA256 legacy hash")
                import hashlib
                return hashlib.sha256(password.encode()).hexdigest() == hashed_password
            elif self._is_pbkdf2_hash(hashed_password):
                print(f"[DDD-AUTH] verifying PBKDF2 hash")
                return self._verify_pbkdf2(password, hashed_password)
            elif self._is_argon2_hash(hashed_password):
                print(f"[DDD-AUTH] verifying Argon2 hash")
                return self._verify_argon2(password, hashed_password)
            elif self._is_plaintext_password(hashed_password):
                print(f"[DDD-AUTH] verifying plaintext password (test mode)")
                return password == hashed_password
            else:
                print(f"[DDD-AUTH] unknown hash format: {hashed_password[:20]}...")
                return False
        except Exception as e:
            print(f"[DDD-AUTH] password verification error: {e}")
            return False
    
    def _is_bcrypt_hash(self, hash_str: str) -> bool:
        """Erkennt bcrypt-Hashes"""
        return hash_str.startswith('$2a$') or hash_str.startswith('$2b$') or hash_str.startswith('$2y$')
    
    def _is_sha256_hash(self, hash_str: str) -> bool:
        """Erkennt SHA256-Hashes (Legacy)"""
        return len(hash_str) == 64 and all(c in '0123456789abcdef' for c in hash_str)
    
    def _is_plaintext_password(self, hash_str: str) -> bool:
        """Erkennt Klartext-Passwörter (Test/Development)"""
        # Einfache Heuristik: nicht zu kurz, nicht zu lang, enthält Buchstaben
        return (8 <= len(hash_str) <= 50 and 
                any(c.isalpha() for c in hash_str) and
                not hash_str.startswith('$') and
                not hash_str.startswith('pbkdf2'))
    
    def _is_pbkdf2_hash(self, hash_str: str) -> bool:
        """Erkennt PBKDF2-Hashes"""
        return hash_str.startswith('pbkdf2:')
    
    def _is_argon2_hash(self, hash_str: str) -> bool:
        """Erkennt Argon2-Hashes"""
        return hash_str.startswith('$argon2id$') or hash_str.startswith('$argon2i$')
    
    def _verify_pbkdf2(self, password: str, hash_str: str) -> bool:
        """Verifiziert PBKDF2-Hash"""
        try:
            import hashlib
            # Format: pbkdf2:sha256:iterations:salt:hash
            parts = hash_str.split(':')
            if len(parts) != 5:
                return False
            algorithm, hash_name, iterations, salt, stored_hash = parts
            iterations = int(iterations)
            salt = bytes.fromhex(salt)
            
            # Generiere Hash
            derived_key = hashlib.pbkdf2_hmac(hash_name, password.encode(), salt, iterations)
            return derived_key.hex() == stored_hash
        except Exception:
            return False
    
    def _verify_argon2(self, password: str, hash_str: str) -> bool:
        """Verifiziert Argon2-Hash"""
        try:
            import argon2
            return argon2.PasswordHasher().verify(hash_str, password)
        except Exception:
            return False
    
    def _is_legacy_hash(self, hash_str: str) -> bool:
        """Erkennt Legacy-Hash-Formate (nicht DDD-Standard)"""
        return (self._is_sha256_hash(hash_str) or 
                self._is_pbkdf2_hash(hash_str) or
                self._is_plaintext_password(hash_str) or
                (self._is_bcrypt_hash(hash_str) and not self._is_ddd_bcrypt(hash_str)))
    
    def _is_ddd_bcrypt(self, hash_str: str) -> bool:
        """Erkennt DDD-Standard bcrypt (z.B. mit höheren Runden)"""
        # DDD-Standard: bcrypt mit mindestens 12 Runden
        if not hash_str.startswith('$2b$'):
            return False
        try:
            parts = hash_str.split('$')
            if len(parts) >= 3:
                rounds = int(parts[2])
                return rounds >= 12  # DDD-Mindeststandard
        except:
            pass
        return False
    
    def _hash_password_ddd_policy(self, password: str) -> str:
        """Hasht Passwort nach DDD-Policy (bcrypt mit 12 Runden)"""
        try:
            import bcrypt
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception as e:
            print(f"[DDD-AUTH] DDD hash generation error: {e}")
            return None
    
    def _update_user_password(self, user_id: int, new_hash: str) -> bool:
        """Aktualisiert Benutzer-Passwort in der DB"""
        try:
            import sqlite3
            db_path = self.user_repository.db_path if hasattr(self.user_repository, 'db_path') else 'backend/qms_mvp.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET hashed_password = ? WHERE id = ?",
                    (new_hash, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"[DDD-AUTH] password update error: {e}")
            return False
    
    def _create_token_data(self, user: User) -> Dict[str, Any]:
        """Erstellt Token-Daten (spiegelt Legacy-Verhalten)"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        return {
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "iat": now,
            "exp": expire,
            "user_id": user.id,
            "groups": self._get_user_groups(user),
            "permissions": self._get_user_permissions(user)
        }
    
    def _create_jwt_token(self, token_data: Dict[str, Any]) -> str:
        """Erstellt JWT-Token (identisch zu Legacy)"""
        return jwt.encode(token_data, self.secret_key, algorithm=self.jwt_algorithm)
    
    def _get_user_groups(self, user: User) -> list:
        """Holt Benutzergruppen (spiegelt Legacy-Verhalten)"""
        # TODO: Implementiere Gruppen-Logik basierend auf Legacy
        # Für jetzt: leere Liste (wie Legacy)
        return []
    
    def _get_user_permissions(self, user: User) -> list:
        """Holt Benutzerberechtigungen (spiegelt Legacy-Verhalten)"""
        # DDD-Login muss dem Frontend sofort aussagekräftige Permissions liefern,
        # da das UI die Sichtbarkeit (z. B. IG-/Level-Editor) anhand von
        # login_result["permissions"] prüft.
        #
        # Legacy-Parität: qms.admin erhält System-Admin-Rechte.
        try:
            email = getattr(user, 'email', '') or ''
            approval_level = getattr(user, 'approval_level', 0) or 0
            employee_id = getattr(user, 'employee_id', '') or ''
        except Exception:
            email, approval_level, employee_id = '', 0, ''

        # QMS Admin: volle Admin-Rechte analog Legacy
        if email == 'qms.admin@company.com':
            return [
                'system_administration',
                'user_management',
                'all_rights',
                'final_approval',
                'document_management',
                'equipment_management',
            ]

        # Default (bis vollständige DDD-RBAC Implementierung): keine speziellen Rechte
        return []
