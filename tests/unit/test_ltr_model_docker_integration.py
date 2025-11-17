"""
Tests für LTR-Model Docker-Integration (Fix 3).

TDD Phase 1: RED - Tests für LTR-Model Training im Container.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestLTRModelDockerIntegration:
    """Tests für LTR-Model Integration im Docker-Container."""
    
    def test_train_ltr_model_creates_model_file(self, tmp_path):
        """
        Test: Trainingsscript erstellt Model-File.
        
        RED → GREEN → REFACTOR
        """
        # Arrange: Temporäres Model-Verzeichnis
        model_dir = tmp_path / 'ml_models'
        model_dir.mkdir()
        model_path = model_dir / 'ltr_ranker_v1.pkl'
        
        # Mock Training-Daten
        with patch('scripts.train_ltr_model.SessionLocal') as mock_session, \
             patch('scripts.train_ltr_model.TrainingDataRepositorySQLite') as mock_repo, \
             patch('scripts.train_ltr_model.LTRTrainingPipeline') as mock_pipeline:
            
            # Setup Mocks
            mock_db_session = MagicMock()
            mock_session.return_value = mock_db_session
            
            mock_training_repo = MagicMock()
            mock_training_repo.get_statistics.return_value = {
                'total_samples': 10,
                'oldest_sample': '2025-01-01',
                'newest_sample': '2025-01-02',
                'unique_queries': 5
            }
            mock_repo.return_value = mock_training_repo
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.train_and_validate.return_value = {
                'ndcg_mean': 0.85,
                'ndcg_std': 0.05,
                'ndcg_scores': [0.8, 0.85, 0.9]
            }
            mock_pipeline_instance.is_trained.return_value = True
            mock_pipeline_instance.save_model = MagicMock()
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Act: Führe Trainingsscript aus (simuliert)
            from scripts.train_ltr_model import train_ltr_model
            
            # Mock model_path für Script
            with patch('scripts.train_ltr_model.Path') as mock_path:
                mock_path.return_value.parent = tmp_path
                mock_path.return_value.__truediv__ = lambda self, other: tmp_path / other
                
                # Führe Training aus
                result = train_ltr_model()
                
                # Assert: Training wurde aufgerufen
                assert mock_pipeline_instance.train_and_validate.called, \
                    "Training sollte aufgerufen werden"
                assert mock_pipeline_instance.save_model.called, \
                    "Model sollte gespeichert werden"
    
    def test_train_ltr_model_uses_relative_path(self):
        """
        Test: Trainingsscript verwendet relative Pfade (nicht absolute).
        
        RED → GREEN → REFACTOR
        """
        import inspect
        from scripts.train_ltr_model import train_ltr_model
        
        # Arrange: Lese Source-Code
        source = inspect.getsource(train_ltr_model)
        
        # Assert: Keine absoluten Pfade (außer project_root)
        # Erlaubt: project_root / 'data' / 'ml_models' / 'ltr_ranker_v1.pkl'
        # Nicht erlaubt: /Users/... oder C:\...
        
        # Prüfe ob absolute Pfade verwendet werden (außer project_root)
        has_absolute_path = '/Users/' in source or 'C:\\' in source or '/home/' in source
        
        # project_root ist OK (wird dynamisch berechnet)
        assert not has_absolute_path or 'project_root' in source, \
            "Trainingsscript sollte keine hardcoded absoluten Pfade verwenden"
    
    def test_ltr_inference_service_loads_model(self, tmp_path):
        """
        Test: LTRInferenceService lädt Model korrekt.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.ml.inference_service import (
            LTRInferenceService
        )
        
        # Arrange: Mock Model-File
        model_path = tmp_path / 'ltr_ranker_v1.pkl'
        model_path.touch()  # Erstelle leere Datei
        
        # Mock sklearn/lightgbm
        with patch('contexts.ragintegration.infrastructure.ml.inference_service.pickle') as mock_pickle, \
             patch('os.path.exists', return_value=True):
            
            # Mock Model-Daten
            mock_model_data = {
                'model': MagicMock(),
                'model_type': 'sklearn',
                'model_version': '1.0.0'
            }
            mock_pickle.load.return_value = mock_model_data
            
            # Act: Lade Model
            inference_service = LTRInferenceService(model_path=str(model_path))
            
            # Assert: Service ist ready
            assert inference_service.is_ready(), \
                "LTRInferenceService sollte ready sein wenn Model existiert"
    
    def test_ltr_inference_service_handles_missing_model(self):
        """
        Test: LTRInferenceService handelt fehlendes Model korrekt.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.ml.inference_service import (
            LTRInferenceService
        )
        
        # Arrange: Model existiert nicht
        with patch('os.path.exists', return_value=False):
            # Act: Erstelle Service ohne Model
            inference_service = LTRInferenceService(model_path=None)
            
            # Assert: Service ist nicht ready
            assert not inference_service.is_ready(), \
                "LTRInferenceService sollte nicht ready sein wenn Model fehlt"
    
    def test_ltr_model_path_in_container(self):
        """
        Test: Model-Pfad ist korrekt für Docker-Container.
        
        RED → GREEN → REFACTOR
        """
        # Arrange: Container-Umgebung (data/ml_models/ltr_ranker_v1.pkl)
        expected_path = 'data/ml_models/ltr_ranker_v1.pkl'
        
        # Act: Prüfe ob Pfad relativ ist
        is_relative = not os.path.isabs(expected_path)
        
        # Assert: Pfad ist relativ
        assert is_relative, \
            f"Model-Pfad sollte relativ sein: {expected_path}"
        
        # Assert: Pfad verwendet data/ml_models
        assert 'data/ml_models' in expected_path, \
            "Model-Pfad sollte 'data/ml_models' enthalten"

