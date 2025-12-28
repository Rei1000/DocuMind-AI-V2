"""
Learning-to-Rank Training Pipeline.

Infrastructure Layer: Training-Pipeline für LTR-Modelle (LightGBM Ranker).

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Features:
- Training Data Preparation
- LightGBM Ranker Training
- Cross-Validation mit NDCG@k
- Model Persistence (Save/Load)
- Feature Importance Analysis
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pickle
from pathlib import Path
import os

# LightGBM für Learning-to-Rank (mit Fallback zu sklearn)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except (ImportError, OSError) as e:
    LIGHTGBM_AVAILABLE = False
    print(f"WARNING: LightGBM not available ({e}). Using sklearn GradientBoostingRegressor as fallback.")

# sklearn für Metrics und Fallback-Model
from sklearn.model_selection import GroupKFold
from sklearn.metrics import ndcg_score
from sklearn.ensemble import GradientBoostingRegressor


class LTRTrainingPipeline:
    """
    Learning-to-Rank Training Pipeline.
    
    Verwendet LightGBM Ranker für echtes Learning-to-Rank.
    Trainiert auf historischen Query/Chunk/Relevance-Daten.
    """
    
    def __init__(
        self,
        training_data_repo,
        model_type: str = 'lightgbm',
        model_version: str = '1.0.0'
    ):
        """
        Initialisiere Training Pipeline.
        
        Args:
            training_data_repo: Repository für Training-Daten
            model_type: Typ des Models ('lightgbm' oder 'xgboost')
            model_version: Model-Version für Tracking
        """
        self.training_data_repo = training_data_repo
        self.model_version = model_version
        self.model = None
        self._is_trained = False
        
        # Bestimme Model-Typ basierend auf Verfügbarkeit
        if LIGHTGBM_AVAILABLE:
            self.model_type = 'lightgbm'
            print("✅ Verwende LightGBM Ranker für LTR")
        else:
            self.model_type = 'sklearn'
            print("⚠️ Verwende sklearn GradientBoostingRegressor als Fallback (LightGBM nicht verfügbar)")
        
        # Feature Extractor
        from .features.feature_extractor import MLFeatureExtractor
        self.feature_extractor = MLFeatureExtractor()
    
    def is_trained(self) -> bool:
        """Prüfe ob Model trainiert ist."""
        return self._is_trained and self.model is not None
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bereite Training-Daten vor.
        
        Returns:
            Tuple (X, y, qids)
            - X: Feature-Matrix (n_samples, 11)
            - y: Relevance Scores (n_samples,)
            - qids: Query-IDs (n_samples,) für Ranking
        """
        # Hole Training-Samples aus Repository
        training_samples = self.training_data_repo.get_training_samples()
        
        if not training_samples or len(training_samples) == 0:
            raise ValueError("Keine Training-Daten verfügbar")
        
        # Extrahiere Features
        features_list = []
        relevance_scores = []
        query_ids = []
        
        # Query-ID Mapping (String → Integer)
        query_to_id = {}
        current_qid = 0
        
        for sample in training_samples:
            # Extrahiere Features
            features = self.feature_extractor.extract(
                query=sample['query'],
                chunk=sample['chunk'],
                vector_score=sample['vector_score'],
                text_score=sample['text_score'],
                bm25_score=sample.get('bm25_score', 0.0),
                jaccard_score=sample.get('jaccard_score', 0.0),
                keyword_matches=sample['keyword_matches'],
                user_level=sample['user_level'],
                hybrid_score=sample['hybrid_score']
            )
            
            features_list.append(features)
            relevance_scores.append(sample['relevance_score'])
            
            # Query-ID für Ranking
            query = sample['query']
            if query not in query_to_id:
                query_to_id[query] = current_qid
                current_qid += 1
            query_ids.append(query_to_id[query])
        
        # Konvertiere zu numpy arrays
        X = np.array(features_list, dtype=np.float64)
        y = np.array(relevance_scores, dtype=np.float64)
        qids = np.array(query_ids, dtype=np.int32)
        
        return X, y, qids
    
    def train(
        self,
        num_boost_round: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 6,
        num_leaves: int = 31
    ):
        """
        Trainiere LTR-Modell.
        
        Args:
            num_boost_round: Anzahl Boosting-Runden
            learning_rate: Learning Rate
            max_depth: Maximale Baum-Tiefe
            num_leaves: Maximale Anzahl Blätter
            
        Returns:
            Trainiertes Model
        """
        # Prepare Data
        X, y, qids = self.prepare_training_data()
        
        if self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            # LightGBM Ranker
            train_data = lgb.Dataset(X, label=y, group=self._get_query_groups(qids))
            
            params = {
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [1, 3, 5, 10],
                'num_leaves': num_leaves,
                'max_depth': max_depth,
                'learning_rate': learning_rate,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1
            }
            
            self.model = lgb.train(
                params,
                train_data,
                num_boost_round=num_boost_round
            )
        else:
            # sklearn Fallback (GradientBoostingRegressor)
            print("⚠️ Training mit sklearn GradientBoostingRegressor (Fallback)")
            
            self.model = GradientBoostingRegressor(
                n_estimators=num_boost_round,
                learning_rate=learning_rate,
                max_depth=max_depth,
                subsample=0.8,
                random_state=42
            )
            
            self.model.fit(X, y)
        
        self._is_trained = True
        
        return self.model
    
    def _get_query_groups(self, qids: np.ndarray) -> List[int]:
        """
        Berechne Query-Groups für LightGBM Ranker.
        
        LightGBM benötigt die Anzahl von Samples pro Query (nicht die Query-IDs).
        
        Args:
            qids: Query-IDs Array (n_samples,)
            
        Returns:
            Liste mit Anzahl Samples pro Query
        """
        unique_qids, counts = np.unique(qids, return_counts=True)
        return counts.tolist()
    
    def train_and_validate(
        self,
        n_splits: int = 3,
        **train_kwargs
    ) -> Dict[str, float]:
        """
        Trainiere und validiere Model mit Cross-Validation.
        
        Args:
            n_splits: Anzahl CV-Splits
            **train_kwargs: Training-Parameter
            
        Returns:
            Dict mit Validation-Scores
        """
        # Prepare Data
        X, y, qids = self.prepare_training_data()
        
        # GroupKFold (gruppiert nach Query-ID)
        gkf = GroupKFold(n_splits=n_splits)
        
        ndcg_scores = []
        
        for train_idx, val_idx in gkf.split(X, y, groups=qids):
            # Split Data
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            qids_train, qids_val = qids[train_idx], qids[val_idx]
            
            # Train on Fold
            if self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
                # LightGBM Ranker
                train_data = lgb.Dataset(
                    X_train,
                    label=y_train,
                    group=self._get_query_groups(qids_train)
                )
                
                params = {
                    'objective': 'lambdarank',
                    'metric': 'ndcg',
                    'ndcg_eval_at': [1, 3, 5, 10],
                    'num_leaves': train_kwargs.get('num_leaves', 31),
                    'max_depth': train_kwargs.get('max_depth', 6),
                    'learning_rate': train_kwargs.get('learning_rate', 0.1),
                    'verbose': -1
                }
                
                fold_model = lgb.train(
                    params,
                    train_data,
                    num_boost_round=train_kwargs.get('num_boost_round', 100)
                )
            else:
                # sklearn Fallback
                fold_model = GradientBoostingRegressor(
                    n_estimators=train_kwargs.get('num_boost_round', 100),
                    learning_rate=train_kwargs.get('learning_rate', 0.1),
                    max_depth=train_kwargs.get('max_depth', 6),
                    subsample=0.8,
                    random_state=42
                )
                fold_model.fit(X_train, y_train)
            
            # Predict on Validation Set
            y_pred = fold_model.predict(X_val)
            
            # Berechne NDCG@10 pro Query
            fold_ndcg_scores = []
            for qid in np.unique(qids_val):
                qid_mask = qids_val == qid
                y_true_query = y_val[qid_mask].reshape(1, -1)
                y_pred_query = y_pred[qid_mask].reshape(1, -1)
                
                # NDCG@10 (oder weniger falls Query < 10 Dokumente hat)
                k = min(10, len(y_true_query[0]))
                ndcg = ndcg_score(y_true_query, y_pred_query, k=k)
                fold_ndcg_scores.append(ndcg)
            
            # Durchschnittlicher NDCG für diesen Fold
            fold_ndcg_mean = np.mean(fold_ndcg_scores) if fold_ndcg_scores else 0.0
            ndcg_scores.append(fold_ndcg_mean)
        
        # Final Training auf allen Daten
        self.train(**train_kwargs)
        
        # Return Validation Scores
        return {
            'ndcg_mean': float(np.mean(ndcg_scores)),
            'ndcg_std': float(np.std(ndcg_scores)),
            'ndcg_scores': [float(s) for s in ndcg_scores]
        }
    
    def save_model(self, path: str):
        """
        Speichere trainiertes Model.
        
        Args:
            path: Pfad zur Model-Datei (.pkl oder .txt)
        """
        if not self.is_trained():
            raise ValueError("Model ist nicht trainiert")
        
        # Erstelle Verzeichnis falls nicht vorhanden
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Speichere Model
        if self.model_type == 'lightgbm' and path.endswith('.txt'):
            # LightGBM native Format
            self.model.save_model(path)
        else:
            # Pickle Format (für alle Model-Typen)
            model_data = {
                'model': self.model,
                'model_type': self.model_type,
                'model_version': self.model_version,
                'feature_names': self.feature_extractor.feature_names
            }
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)
    
    def load_model(self, path: str):
        """
        Lade trainiertes Model.
        
        Args:
            path: Pfad zur Model-Datei
            
        Returns:
            Geladenes Model
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model-File nicht gefunden: {path}")
        
        # Lade Model
        if path.endswith('.txt') and LIGHTGBM_AVAILABLE:
            # LightGBM native Format
            self.model = lgb.Booster(model_file=path)
            self.model_type = 'lightgbm'
        else:
            # Pickle Format (für alle Model-Typen)
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.model_type = model_data.get('model_type', 'sklearn')
                self.model_version = model_data.get('model_version', '1.0.0')
        
        self._is_trained = True
        
        return self.model


