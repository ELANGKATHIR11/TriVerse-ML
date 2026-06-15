"""System monitoring utility for tracking CPU, memory, and resource utilization."""
import psutil
from datetime import datetime, UTC

class SystemMonitor:
    """Monitors system-level resource utilization."""
    
    def get_stats(self) -> dict:
        """Get current CPU, RAM, and timestamp stats.
        
        Returns:
            dict: Containing cpu_percent, ram_percent, ram_total_gb, and timestamp.
        """
        mem = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": mem.percent,
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
