"""
Evidence Integrity System
Provides cryptographic evidence integrity and legal-grade audit trails
"""

import hashlib
import json
import os
import cv2
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class EvidenceFrame:
    """Cryptographically secured evidence frame"""
    frame_id: str
    detection_id: str
    case_id: int
    footage_id: int
    timestamp: float
    frame_path: str
    frame_hash: str
    frame_size: Tuple[int, int]
    frame_format: str
    bounding_box: Tuple[int, int, int, int]
    confidence_score: float
    detection_method: str
    created_at: str
    verified_by: Optional[int] = None
    verification_timestamp: Optional[str] = None
    chain_hash: str = ""
    evidence_number: str = ""
    legal_status: str = "pending"

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class EvidenceChain:
    """Complete evidence chain for a case"""
    chain_id: str
    case_id: int
    created_at: str
    chain_hash: str
    previous_chain_hash: str = ""
    frames: List[EvidenceFrame] = None
    verified_by: Optional[int] = None
    verification_timestamp: Optional[str] = None
    legal_officer: Optional[str] = None

    def __post_init__(self):
        if self.frames is None:
            self.frames = []

    def add_frame(self, frame: EvidenceFrame):
        self.frames.append(frame)
        self._update_chain_hash()

    def _update_chain_hash(self):
        chain_data = {
            'chain_id': self.chain_id,
            'case_id': self.case_id,
            'frames': [frame.frame_hash for frame in self.frames],
            'created_at': self.created_at
        }
        chain_string = json.dumps(chain_data, sort_keys=True)
        self.chain_hash = hashlib.sha256(chain_string.encode()).hexdigest()

    def verify_integrity(self) -> Dict[str, bool]:
        results = {'chain_integrity': True, 'frame_integrity': True, 'hash_verification': True, 'file_verification': True}
        original_hash = self.chain_hash
        self._update_chain_hash()
        if original_hash != self.chain_hash:
            results['chain_integrity'] = False
            results['hash_verification'] = False
        for frame in self.frames:
            if not self._verify_frame_integrity(frame):
                results['frame_integrity'] = False
                results['file_verification'] = False
        return results

    def _verify_frame_integrity(self, frame: EvidenceFrame) -> bool:
        try:
            if not os.path.exists(frame.frame_path): return False
            current_hash = self._calculate_frame_hash(frame.frame_path)
            return current_hash == frame.frame_hash
        except: return False

    def _calculate_frame_hash(self, frame_path: str) -> str:
        try:
            img = cv2.imread(frame_path)
            if img is None: return ""
            frame_bytes = cv2.imencode('.jpg', img)[1].tobytes()
            return hashlib.sha256(frame_bytes).hexdigest()
        except: return ""

class EvidenceIntegritySystem:
    def __init__(self):
        self.evidence_dir = Path("static/evidence")
        self.evidence_dir.mkdir(exist_ok=True)
        self.evidence_counter = self._load_evidence_counter()
        self.chains: Dict[str, EvidenceChain] = {}

    def _load_evidence_counter(self) -> int:
        counter_file = self.evidence_dir / "evidence_counter.txt"
        try:
            if counter_file.exists(): return int(counter_file.read_text().strip())
            return 1
        except: return 1

    def _save_evidence_counter(self):
        counter_file = self.evidence_dir / "evidence_counter.txt"
        counter_file.write_text(str(self.evidence_counter))

    def create_evidence_frame(self, detection_data: Dict, frame_image: np.ndarray) -> EvidenceFrame:
        frame_id = self._generate_frame_id(detection_data)
        evidence_number = f"EVD-{self.evidence_counter:06d}"
        self.evidence_counter += 1
        self._save_evidence_counter()
        frame_path = self._save_evidence_frame(frame_image, frame_id, evidence_number)
        frame_hash = self._calculate_secure_frame_hash(frame_path)
        
        return EvidenceFrame(
            frame_id=frame_id, detection_id=detection_data.get('detection_id', ''),
            case_id=detection_data.get('case_id', 0), footage_id=detection_data.get('footage_id', 0),
            timestamp=detection_data.get('timestamp', 0.0), frame_path=frame_path,
            frame_hash=frame_hash, frame_size=(frame_image.shape[1], frame_image.shape[0]),
            frame_format="jpg", bounding_box=detection_data.get('bbox', (0, 0, 0, 0)),
            confidence_score=detection_data.get('confidence', 0.0),
            detection_method=detection_data.get('method', 'unknown'),
            created_at=datetime.now(timezone.utc).isoformat(),
            evidence_number=evidence_number, legal_status="pending"
        )

    def _generate_frame_id(self, detection_data: Dict) -> str:
        id_string = f"frame_{detection_data.get('case_id')}_{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]

    def _save_evidence_frame(self, frame_image: np.ndarray, frame_id: str, evidence_number: str) -> str:
        case_dir = self.evidence_dir / f"case_{frame_id[:8]}"
        case_dir.mkdir(exist_ok=True)
        frame_path = case_dir / f"{evidence_number}_{frame_id}.jpg"
        cv2.imwrite(str(frame_path), frame_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return str(frame_path)

    def _calculate_secure_frame_hash(self, frame_path: str) -> str:
        img = cv2.imread(frame_path)
        if img is None: raise ValueError("Cannot read frame")
        frame_bytes = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tobytes()
        return hashlib.sha256(frame_bytes).hexdigest()

    def create_evidence_chain(self, case_id: int) -> EvidenceChain:
        chain_id = f"chain_{case_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        chain = EvidenceChain(chain_id=chain_id, case_id=case_id, created_at=datetime.now(timezone.utc).isoformat(), chain_hash="")
        self.chains[chain_id] = chain
        return chain

    def add_frame_to_chain(self, chain_id: str, evidence_frame: EvidenceFrame):
        if chain_id not in self.chains: return
        self.chains[chain_id].add_frame(evidence_frame)
        self._save_evidence_chain(self.chains[chain_id])

    def _save_evidence_chain(self, chain: EvidenceChain):
        chain_file = self.evidence_dir / f"{chain.chain_id}.json"
        with open(chain_file, 'w') as f:
            json.dump(asdict(chain), f, indent=2)

    def load_evidence_chain(self, chain_id: str) -> Optional[EvidenceChain]:
        chain_file = self.evidence_dir / f"{chain_id}.json"
        if not chain_file.exists(): return None
        try:
            with open(chain_file, 'r') as f:
                data = json.load(f)
            chain = EvidenceChain(
                chain_id=data['chain_id'], case_id=data['case_id'],
                created_at=data['created_at'], chain_hash=data['chain_hash']
            )
            for f_data in data['frames']:
                chain.frames.append(EvidenceFrame(**f_data))
            self.chains[chain_id] = chain
            return chain
        except: return None

    def verify_evidence_integrity(self, chain_id: str) -> Dict:
        chain = self.chains.get(chain_id) or self.load_evidence_chain(chain_id)
        if not chain: return {"error": "Not found"}
        return chain.verify_integrity()

    def generate_legal_evidence_report(self, case_id: int) -> Dict:
        case_chains = [c for c in self.chains.values() if c.case_id == case_id]
        return {"case_id": case_id, "total_chains": len(case_chains)}

evidence_system = EvidenceIntegritySystem()

def create_evidence_frame(d, img): return evidence_system.create_evidence_frame(d, img)
def create_evidence_chain(cid): return evidence_system.create_evidence_chain(cid)
def verify_evidence_integrity(cid): return evidence_system.verify_evidence_integrity(cid)
def generate_legal_evidence_report(cid): return evidence_system.generate_legal_evidence_report(cid)