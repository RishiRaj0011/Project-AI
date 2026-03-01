# Add to end of admin.py

@admin_bp.route("/analyze-batch/<int:case_id>", methods=["POST"])
@login_required
@admin_required
def analyze_batch(case_id):
    """Batch analyze multiple footages with strict accuracy"""
    try:
        case = Case.query.get_or_404(case_id)
        footage_ids = request.json.get('footage_ids', [])
        
        if not footage_ids:
            return jsonify({'success': False, 'error': 'No footage selected'})
        
        batch_id = f"batch_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Trigger parallel Celery tasks
        try:
            from tasks import analyze_batch_parallel
            task = analyze_batch_parallel.delay(case_id, footage_ids, batch_id)
            
            return jsonify({
                'success': True,
                'batch_id': batch_id,
                'task_id': task.id,
                'footage_count': len(footage_ids),
                'message': f'Analyzing {len(footage_ids)} videos in parallel'
            })
        except ImportError:
            # Fallback: direct processing
            from batch_processor import process_batch_direct
            results = process_batch_direct(case_id, footage_ids, batch_id)
            
            return jsonify({
                'success': True,
                'batch_id': batch_id,
                'results': results
            })
            
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/batch-results/<int:case_id>/<batch_id>")
@login_required
@admin_required
def batch_results(case_id, batch_id):
    """Unified timeline of all batch detections"""
    case = Case.query.get_or_404(case_id)
    
    # Get all detections from batch, sorted by confidence
    detections = PersonDetection.query.join(LocationMatch).filter(
        LocationMatch.case_id == case_id,
        PersonDetection.batch_id == batch_id
    ).order_by(PersonDetection.confidence_score.desc()).all()
    
    stats = {
        'total': len(detections),
        'high_confidence': len([d for d in detections if d.confidence_score > 0.88]),
        'frontal_only': len([d for d in detections if d.is_frontal_face])
    }
    
    return render_template(
        'admin/batch_results.html',
        case=case,
        batch_id=batch_id,
        detections=detections,
        stats=stats
    )
