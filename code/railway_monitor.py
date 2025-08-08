"""
Railway Performance Monitoring Utility
Monitors memory, CPU, and connection metrics for Railway deployment
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - detailed system monitoring disabled")


class RailwayMonitor:
    """
    Performance monitoring utility optimized for Railway deployment constraints.
    Tracks memory usage, CPU load, connection counts, and provides alerts.
    """
    
    def __init__(
        self,
        memory_limit_mb: int = 512,
        memory_warning_threshold: float = 0.8,
        cpu_warning_threshold: float = 0.9,
        monitoring_interval: int = 30
    ):
        self.memory_limit_mb = memory_limit_mb
        self.memory_warning_threshold = memory_warning_threshold
        self.cpu_warning_threshold = cpu_warning_threshold
        self.monitoring_interval = monitoring_interval
        
        # State tracking
        self.start_time = time.time()
        self.connections_count = 0
        self.total_transcriptions = 0
        self.last_gc_time = time.time()
        
        # Metrics history (keep lightweight for memory)
        self.metrics_history = []
        self.max_history_size = 100 if os.getenv("RAILWAY_DEPLOYMENT") else 500
        
        # Alerts state
        self.memory_alert_active = False
        self.cpu_alert_active = False
        
        logger.info(f"🔍 Railway Monitor initialized (limits: {memory_limit_mb}MB memory)")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "connections": self.connections_count,
            "transcriptions": self.total_transcriptions,
            "railway_deployment": os.getenv("RAILWAY_DEPLOYMENT", "false") == "true"
        }
        
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                
                metrics.update({
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "memory_percent": (memory_info.rss / 1024 / 1024) / self.memory_limit_mb,
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads(),
                    "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
                })
                
                # System-wide metrics (if available)
                try:
                    system_memory = psutil.virtual_memory()
                    metrics.update({
                        "system_memory_percent": system_memory.percent,
                        "system_cpu_percent": psutil.cpu_percent(interval=0.1)
                    })
                except:
                    pass
                    
            except Exception as e:
                logger.debug(f"Error collecting psutil metrics: {e}")
                metrics.update({
                    "memory_mb": 0,
                    "memory_percent": 0,
                    "cpu_percent": 0
                })
        else:
            # Fallback metrics without psutil
            metrics.update({
                "memory_mb": 0,
                "memory_percent": 0,
                "cpu_percent": 0,
                "threads": 0
            })
        
        return metrics
    
    def check_alerts(self, metrics: Dict[str, Any]) -> None:
        """Check for alert conditions and log warnings."""
        memory_percent = metrics.get("memory_percent", 0)
        cpu_percent = metrics.get("cpu_percent", 0)
        
        # Memory alerts
        if memory_percent > self.memory_warning_threshold:
            if not self.memory_alert_active:
                logger.warning(
                    f"🚨 HIGH MEMORY USAGE: {memory_percent:.1%} "
                    f"({metrics['memory_mb']:.1f}MB/{self.memory_limit_mb}MB)"
                )
                self.memory_alert_active = True
                self._suggest_memory_optimizations(metrics)
        else:
            if self.memory_alert_active:
                logger.info(f"✅ Memory usage normalized: {memory_percent:.1%}")
                self.memory_alert_active = False
        
        # CPU alerts  
        if cpu_percent > self.cpu_warning_threshold * 100:  # psutil returns 0-100
            if not self.cpu_alert_active:
                logger.warning(f"🚨 HIGH CPU USAGE: {cpu_percent:.1f}%")
                self.cpu_alert_active = True
        else:
            if self.cpu_alert_active:
                logger.info(f"✅ CPU usage normalized: {cpu_percent:.1f}%")
                self.cpu_alert_active = False
    
    def _suggest_memory_optimizations(self, metrics: Dict[str, Any]) -> None:
        """Suggest optimizations based on current metrics."""
        suggestions = []
        
        if metrics.get("connections", 0) > 5:
            suggestions.append("Consider limiting concurrent connections")
        
        if len(self.metrics_history) > 50:
            suggestions.append("Metrics history getting large - consider reducing retention")
        
        if metrics.get("threads", 0) > 10:
            suggestions.append("High thread count detected - check for resource leaks")
        
        if suggestions:
            logger.info("💡 Memory optimization suggestions:")
            for suggestion in suggestions:
                logger.info(f"   • {suggestion}")
    
    def add_connection(self) -> None:
        """Track new connection."""
        self.connections_count += 1
        logger.debug(f"🔗 Connection added. Total: {self.connections_count}")
    
    def remove_connection(self) -> None:
        """Track connection removal."""
        self.connections_count = max(0, self.connections_count - 1)
        logger.debug(f"🔗 Connection removed. Total: {self.connections_count}")
    
    def add_transcription(self) -> None:
        """Track completed transcription."""
        self.total_transcriptions += 1
    
    def log_metrics(self, context: str = "") -> Dict[str, Any]:
        """Log current metrics with optional context."""
        metrics = self.get_current_metrics()
        self.check_alerts(metrics)
        
        # Add to history (with size management)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size//2:]  # Keep half
        
        # Format log message
        context_str = f" [{context}]" if context else ""
        log_parts = [
            f"🔍{context_str}",
            f"Memory: {metrics['memory_mb']:.1f}MB ({metrics['memory_percent']:.1%})",
            f"CPU: {metrics.get('cpu_percent', 0):.1f}%",
            f"Connections: {metrics['connections']}",
            f"Transcriptions: {metrics['transcriptions']}"
        ]
        
        if metrics['memory_percent'] > 0.7:  # High memory usage
            logger.warning(" | ".join(log_parts))
        else:
            logger.info(" | ".join(log_parts))
        
        return metrics
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics since startup."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        memory_values = [m['memory_mb'] for m in self.metrics_history if m['memory_mb'] > 0]
        cpu_values = [m['cpu_percent'] for m in self.metrics_history if m['cpu_percent'] > 0]
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_connections": self.connections_count,
            "total_transcriptions": self.total_transcriptions,
            "memory_stats": {
                "current_mb": memory_values[-1] if memory_values else 0,
                "peak_mb": max(memory_values) if memory_values else 0,
                "average_mb": sum(memory_values) / len(memory_values) if memory_values else 0,
                "limit_mb": self.memory_limit_mb
            },
            "cpu_stats": {
                "current_percent": cpu_values[-1] if cpu_values else 0,
                "peak_percent": max(cpu_values) if cpu_values else 0,
                "average_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0
            },
            "metrics_collected": len(self.metrics_history),
            "alerts_active": {
                "memory": self.memory_alert_active,
                "cpu": self.cpu_alert_active
            }
        }
    
    async def start_monitoring(self) -> None:
        """Start background monitoring loop."""
        logger.info(f"🔍 Starting Railway monitoring (interval: {self.monitoring_interval}s)")
        
        while True:
            try:
                self.log_metrics("monitor")
                
                # Periodic garbage collection hint for Railway
                if time.time() - self.last_gc_time > 300:  # Every 5 minutes
                    import gc
                    collected = gc.collect()
                    if collected > 0:
                        logger.debug(f"🗑️ Garbage collected {collected} objects")
                    self.last_gc_time = time.time()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("🔍 Monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"🔍 Monitoring error: {e}", exc_info=True)
                await asyncio.sleep(self.monitoring_interval)  # Continue monitoring


# Global monitor instance (initialized by server.py if on Railway)
railway_monitor: Optional[RailwayMonitor] = None

def init_railway_monitor() -> Optional[RailwayMonitor]:
    """Initialize global Railway monitor if on Railway."""
    global railway_monitor
    
    if os.getenv("RAILWAY_DEPLOYMENT", "false").lower() == "true":
        memory_limit = int(os.getenv("MEMORY_LIMIT", "512").rstrip("MB"))
        railway_monitor = RailwayMonitor(memory_limit_mb=memory_limit)
        logger.info("🔍 Railway monitoring initialized")
        return railway_monitor
    else:
        logger.debug("🔍 Not on Railway - monitoring disabled")
        return None

def get_monitor() -> Optional[RailwayMonitor]:
    """Get the global Railway monitor instance."""
    return railway_monitor