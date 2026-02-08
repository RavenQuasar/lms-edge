from fastapi import APIRouter, Depends
import psutil
import time
import os
from app.core.security import RoleChecker
from app.models.user import UserRole
from app.schemas.stats import SystemInfo
from typing import List
from datetime import datetime
import logging

router = APIRouter()

admin_checker = RoleChecker([UserRole.ADMIN])

logger = logging.getLogger(__name__)


def get_cpu_temperature():
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    return entries[0].current
    except Exception as e:
        logger.warning(f"Could not get CPU temperature: {e}")
    return None


@router.get("/info", response_model=SystemInfo)
async def get_system_info(token: str = Depends(admin_checker)):
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_total = memory.total / (1024 ** 3)
    
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_total = disk.total / (1024 ** 3)
    
    temperature = get_cpu_temperature()
    
    uptime_seconds = time.time() - psutil.boot_time()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime = f"{hours}h {minutes}m"
    
    return SystemInfo(
        cpu_usage=cpu_percent,
        cpu_count=cpu_count,
        memory_usage=memory_percent,
        memory_total=memory_total,
        disk_usage=disk_percent,
        disk_total=disk_total,
        temperature=temperature,
        uptime=uptime
    )


@router.get("/logs")
async def get_logs(limit: int = 100, token: str = Depends(admin_checker)):
    log_file = "logs/lms.log"
    logs = []
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    logs.append(line.strip())
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
    
    return {"logs": logs}


@router.get("/processes")
async def get_processes(token: str = Depends(admin_checker)):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            proc_info = proc.info
            if proc_info['cpu_percent'] is not None:
                processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'cpu_percent': proc_info['cpu_percent'],
                    'memory_percent': proc_info['memory_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return {"processes": processes[:20]}
