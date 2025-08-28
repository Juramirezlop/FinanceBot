"""
Monitor de salud del sistema para prevenir crashes y optimizar rendimiento
"""

import logging
import threading
import time
import psutil
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthChecker:
    """Monitor de salud del sistema"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.start_time = datetime.now()
        self.health_stats = {
            'uptime': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'last_check': None,
            'alerts_sent': 0,
            'restarts_suggested': 0
        }
        
        # Thresholds para alertas
        self.memory_warning_threshold = 75  # %
        self.memory_critical_threshold = 90  # %
        self.cpu_warning_threshold = 80  # %
        self.uptime_restart_suggestion = 24 * 60 * 60  # 24 horas
        
    def start_monitoring(self):
        """Inicia el monitoreo de salud"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitor de salud iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitor de salud detenido")
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring:
            try:
                self._check_system_health()
                time.sleep(300)  # Verificar cada 5 minutos
            except Exception as e:
                logger.error(f"Error en monitor de salud: {e}")
                time.sleep(60)  # Retry en 1 minuto
    
    def _check_system_health(self):
        """Verifica la salud del sistema"""
        try:
            # Actualizar estadísticas
            process = psutil.Process(os.getpid())
            
            self.health_stats.update({
                'uptime': (datetime.now() - self.start_time).total_seconds(),
                'memory_usage': process.memory_percent(),
                'cpu_usage': process.cpu_percent(interval=1),
                'last_check': datetime.now()
            })
            
            # Verificar thresholds y generar alertas
            self._check_memory_usage()
            self._check_cpu_usage()
            self._check_uptime()
            
            # Log estadísticas cada hora
            if int(time.time()) % 3600 == 0:
                self._log_health_stats()
                
        except Exception as e:
            logger.error(f"Error verificando salud del sistema: {e}")
    
    def _check_memory_usage(self):
        """Verifica el uso de memoria"""
        memory_percent = self.health_stats['memory_usage']
        
        if memory_percent > self.memory_critical_threshold:
            logger.critical(f"Memoria crítica: {memory_percent:.1f}%")
            self.health_stats['alerts_sent'] += 1
            
            # Forzar limpieza de memoria
            import gc
            collected = gc.collect()
            logger.info(f"Limpieza forzada: {collected} objetos recolectados")
            
        elif memory_percent > self.memory_warning_threshold:
            logger.warning(f"Memoria alta: {memory_percent:.1f}%")
    
    def _check_cpu_usage(self):
        """Verifica el uso de CPU"""
        cpu_percent = self.health_stats['cpu_usage']
        
        if cpu_percent > self.cpu_warning_threshold:
            logger.warning(f"CPU alta: {cpu_percent:.1f}%")
    
    def _check_uptime(self):
        """Verifica el tiempo de actividad"""
        uptime = self.health_stats['uptime']
        
        if uptime > self.uptime_restart_suggestion:
            logger.info(f"Bot ejecutándose por {uptime/3600:.1f} horas - considerar reinicio")
            self.health_stats['restarts_suggested'] += 1
    
    def _log_health_stats(self):
        """Registra estadísticas de salud"""
        stats = self.health_stats
        logger.info(
            f"Salud del sistema - "
            f"Uptime: {stats['uptime']/3600:.1f}h, "
            f"Memoria: {stats['memory_usage']:.1f}%, "
            f"CPU: {stats['cpu_usage']:.1f}%, "
            f"Alertas: {stats['alerts_sent']}"
        )
    
    def get_health_report(self) -> Dict[str, Any]:
        """Obtiene reporte completo de salud"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'status': self._get_overall_status(),
                'uptime_hours': self.health_stats['uptime'] / 3600,
                'memory': {
                    'percent': self.health_stats['memory_usage'],
                    'rss_mb': memory_info.rss / 1024 / 1024,
                    'vms_mb': memory_info.vms / 1024 / 1024
                },
                'cpu_percent': self.health_stats['cpu_usage'],
                'alerts_sent': self.health_stats['alerts_sent'],
                'last_check': self.health_stats['last_check'],
                'monitoring': self.monitoring
            }
        except Exception as e:
            logger.error(f"Error generando reporte de salud: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_overall_status(self) -> str:
        """Determina el estado general del sistema"""
        memory = self.health_stats['memory_usage']
        cpu = self.health_stats['cpu_usage']
        
        if memory > self.memory_critical_threshold or cpu > 95:
            return 'critical'
        elif memory > self.memory_warning_threshold or cpu > self.cpu_warning_threshold:
            return 'warning'
        else:
            return 'healthy'
    
    def force_health_check(self) -> Dict[str, Any]:
        """Fuerza una verificación de salud inmediata"""
        self._check_system_health()
        return self.get_health_report()