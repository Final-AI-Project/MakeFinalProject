"""
Health Check Router
서버 상태 확인 API
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """서버 상태 확인"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Plant Whisperer API",
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """상세 서버 상태 확인"""
    import psutil
    import os
    
    # Get system information
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Plant Whisperer API",
        "version": "1.0.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            }
        },
        "process": {
            "pid": os.getpid(),
            "memory_usage": psutil.Process().memory_info().rss
        }
    }
