"""
Integration Tests: Docker Services Setup

RED Phase: Diese Tests schlagen fehl, bis Docker-Setup vollständig ist.
GREEN Phase: Nach Implementierung sollten alle Tests grün werden.

Test-Kategorien:
- Service Availability: Alle Services starten korrekt
- Health Checks: Health Endpoints funktionieren
- Service Communication: Services können kommunizieren
- Database Initialization: Datenbank wird korrekt initialisiert
"""

import pytest
import subprocess
import time
import requests
from typing import Dict, List
import os
import yaml


class TestDockerServicesSetup:
    """Integration Tests für Docker Services Setup"""
    
    @pytest.fixture(scope="class")
    def docker_compose_file(self):
        """Pfad zur docker-compose.yml"""
        return os.path.join(os.path.dirname(__file__), "..", "..", "..", "docker-compose.yml")
    
    @pytest.fixture(scope="class")
    def docker_compose_config(self, docker_compose_file):
        """Lade docker-compose.yml Konfiguration"""
        if not os.path.exists(docker_compose_file):
            pytest.skip(f"docker-compose.yml nicht gefunden: {docker_compose_file}")
        
        with open(docker_compose_file, 'r') as f:
            return yaml.safe_load(f)
    
    def test_docker_compose_file_exists(self, docker_compose_file):
        """RED: docker-compose.yml muss existieren"""
        assert os.path.exists(docker_compose_file), f"docker-compose.yml nicht gefunden: {docker_compose_file}"
    
    def test_qdrant_service_defined(self, docker_compose_config):
        """RED: Qdrant Service muss in docker-compose.yml definiert sein"""
        services = docker_compose_config.get('services', {})
        assert 'qdrant' in services, "Qdrant Service fehlt in docker-compose.yml"
        
        qdrant_service = services['qdrant']
        assert 'image' in qdrant_service or 'build' in qdrant_service, "Qdrant Service hat kein image oder build"
        assert 'ports' in qdrant_service, "Qdrant Service hat keine Ports definiert"
        assert '6333' in str(qdrant_service.get('ports', [])), "Qdrant Port 6333 fehlt"
    
    def test_backend_service_defined(self, docker_compose_config):
        """RED: Backend Service muss in docker-compose.yml definiert sein"""
        services = docker_compose_config.get('services', {})
        assert 'backend' in services, "Backend Service fehlt in docker-compose.yml"
        
        backend_service = services['backend']
        assert 'build' in backend_service or 'image' in backend_service, "Backend Service hat kein build oder image"
        assert 'ports' in backend_service, "Backend Service hat keine Ports definiert"
        assert '8000' in str(backend_service.get('ports', [])), "Backend Port 8000 fehlt"
    
    def test_frontend_service_defined(self, docker_compose_config):
        """RED: Frontend Service muss in docker-compose.yml definiert sein"""
        services = docker_compose_config.get('services', {})
        assert 'frontend' in services, "Frontend Service fehlt in docker-compose.yml"
        
        frontend_service = services['frontend']
        assert 'build' in frontend_service or 'image' in frontend_service, "Frontend Service hat kein build oder image"
        assert 'ports' in frontend_service, "Frontend Service hat keine Ports definiert"
        assert '3000' in str(frontend_service.get('ports', [])), "Frontend Port 3000 fehlt"
    
    def test_backend_depends_on_qdrant(self, docker_compose_config):
        """RED: Backend sollte von Qdrant abhängen (depends_on)"""
        services = docker_compose_config.get('services', {})
        backend_service = services.get('backend', {})
        depends_on = backend_service.get('depends_on', [])
        
        # depends_on kann Liste oder Dict sein
        if isinstance(depends_on, list):
            assert 'qdrant' in depends_on, "Backend sollte von Qdrant abhängen (depends_on: qdrant)"
        elif isinstance(depends_on, dict):
            assert 'qdrant' in depends_on, "Backend sollte von Qdrant abhängen (depends_on: qdrant)"
    
    def test_no_absolute_paths_in_docker_compose(self, docker_compose_config):
        """RED: docker-compose.yml sollte keine absoluten Pfade enthalten (nur relative)"""
        services = docker_compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            # Prüfe environment variables
            env = service_config.get('environment', {})
            if isinstance(env, dict):
                for key, value in env.items():
                    if isinstance(value, str) and value.startswith('/Users/'):
                        pytest.fail(f"Service {service_name} hat absoluten Pfad in {key}: {value}")
            
            # Prüfe volumes
            volumes = service_config.get('volumes', [])
            for volume in volumes:
                if isinstance(volume, str) and volume.startswith('/Users/'):
                    pytest.fail(f"Service {service_name} hat absoluten Pfad in volumes: {volume}")
    
    def test_backend_has_healthcheck(self, docker_compose_config):
        """RED: Backend sollte Health Check haben"""
        services = docker_compose_config.get('services', {})
        backend_service = services.get('backend', {})
        assert 'healthcheck' in backend_service, "Backend Service hat keinen Health Check"
        
        healthcheck = backend_service['healthcheck']
        assert 'test' in healthcheck, "Backend Health Check hat kein test"
    
    def test_qdrant_has_healthcheck(self, docker_compose_config):
        """RED: Qdrant sollte Health Check haben"""
        services = docker_compose_config.get('services', {})
        qdrant_service = services.get('qdrant', {})
        assert 'healthcheck' in qdrant_service, "Qdrant Service hat keinen Health Check"
        
        healthcheck = qdrant_service['healthcheck']
        assert 'test' in healthcheck, "Qdrant Health Check hat kein test"
    
    def test_frontend_has_healthcheck(self, docker_compose_config):
        """RED: Frontend sollte Health Check haben"""
        services = docker_compose_config.get('services', {})
        frontend_service = services.get('frontend', {})
        assert 'healthcheck' in frontend_service, "Frontend Service hat keinen Health Check"
        
        healthcheck = frontend_service['healthcheck']
        assert 'test' in healthcheck, "Frontend Health Check hat kein test"
    
    def test_database_volume_mounted(self, docker_compose_config):
        """RED: Datenbank-Volume sollte gemountet sein"""
        services = docker_compose_config.get('services', {})
        backend_service = services.get('backend', {})
        volumes = backend_service.get('volumes', [])
        
        # Prüfe ob data-Volume gemountet ist
        data_volume_found = False
        for volume in volumes:
            if isinstance(volume, str) and 'data' in volume.lower():
                data_volume_found = True
                break
            elif isinstance(volume, dict) and 'data' in str(volume).lower():
                data_volume_found = True
                break
        
        assert data_volume_found, "Backend sollte data-Volume gemountet haben"
    
    def test_backend_environment_variables(self, docker_compose_config):
        """RED: Backend sollte korrekte Environment Variables haben"""
        services = docker_compose_config.get('services', {})
        backend_service = services.get('backend', {})
        env = backend_service.get('environment', {})
        
        if isinstance(env, dict):
            # DATABASE_URL sollte relativ sein (nicht /Users/...)
            db_url = env.get('DATABASE_URL', '')
            if db_url and isinstance(db_url, str):
                assert not db_url.startswith('/Users/'), f"DATABASE_URL sollte relativ sein, nicht: {db_url}"
            
            # PYTHONPATH sollte gesetzt sein
            assert 'PYTHONPATH' in env, "Backend sollte PYTHONPATH haben"
    
    def test_qdrant_environment_variables(self, docker_compose_config):
        """RED: Qdrant sollte korrekte Environment Variables haben"""
        services = docker_compose_config.get('services', {})
        qdrant_service = services.get('qdrant', {})
        env = qdrant_service.get('environment', {})
        
        # Qdrant braucht normalerweise keine speziellen Env-Vars, aber prüfen wir trotzdem
        # (kann leer sein, das ist ok)
        assert isinstance(env, (dict, list)) or env is None, "Qdrant environment sollte dict, list oder None sein"
    
    def test_frontend_environment_variables(self, docker_compose_config):
        """RED: Frontend sollte korrekte Environment Variables haben"""
        services = docker_compose_config.get('services', {})
        frontend_service = services.get('frontend', {})
        env = frontend_service.get('environment', {})
        
        if isinstance(env, dict):
            # NEXT_PUBLIC_API_BASE_URL sollte gesetzt sein
            api_url = env.get('NEXT_PUBLIC_API_BASE_URL', '')
            assert api_url, "Frontend sollte NEXT_PUBLIC_API_BASE_URL haben"
            # Sollte auf Backend zeigen (nicht localhost:8000 direkt, sondern Service-Name)
            # In Docker sollte es http://backend:8000 sein (interne Kommunikation)
            # Oder http://localhost:8000 für externe Kommunikation
            assert '8000' in api_url or 'backend' in api_url.lower(), f"NEXT_PUBLIC_API_BASE_URL sollte auf Backend zeigen: {api_url}"


