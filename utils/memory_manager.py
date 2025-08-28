"""
Gestor de memoria para optimizar el rendimiento del bot
"""

import gc
import logging
import threading
import time
from typing import Dict, Any
import psutil
import os

logger = logging.getLogger(__name__)

class MemoryManager:
    """Gestor de memoria para mantener el bot optimizado"""
    
    def __init__(self):
        self.cleanup_interval = 3600  # 1 hora
        self.cleanup_thread = None
        self.running = False
        self.memory_threshold = 80  # Porcentaje de memoria antes de forzar limpieza
    
    def start_monitoring(self):
        """Inicia el monitoreo automático de memoria"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
            
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._memory_monitor, daemon=True)
        self.cleanup_thread.start()
        logger.info("Monitor de memoria iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo de memoria"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Monitor de memoria detenido")
    
    def _memory_monitor(self):
        """Hilo de monitoreo de memoria"""
        while self.running:
            try:
                # Verificar uso de memoria
                memory_percent = self.get_memory_usage()
                
                if memory_percent > self.memory_threshold:
                    logger.warning(f"Memoria alta detectada: {memory_percent:.1f}%")
                    self.force_cleanup()
                
                # Limpieza periódica ligera
                if int(time.time()) % self.cleanup_interval == 0:
                    self.periodic_cleanup()
                
                time.sleep(60)  # Verificar cada minuto
                
            except Exception as e:
                logger.error(f"Error en monitor de memoria: {e}")
                time.sleep(300)  # Esperar 5 minutos en caso de error
    
    def get_memory_usage(self) -> float:
        """Obtiene el porcentaje de uso de memoria del proceso"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_percent()
        except Exception as e:
            logger.error(f"Error obteniendo uso de memoria: {e}")
            return 0.0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Obtiene información detallada de memoria"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # MB
                'vms_mb': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error obteniendo información de memoria: {e}")
            return {}
    
    def periodic_cleanup(self):
        """Limpieza periódica ligera"""
        try:
            # Recolección de basura ligera
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"Limpieza periódica: {collected} objetos recolectados")
        except Exception as e:
            logger.error(f"Error en limpieza periódica: {e}")
    
    def force_cleanup(self):
        """Limpieza forzada más agresiva"""
        try:
            logger.info("Iniciando limpieza forzada de memoria")
            
            # Recolección de basura completa
            gc.disable()
            collected = 0
            for generation in range(3):
                collected += gc.collect(generation)
            gc.enable()
            
            # Log de resultados
            memory_info = self.get_memory_info()
            logger.info(f"Limpieza completada: {collected} objetos recolectados, "
                       f"memoria: {memory_info.get('percent', 0):.1f}%")
            
        except Exception as e:
            logger.error(f"Error en limpieza forzada: {e}")
    
    def cleanup_all(self):
        """Limpieza completa al cerrar el bot"""
        try:
            logger.info("Limpieza completa de memoria")
            
            # Recolección completa
            for _ in range(3):
                gc.collect()
            
            # Desfragmentar si es posible
            try:
                gc.set_debug(0)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error en limpieza completa: {e}")
    
    def optimize_collections(self):
        """Optimiza los parámetros del recolector de basura"""
        try:
            # Configurar thresholds más agresivos para entornos con poca memoria
            gc.set_threshold(700, 10, 10)  # Valores más conservadores
            logger.debug("Thresholds de GC optimizados")
        except Exception as e:
            logger.error(f"Error optimizando recolector: {e}")
    
    def log_memory_stats(self):
        """Log estadísticas de memoria para debugging"""
        try:
            memory_info = self.get_memory_info()
            gc_stats = gc.get_stats()
            
            logger.info(f"Memoria - RSS: {memory_info.get('rss_mb', 0):.1f}MB, "
                       f"Uso: {memory_info.get('percent', 0):.1f}%, "
                       f"Disponible: {memory_info.get('available_mb', 0):.1f}MB")
            
            logger.debug(f"GC Stats: {gc_stats}")
            
        except Exception as e:
            logger.error(f"Error en log de estadísticas: {e}")

class ObjectTracker:
    """Rastreador de objetos para detectar memory leaks"""
    
    def __init__(self):
        self.tracked_objects = {}
        self.enabled = False
    
    def enable_tracking(self):
        """Habilita el rastreo de objetos (solo para debugging)"""
        self.enabled = True
        logger.debug("Rastreo de objetos habilitado")
    
    def track_object(self, obj_name: str, obj):
        """Rastrea un objeto específico"""
        if not self.enabled:
            return
            
        obj_id = id(obj)
        self.tracked_objects[obj_id] = {
            'name': obj_name,
            'type': type(obj).__name__,
            'size': len(str(obj)) if hasattr(obj, '__len__') else 0,
            'timestamp': time.time()
        }
    
    def untrack_object(self, obj):
        """Deja de rastrear un objeto"""
        if not self.enabled:
            return
            
        obj_id = id(obj)
        self.tracked_objects.pop(obj_id, None)
    
    def get_tracked_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de objetos rastreados"""
        if not self.enabled:
            return {}
            
        stats = {}
        for obj_info in self.tracked_objects.values():
            obj_type = obj_info['type']
            stats[obj_type] = stats.get(obj_type, 0) + 1
            
        return stats
    
    def cleanup_old_references(self, max_age: int = 3600):
        """Limpia referencias de objetos antiguos"""
        if not self.enabled:
            return
            
        current_time = time.time()
        to_remove = []
        
        for obj_id, obj_info in self.tracked_objects.items():
            if current_time - obj_info['timestamp'] > max_age:
                to_remove.append(obj_id)
        
        for obj_id in to_remove:
            del self.tracked_objects[obj_id]
            
        if to_remove:
            logger.debug(f"Limpiadas {len(to_remove)} referencias antiguas")