"""
FAISS Vector Search Service for Face Encoding Matching
Efficient similarity search for 128-d face encodings
"""
import faiss
import numpy as np
import json
import os
import pickle
from typing import List, Tuple, Optional

class FaceVectorSearchService:
    def __init__(self, dimension: int = 128, index_path: str = "instance/faiss_index.bin", nlist: int = 100):
        """
        Initialize FAISS index for face encoding search
        
        Args:
            dimension: Face encoding dimension (default: 128)
            index_path: Path to save/load FAISS index
            nlist: Number of clusters for IVF (default: 100)
        """
        self.dimension = dimension
        self.index_path = index_path
        self.mapping_path = index_path.replace('.bin', '_mapping.pkl')
        self.nlist = nlist
        self.index = None
        self.id_mapping = []  # Maps FAISS index position to database IDs
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or load FAISS index with cosine similarity"""
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            self._load_index()
        else:
            # Use IndexFlatIP for stability with small datasets (no training required)
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = []
    
    def _load_index(self):
        """Load existing FAISS index and ID mapping with backup and admin alerts"""
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.mapping_path, 'rb') as f:
                self.id_mapping = pickle.load(f)
            print(f"✅ FAISS index loaded: {self.index.ntotal} encodings")
        except Exception as e:
            print(f"❌ FAISS index load error: {e}")
            
            # Try backup restore
            backup_path = self.index_path + '.backup'
            if os.path.exists(backup_path):
                try:
                    self.index = faiss.read_index(backup_path)
                    with open(self.mapping_path + '.backup', 'rb') as f:
                        self.id_mapping = pickle.load(f)
                    print(f"✅ Restored from backup: {self.index.ntotal} encodings")
                    self._save_index()  # Save as primary
                    self._send_admin_alert('FAISS index restored from backup', 'warning')
                    return
                except:
                    pass
            
            # Alert admin about data loss
            self._send_admin_alert(f'FAISS index corrupt - creating new (data loss!): {e}', 'critical')
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = []
    
    def _save_index(self):
        """Save FAISS index with automatic backup"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Create backup before saving
        if os.path.exists(self.index_path):
            import shutil
            shutil.copy2(self.index_path, self.index_path + '.backup')
            shutil.copy2(self.mapping_path, self.mapping_path + '.backup')
        
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, 'wb') as f:
            pickle.dump(self.id_mapping, f)
    
    def _send_admin_alert(self, message: str, level: str = 'warning'):
        """Send alert to admin about FAISS issues"""
        try:
            from models import Notification, User, db
            from datetime import datetime
            
            # Get all admin users
            admins = User.query.filter_by(is_admin=True).all()
            
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    title=f'🚨 FAISS Index Alert',
                    message=message,
                    type='danger' if level == 'critical' else 'warning',
                    created_at=datetime.utcnow()
                )
                db.session.add(notification)
            
            db.session.commit()
            print(f"✅ Admin alert sent: {message}")
        except Exception as e:
            print(f"❌ Failed to send admin alert: {e}")
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity"""
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector
    
    def insert_encoding(self, face_encoding: List[float], db_id: int):
        """
        Insert a single face encoding into the index
        
        Args:
            face_encoding: 128-d face encoding as list
            db_id: Database ID (PersonProfile.id or Case.id)
        """
        vector = np.array(face_encoding, dtype=np.float32).reshape(1, -1)
        vector = self._normalize_vector(vector)
        
        # IndexFlatIP doesn't require training
        self.index.add(vector)
        self.id_mapping.append(db_id)
        self._save_index()
    
    def insert_batch(self, encodings: List[Tuple[List[float], int]]):
        """
        Insert multiple face encodings in batch
        
        Args:
            encodings: List of (face_encoding, db_id) tuples
        """
        if not encodings:
            return
        
        vectors = np.array([enc[0] for enc in encodings], dtype=np.float32)
        vectors = np.array([self._normalize_vector(v) for v in vectors])
        
        # IndexFlatIP doesn't require training
        self.index.add(vectors)
        self.id_mapping.extend([enc[1] for enc in encodings])
        self._save_index()
    
    def search(self, query_encoding: List[float], top_k: int = 3) -> List[Tuple[int, float]]:
        """
        Search for top-k most similar face encodings
        
        Args:
            query_encoding: 128-d face encoding from CCTV frame
            top_k: Number of top matches to return (default: 3)
        
        Returns:
            List of (db_id, similarity_score) tuples, sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array(query_encoding, dtype=np.float32).reshape(1, -1)
        query_vector = self._normalize_vector(query_vector)
        
        # Search returns cosine similarity scores (higher is better)
        similarities, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for idx, sim in zip(indices[0], similarities[0]):
            if idx != -1 and idx < len(self.id_mapping):
                results.append((self.id_mapping[idx], float(sim)))
        
        return results
    
    def rebuild_from_database(self, person_profiles):
        """
        Rebuild entire index from PersonProfile database records
        
        Args:
            person_profiles: Query result of PersonProfile.query.all()
        """
        # Use IndexFlatIP for stability with any dataset size
        self.index = faiss.IndexFlatIP(self.dimension)
        self.id_mapping = []
        
        encodings = []
        for profile in person_profiles:
            if profile.primary_face_encoding:
                try:
                    encoding = json.loads(profile.primary_face_encoding)
                    if len(encoding) == self.dimension:
                        encodings.append((encoding, profile.id))
                except:
                    continue
        
        if encodings:
            self.insert_batch(encodings)
    
    def remove_encoding(self, db_id: int):
        """
        Remove encoding by database ID (requires rebuild)
        Note: FAISS doesn't support efficient deletion, so we rebuild without the ID
        """
        if db_id not in self.id_mapping:
            return
        
        # Mark for rebuild - actual removal happens on next rebuild
        pass
    
    def get_index_size(self) -> int:
        """Get number of vectors in index"""
        return self.index.ntotal if self.index else 0


# Global service instance
_face_search_service = None

def get_face_search_service() -> FaceVectorSearchService:
    """Get or create global face search service instance"""
    global _face_search_service
    if _face_search_service is None:
        _face_search_service = FaceVectorSearchService()
    return _face_search_service