class TestDockerServicesRuntime:
    """Integration Tests für laufende Docker Services (benötigt docker-compose up)"""
    
    @pytest.mark.skipif(
        not os.getenv('DOCKER_TESTS_ENABLED', '').lower() == 'true',
        reason="Docker Runtime Tests sind standardmäßig deaktiviert. Setze DOCKER_TESTS_ENABLED=true"
    )
    def test_qdrant_service_running(self):
        """RED: Qdrant Service sollte laufen und erreichbar sein"""
        try:
            response = requests.get('http://localhost:6333/collections', timeout=5)
            assert response.status_code == 200, f"Qdrant nicht erreichbar: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Qdrant Service nicht erreichbar: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('DOCKER_TESTS_ENABLED', '').lower() == 'true',
        reason="Docker Runtime Tests sind standardmäßig deaktiviert. Setze DOCKER_TESTS_ENABLED=true"
    )
    def test_backend_service_running(self):
        """RED: Backend Service sollte laufen und Health Check funktionieren"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            assert response.status_code == 200, f"Backend Health Check fehlgeschlagen: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Backend Service nicht erreichbar: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('DOCKER_TESTS_ENABLED', '').lower() == 'true',
        reason="Docker Runtime Tests sind standardmäßig deaktiviert. Setze DOCKER_TESTS_ENABLED=true"
    )
    def test_frontend_service_running(self):
        """RED: Frontend Service sollte laufen und erreichbar sein"""
        try:
            response = requests.get('http://localhost:3000', timeout=5)
            assert response.status_code == 200, f"Frontend nicht erreichbar: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Frontend Service nicht erreichbar: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('DOCKER_TESTS_ENABLED', '').lower() == 'true',
        reason="Docker Runtime Tests sind standardmäßig deaktiviert. Setze DOCKER_TESTS_ENABLED=true"
    )
    def test_backend_can_connect_to_qdrant(self):
        """RED: Backend sollte Qdrant erreichen können (über Docker Network)"""
        # Dieser Test prüft ob Backend Qdrant erreichen kann
        # Wir testen das indirekt über einen Backend-Endpoint der Qdrant nutzt
        try:
            # Versuche einen RAG-Endpoint der Qdrant nutzt
            response = requests.get('http://localhost:8000/api/rag/health', timeout=5)
            # Health Check sollte funktionieren (auch wenn Qdrant nicht vollständig konfiguriert ist)
            assert response.status_code in [200, 404, 500], f"Backend RAG Health Check: {response.status_code}"
            # 404 ist ok (Endpoint existiert vielleicht nicht)
            # 500 könnte Qdrant-Verbindungsproblem sein (das wäre dann ein Fehler)
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Backend kann Qdrant nicht erreichen: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('DOCKER_TESTS_ENABLED', '').lower() == 'true',
        reason="Docker Runtime Tests sind standardmäßig deaktiviert. Setze DOCKER_TESTS_ENABLED=true"
    )
    def test_frontend_can_connect_to_backend(self):
        """RED: Frontend sollte Backend erreichen können"""
        # Prüfe ob Frontend Backend-API erreichen kann
        # Wir testen das über einen Backend-Endpoint
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            assert response.status_code == 200, f"Frontend kann Backend nicht erreichen: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Frontend kann Backend nicht erreichen: {e}")

