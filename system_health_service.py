"""
Unified System Health Service - Single Source of Truth
Consolidates: system_monitor.py, system_resilience_monitor.py
"""
import os
import psutil
import time
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_connections: int
    response_time: float
    error_count: int
    gpu_available: bool
    overall_status: str

class SystemHealthService:
    def __init__(self):
        self.monitoring_active = False
        self.metrics_history = []
        
        self.alert_thresholds = {
            'cpu_critical': 90.0,
            'cpu_warning': 75.0,
            'memory_critical': 85.0,
            'memory_warning': 70.0,
            'disk_critical': 90.0,
            'disk_warning': 80.0
        }
        
        self.auto_recovery_enabled = True
        self.gpu_available = False
        self.cpu_fallback_active = True
        
        self.db_path = Path('instance/system_monitor.db')
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger('SystemHealth')
    
    def _init_database(self):
        """Initialize database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        gpu_available BOOLEAN,
                        active_connections INTEGER,
                        response_time REAL,
                        error_count INTEGER,
                        overall_status TEXT
                    )
                """)
                conn.commit()
                logger.info("System health database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            try:
                connections = len(psutil.net_connections())
            except:
                connections = 0
            
            # Check GPU
            gpu_available = False
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_available = True
            except:
                pass
            
            # Determine status
            if cpu_percent >= 90 or memory.percent >= 85:
                status = 'critical'
            elif cpu_percent >= 75 or memory.percent >= 70:
                status = 'warning'
            else:
                status = 'healthy'
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage=disk.percent,
                active_connections=connections,
                response_time=0.0,
                error_count=0,
                gpu_available=gpu_available,
                overall_status=status
            )
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None
    
    def analyze_metrics(self, metrics: SystemMetrics) -> Dict:
        """Analyze metrics and determine actions"""
        analysis = {
            'status': metrics.overall_status,
            'alerts': [],
            'auto_actions': []
        }
        
        if metrics.cpu_percent >= self.alert_thresholds['cpu_critical']:
            analysis['alerts'].append(f"Critical CPU: {metrics.cpu_percent:.1f}%")
            analysis['auto_actions'].append('optimize_cpu')
        elif metrics.cpu_percent >= self.alert_thresholds['cpu_warning']:
            analysis['alerts'].append(f"High CPU: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent >= self.alert_thresholds['memory_critical']:
            analysis['alerts'].append(f"Critical Memory: {metrics.memory_percent:.1f}%")
            analysis['auto_actions'].append('clear_cache')
        elif metrics.memory_percent >= self.alert_thresholds['memory_warning']:
            analysis['alerts'].append(f"High Memory: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_usage >= self.alert_thresholds['disk_critical']:
            analysis['alerts'].append(f"Critical Disk: {metrics.disk_usage:.1f}%")
            analysis['auto_actions'].append('cleanup_files')
        
        return analysis
    
    def execute_auto_recovery(self, actions: List[str]):
        """Execute automatic recovery actions"""
        if not self.auto_recovery_enabled:
            return
        
        for action in actions:
            try:
                if action == 'clear_cache':
                    self._clear_cache()
                elif action == 'cleanup_files':
                    self._cleanup_files()
                elif action == 'optimize_cpu':
                    self._optimize_cpu()
                
                logger.info(f"Executed recovery action: {action}")
            except Exception as e:
                logger.error(f"Failed to execute {action}: {e}")
    
    def _clear_cache(self):
        """Clear system cache"""
        temp_dirs = ['static/temp', 'static/cache']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
    
    def _cleanup_files(self):
        """Cleanup old temporary files"""
        cleanup_dirs = ['static/temp', 'static/cache', 'logs']
        total_freed = 0
        
        for directory in cleanup_dirs:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    try:
                        if os.path.isfile(file_path):
                            if time.time() - os.path.getmtime(file_path) > 86400:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                total_freed += size
                    except:
                        pass
        
        logger.info(f"Cleaned up {total_freed / (1024*1024):.1f} MB")
    
    def _optimize_cpu(self):
        """Optimize CPU usage"""
        try:
            current_process = psutil.Process()
            current_process.nice(10)
            logger.info("CPU optimization applied")
        except:
            pass
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("System health monitoring started")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    metrics = self.collect_metrics()
                    if metrics:
                        self.metrics_history.append(metrics)
                        
                        # Keep last 24 hours
                        cutoff_time = datetime.now() - timedelta(hours=24)
                        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
                        
                        # Analyze
                        analysis = self.analyze_metrics(metrics)
                        
                        if analysis['status'] != 'healthy':
                            for alert in analysis['alerts']:
                                logger.warning(f"Alert: {alert}")
                        
                        if analysis['auto_actions']:
                            self.execute_auto_recovery(analysis['auto_actions'])
                        
                        self._save_metrics(metrics, analysis)
                
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("System health monitoring stopped")
    
    def _save_metrics(self, metrics: SystemMetrics, analysis: Dict):
        """Save metrics to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_health (
                        timestamp, cpu_usage, memory_usage, disk_usage,
                        gpu_available, active_connections, response_time,
                        error_count, overall_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_usage,
                    metrics.gpu_available,
                    metrics.active_connections,
                    metrics.response_time,
                    metrics.error_count,
                    analysis['status']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def get_system_health(self) -> Dict:
        """Get current system health status"""
        if not self.metrics_history:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        latest_metrics = self.metrics_history[-1]
        analysis = self.analyze_metrics(latest_metrics)
        
        return {
            'status': analysis['status'],
            'timestamp': latest_metrics.timestamp.isoformat(),
            'metrics': {
                'cpu_percent': latest_metrics.cpu_percent,
                'memory_percent': latest_metrics.memory_percent,
                'disk_usage': latest_metrics.disk_usage,
                'active_connections': latest_metrics.active_connections,
                'gpu_available': latest_metrics.gpu_available
            },
            'alerts': analysis['alerts']
        }
    
    def get_system_status(self) -> Dict:
        """Get system status (alias for compatibility)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM system_health ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    return {
                        'status': row['overall_status'],
                        'cpu_usage': row['cpu_usage'],
                        'memory_usage': row['memory_usage'],
                        'gpu_available': row['gpu_available'],
                        'cpu_fallback_active': not row['gpu_available']
                    }
        except:
            pass
        
        return {
            'status': 'healthy',
            'gpu_available': self.gpu_available,
            'cpu_fallback_active': self.cpu_fallback_active
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict:
        """Get performance trends over specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No data available'}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'trend': 'increasing' if len(cpu_values) > 1 and cpu_values[-1] > cpu_values[0] else 'stable'
            },
            'memory': {
                'current': memory_values[-1] if memory_values else 0,
                'average': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'trend': 'increasing' if len(memory_values) > 1 and memory_values[-1] > memory_values[0] else 'stable'
            }
        }

# Global instance
system_health = SystemHealthService()

def start_system_monitoring():
    """Start system monitoring"""
    system_health.start_monitoring(interval=30)

def get_system_status():
    """Get current system status"""
    return system_health.get_system_status()
