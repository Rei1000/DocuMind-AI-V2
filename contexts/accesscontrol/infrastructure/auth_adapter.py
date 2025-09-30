"""
DDD Auth Adapter
FastAPI-Router für DDD-Auth-Login
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from contexts.accesscontrol.application.auth_login_service import AuthLoginService, LoginResult
from contexts.accesscontrol.infrastructure.repositories import UserRepositoryImpl


class LoginRequest(BaseModel):
    """Request-Model für Login"""
    email: str
    password: str


class AuthAdapter:
    """Adapter für DDD-Auth-Endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/auth", tags=["auth"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Richtet die Auth-Routen ein"""
        
        @self.router.post("/login")
        async def login(request: LoginRequest) -> Dict[str, Any]:
            """
            DDD-Auth-Login Endpoint
            Spiegelt das Legacy-Verhalten exakt
            """
            try:
                # Repository und Service erstellen
                user_repository = UserRepositoryImpl()
                auth_service = AuthLoginService(user_repository)
                
                # Login durchführen
                result = auth_service.login(request.email, request.password)
                
                if result.success:
                    print(f"[DDD-AUTH] login ok: email={request.email}")
                    return result.data
                else:
                    print(f"[DDD-AUTH] login failed: email={request.email} status={result.status_code}")
                    raise HTTPException(
                        status_code=result.status_code,
                        detail=result.error_message
                    )
                    
            except HTTPException:
                raise
            except Exception as e:
                print(f"[DDD-AUTH] login error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
    
    def get_router(self):
        """Gibt den FastAPI-Router zurück"""
        return self.router
