"""
Sistema de tareas programadas optimizado con manejo de errores y memoria
"""

import logging
import threading
import time
import schedule
from datetime import date, datetime
from typing import Optional
import gc
from utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Programador de tareas optimizado para el bot financiero"""
    
    def __init__(self, bot_manager):
        from core.bot_manager import BotManager
        self.bot_manager: BotManager = bot_manager
        self.bot = bot_manager.bot
        self.db = bot_manager.db
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        
        self._setup_scheduled_tasks()
    
    def _setup_scheduled_tasks(self):
        """Configura todas las tareas programadas"""
        try:
            # Verificar suscripciones cada hora
            schedule.every().hour.do(self._safe_run, self._verificar_suscripciones)
            
            # Verificar recordatorios cada hora
            schedule.every().hour.do(self._safe_run, self._verificar_recordatorios)
            
            # Backup diario a las 2 AM
            schedule.every().day.at("02:00").do(self._safe_run, self._realizar_backup)
            
            # Limpieza de datos antiguos semanal
            schedule.every().sunday.at("03:00").do(self._safe_run, self._limpiar_datos_antiguos)
            
            # Resumen mensual el día 1 a las 8 AM
            schedule.every().day.at("08:00").do(self._safe_run, self._generar_resumen_mensual)
            
            # Limpieza de memoria cada 4 horas
            schedule.every(4).hours.do(self._safe_run, self._limpiar_memoria)
            
            # Limpieza de estados de usuario cada 2 horas
            schedule.every(2).hours.do(self._safe_run, self._limpiar_estados_usuario)
            
            logger.info("Tareas programadas configuradas")
            
        except Exception as e:
            logger.error(f"Error configurando tareas programadas: {e}")
    
    def start(self):
        """Inicia el programador en un hilo separado"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler ya está ejecutándose")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler iniciado")
    
    def stop(self):
        """Detiene el programador"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Scheduler detenido")
    
    def _run_scheduler(self):
        """Ejecuta el programador en un loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logger.error(f"Error en scheduler: {e}")
                time.sleep(60)  # Continuar después de error
    
    def _safe_run(self, task_func):
        """Ejecuta una tarea de forma segura con manejo de errores"""
        try:
            task_func()
            # Limpieza ligera después de cada tarea
            gc.collect()
        except Exception as e:
            logger.error(f"Error ejecutando tarea {task_func.__name__}: {e}")
            ErrorHandler.log_database_error(task_func.__name__, e)
    
    def _verificar_suscripciones(self):
        """Verifica y procesa suscripciones pendientes"""
        try:
            suscripciones_pendientes = self.db.obtener_suscripciones_pendientes()
            
            if not suscripciones_pendientes:
                return
            
            logger.info(f"Procesando {len(suscripciones_pendientes)} suscripciones pendientes")
            
            for suscripcion in suscripciones_pendientes:
                suscripcion_id = suscripcion[0]
                
                # Procesar suscripción
                resultado = self.db.procesar_suscripcion(suscripcion_id)
                
                if resultado:
                    # Notificar al usuario
                    self._notificar_suscripcion_procesada(resultado)
                    logger.info(f"Suscripción procesada: {resultado['nombre']} - ${resultado['monto']}")
                else:
                    logger.error(f"Error procesando suscripción {suscripcion_id}")
            
        except Exception as e:
            logger.error(f"Error verificando suscripciones: {e}")
    
    def _verificar_recordatorios(self):
        """Verifica y envía recordatorios pendientes"""
        try:
            recordatorios_pendientes = self.db.obtener_recordatorios_pendientes()
            
            if not recordatorios_pendientes:
                return
            
            logger.info(f"Procesando {len(recordatorios_pendientes)} recordatorios pendientes")
            
            for recordatorio in recordatorios_pendientes:
                # Enviar recordatorio
                self._enviar_recordatorio(recordatorio)
                
                # Marcar como procesado
                self.db.marcar_recordatorio_procesado(recordatorio['id'])
                
        except Exception as e:
            logger.error(f"Error verificando recordatorios: {e}")
    
    def _realizar_backup(self):
        """Realiza backup de los datos"""
        try:
            if not self.bot_manager.config.BACKUP_ENABLED:
                return
            
            import csv
            import tempfile
            import os
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
                backup_path = f.name
                
                # Obtener datos de movimientos
                with self.db.pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT fecha, tipo, categoria, monto, descripcion, mes, año
                        FROM movimientos 
                        WHERE user_id = ?
                        ORDER BY fecha DESC
                    ''', (self.bot_manager.config.AUTHORIZED_USER_ID,))
                    
                    rows = cursor.fetchall()
                    
                    if rows:
                        writer = csv.writer(f)
                        # Escribir cabeceras
                        writer.writerow(['Fecha', 'Tipo', 'Categoria', 'Monto', 'Descripcion', 'Mes', 'Año'])
                        # Escribir datos
                        for row in rows:
                            writer.writerow(row)
            
            # Enviar archivo al usuario si hay datos
            if rows:
                try:
                    with open(backup_path, 'rb') as f:
                        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
                        filename = f"backup_finanzas_{fecha_str}.csv"
                        
                        self.bot.send_document(
                            self.bot_manager.config.AUTHORIZED_USER_ID,
                            f,
                            caption=f"📄 Backup automático - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                            visible_file_name=filename
                        )
                        
                    logger.info(f"Backup enviado: {len(rows)} registros")
                    
                except Exception as e:
                    logger.error(f"Error enviando backup: {e}")
                    
            else:
                self.bot.send_message(
                    self.bot_manager.config.AUTHORIZED_USER_ID,
                    "📄 No hay movimientos para respaldar todavía."
                )
            
            # Limpiar archivo temporal
            try:
                os.unlink(backup_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error realizando backup: {e}")
    
    def _limpiar_datos_antiguos(self):
        """Limpia datos antiguos de la base de datos"""
        try:
            dias_retencion = self.bot_manager.config.BACKUP_RETENTION_DAYS * 7  # Semanal
            
            if self.db.limpiar_datos_antiguos(dias_retencion):
                logger.info("Limpieza de datos antiguos completada")
            else:
                logger.warning("Error en limpieza de datos antiguos")
                
        except Exception as e:
            logger.error(f"Error limpiando datos antiguos: {e}")
    
    def _generar_resumen_mensual(self):
        """Genera y envía resumen mensual automático"""
        try:
            hoy = date.today()
            
            # Solo ejecutar el día 1 del mes
            if hoy.day != 1:
                return
            
            user_id = self.bot_manager.config.AUTHORIZED_USER_ID
            
            # Calcular mes anterior
            mes_anterior = hoy.month - 1 if hoy.month > 1 else 12
            año = hoy.year if hoy.month > 1 else hoy.year - 1
            
            # Obtener resumen
            resumen = self.db.obtener_resumen_mes(user_id, mes_anterior, año)
            
            # Formatear mensaje
            from utils.message_formatter import MessageFormatter
            formatter = MessageFormatter()
            
            mensaje = (
                f"📊 **Resumen Mensual {mes_anterior:02d}/{año}**\n\n"
                f"📈 **Movimientos:**\n"
                f"   💵 Ingresos: ${resumen['ingresos']:,.2f}\n"
                f"   💸 Gastos: ${resumen['gastos']:,.2f}\n"
                f"   💳 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
                f"💰 **Balance final: ${resumen['balance']:,.2f}**\n"
                f"💡 Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}\n\n"
                f"¡Nuevo mes, nuevas oportunidades! 💪"
            )
            
            self.bot.send_message(user_id, mensaje, parse_mode="Markdown")
            logger.info(f"Resumen mensual enviado para {mes_anterior}/{año}")
            
        except Exception as e:
            logger.error(f"Error generando resumen mensual: {e}")
    
    def _limpiar_memoria(self):
        """Limpia memoria del sistema"""
        try:
            # Usar el memory manager si está disponible
            if hasattr(self.bot_manager, 'memory_manager'):
                self.bot_manager.memory_manager.periodic_cleanup()
            else:
                # Limpieza básica
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"Limpieza programada: {collected} objetos recolectados")
                    
        except Exception as e:
            logger.error(f"Error en limpieza de memoria programada: {e}")
    
    def _limpiar_estados_usuario(self):
        """Limpia estados antiguos de usuarios"""
        try:
            self.bot_manager.cleanup_old_states()
            logger.debug("Limpieza de estados de usuario completada")
        except Exception as e:
            logger.error(f"Error limpiando estados de usuario: {e}")
    
    def _notificar_suscripcion_procesada(self, resultado):
        """Notifica al usuario sobre una suscripción procesada"""
        try:
            mensaje = (
                f"📄 **Suscripción Cobrada**\n\n"
                f"💳 {resultado['nombre']}\n"
                f"💰 ${resultado['monto']:,.2f}\n"
                f"🏷️ Categoría: {resultado['categoria']}\n\n"
                f"Se ha descontado automáticamente de tu balance."
            )
            
            self.bot.send_message(
                resultado['user_id'], 
                mensaje, 
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error enviando notificación de suscripción: {e}")
    
    def _enviar_recordatorio(self, recordatorio):
        """Envía un recordatorio al usuario"""
        try:
            mensaje = f"🔔 **Recordatorio**\n\n{recordatorio['descripcion']}"
            
            if recordatorio.get('monto'):
                mensaje += f"\n💰 Monto estimado: ${recordatorio['monto']:,.2f}"
            
            self.bot.send_message(
                recordatorio['user_id'], 
                mensaje, 
                parse_mode="Markdown"
            )
            
            logger.info(f"Recordatorio enviado: {recordatorio['descripcion']}")
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio: {e}")