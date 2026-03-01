"""
Celery Tasks for Parallel Batch Analysis
"""
from celery import group
from __init__ import create_app, db, make_celery
from models import Case, SurveillanceFootage, LocationMatch, PersonDetection
from batch_processor import analyze_single_footage_strict
import logging

logger = logging.getLogger(__name__)

app = create_app()
celery = make_celery(app)


@celery.task(bind=True)
def analyze_batch_parallel(self, case_id, footage_ids, batch_id):
    """Parallel batch analysis - all videos simultaneously"""
    try:
        # Create parallel task group
        job = group(
            analyze_footage_task.s(case_id, fid, batch_id) 
            for fid in footage_ids
        )
        
        # Execute all in parallel
        result = job.apply_async()
        results = result.get(timeout=600)  # 10 min timeout
        
        return {
            'batch_id': batch_id,
            'total_detections': sum(r.get('detections', 0) for r in results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Batch task failed: {e}")
        return {'error': str(e)}


@celery.task(bind=True)
def analyze_footage_task(self, case_id, footage_id, batch_id):
    """Single footage analysis worker"""
    try:
        with app.app_context():
            result = analyze_single_footage_strict(case_id, footage_id, batch_id)
            return result
            
    except Exception as e:
        logger.error(f"Footage {footage_id} analysis failed: {e}")
        return {'footage_id': footage_id, 'error': str(e)}
