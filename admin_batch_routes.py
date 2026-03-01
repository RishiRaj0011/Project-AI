# Add to admin.py - Batch Analysis Routes

@admin_bp.route("/analyze-batch/<int:case_id>", methods=["POST"])
@login_required
@admin_required
def analyze_batch(case_id):
    """Batch analyze multiple footages for a case"""
    try:
        case = Case.query.get_or_404(case_id)
        footage_ids = request.form.getlist('footage_ids[]')
        
        if not footage_ids:
            return jsonify({'success': False, 'error': 'No footage selected'})
        
        footage_ids = [int(fid) for fid in footage_ids]
        
        # Create batch analysis record
        batch_id = f"batch_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Trigger parallel analysis
        try:
            from tasks import analyze_footage_batch
            result = analyze_footage_batch.delay(case_id, footage_ids, batch_id)
            
            return jsonify({
                'success': True,
                'batch_id': batch_id,
                'task_id': result.id,
                'footage_count': len(footage_ids),
                'message': f'Batch analysis started for {len(footage_ids)} footages'
            })
        except ImportError:
            # Fallback: synchronous processing
            from batch_analyzer import process_batch_sync
            results = process_batch_sync(case_id, footage_ids, batch_id)
            
            return jsonify({
                'success': True,
                'batch_id': batch_id,
                'results': results,
                'message': 'Batch analysis completed'
            })
            
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/batch-results/<int:case_id>/<batch_id>")
@login_required
@admin_required
def batch_results(case_id, batch_id):
    """View consolidated batch analysis results"""
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get all detections from this batch
        detections = PersonDetection.query.join(LocationMatch).filter(
            LocationMatch.case_id == case_id,
            PersonDetection.batch_id == batch_id
        ).order_by(PersonDetection.confidence_score.desc()).all()
        
        # Group by footage
        footage_groups = {}
        for detection in detections:
            footage_id = detection.location_match.footage_id
            if footage_id not in footage_groups:
                footage_groups[footage_id] = {
                    'footage': detection.location_match.footage,
                    'detections': []
                }
            footage_groups[footage_id]['detections'].append(detection)
        
        # Calculate statistics
        stats = {
            'total_detections': len(detections),
            'high_confidence': len([d for d in detections if d.confidence_score > 0.85]),
            'footages_analyzed': len(footage_groups),
            'frontal_faces': len([d for d in detections if d.is_frontal_face])
        }
        
        return render_template(
            'admin/batch_results.html',
            case=case,
            batch_id=batch_id,
            footage_groups=footage_groups,
            detections=detections,
            stats=stats
        )
        
    except Exception as e:
        flash(f'Error loading batch results: {str(e)}', 'error')
        return redirect(url_for('admin.case_detail', case_id=case_id))
