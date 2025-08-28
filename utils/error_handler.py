"""
Sistema de manejo de errores optimizado para el bot
"""

import logging
import functools
import traceback
from typing import Callable, Any
import gc

logger = logging.getLogger(__name__)

def handle_errors(func: Callable) -> Callable:
    """Decorador para manejar errores de forma consistente"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log detallado del error
            logger.error(f"Error en {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Limpiar memoria en caso de error
            gc.collect()
            
            # Si es un método de handler, intentar enviar mensaje de error
            if hasattr(args[0], 'bot') and len(args) > 1:
                try:
                    handler_self = args[0]
                    message_or_call = args[1]
                    
                    if hasattr(message_or_call, 'message'):  # Es callback
                        handler_self.bot.edit_message_text(
                            "❌ Error procesando la solicitud. Intenta de nuevo.",
                            message_or_call.message.chat.id,
                            message_or_call.message.message_id
                        )
                    elif hasattr(message_or_call, 'chat'):  # Es message
                        handler_self.bot.reply_to(
                            message_or_call,
                            "❌ Error procesando la solicitud. Intenta de nuevo."
                        )
                except Exception as reply_error:
                    logger.error(f"Error enviando mensaje de error: {reply_error}")
            
            # Re-raise para debugging en desarrollo
            # En producción, podrías comentar esta línea
            raise
    
    return wrapper

class ErrorHandler:
    """Clase para manejo centralizado de errores"""
    
    @staticmethod
    def log_database_error(operation: str, error: Exception):
        """Log específico para errores de base de datos"""
        logger.error(f"Database error in {operation}: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def log_telegram_error(operation: str, error: Exception):
        """Log específico para errores de Telegram API"""
        logger.error(f"Telegram API error in {operation}: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def log_validation_error(field: str, value: Any, error: str):
        """Log específico para errores de validación"""
        logger.warning(f"Validation error for {field} with value '{value}': {error}")
    
    @staticmethod
    def handle_memory_error():
        """Manejo específico para errores de memoria"""
        logger.critical("Memory error detected, attempting cleanup")
        gc.collect()
        # Aquí podrías agregar más lógica de limpieza si es necesaria