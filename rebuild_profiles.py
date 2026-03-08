"""
Profile Rebuilder - Fix Missing PersonProfile Records
Generates face encodings for Approved cases without PersonProfile
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import Case, PersonProfile, TargetImage
import face_recognition
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rebuild_missing_profiles():
    """Rebuild PersonProfile records for cases missing them"""
    app = create_app()
    
    with app.app_context():
        logger.info("🔄 Starting PersonProfile rebuild...")
        
        # Find Approved/Under Processing cases without PersonProfile
        cases_without_profiles = db.session.query(Case).outerjoin(PersonProfile).filter(
            Case.status.in_(['Approved', 'Under Processing']),
            PersonProfile.id.is_(None)
        ).all()
        
        logger.info(f"Found {len(cases_without_profiles)} cases without PersonProfile")
        
        profiles_created = 0
        
        for case in cases_without_profiles:
            try:
                # Get case images
                target_images = TargetImage.query.filter_by(case_id=case.id).all()
                
                if not target_images:
                    logger.warning(f"Case {case.id} ({case.person_name}) has no images - skipping")
                    continue
                
                # Extract face encodings from images
                face_encodings = []
                for target_image in target_images:
                    image_path = os.path.join('static', target_image.image_path)
                    if not os.path.exists(image_path):
                        image_path = os.path.join('app', 'static', target_image.image_path)
                    
                    if os.path.exists(image_path):
                        try:
                            image = face_recognition.load_image_file(image_path)
                            encodings = face_recognition.face_encodings(image)
                            if encodings:
                                face_encodings.extend([enc.tolist() for enc in encodings])
                                logger.info(f"✅ Extracted {len(encodings)} encodings from {target_image.image_path}")
                        except Exception as e:
                            logger.error(f"Error processing {image_path}: {e}")
                
                if not face_encodings:
                    logger.warning(f"No face encodings found for case {case.id} - skipping")
                    continue
                
                # Create PersonProfile
                profile = PersonProfile(
                    case_id=case.id,
                    primary_face_encoding=json.dumps(face_encodings[0]),
                    face_quality_score=0.8,
                    profile_confidence=0.9
                )
                
                # Store multiple encodings if available
                if len(face_encodings) > 1:
                    profile.front_encodings = json.dumps(face_encodings[:3])  # Store up to 3
                
                db.session.add(profile)
                profiles_created += 1
                
                logger.info(f"✅ Created PersonProfile for case {case.id} ({case.person_name}) with {len(face_encodings)} encodings")
                
            except Exception as e:
                logger.error(f"Error creating profile for case {case.id}: {e}")
                continue
        
        if profiles_created > 0:
            db.session.commit()
            logger.info(f"🎉 Successfully created {profiles_created} PersonProfile records")
            
            # Trigger FAISS rebuild
            try:
                from migrate_faiss_index import migrate_faiss_index
                migrate_faiss_index()
                logger.info("✅ FAISS index rebuilt successfully")
            except Exception as e:
                logger.error(f"FAISS rebuild failed: {e}")
        else:
            logger.info("No profiles created - all cases already have profiles or no valid images")
        
        return profiles_created

if __name__ == "__main__":
    logger.info("Starting PersonProfile rebuild script...")
    count = rebuild_missing_profiles()
    logger.info(f"Rebuild complete: {count} profiles created")