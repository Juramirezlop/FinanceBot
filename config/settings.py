"""
Configuración centralizada del bot
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

@dataclass
class BotConfig:
    """Configuración del bot de finanzas"""
    
    # Configuración del bot de Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    AUTHORIZED_USER_ID: int = int(os.getenv("AUTHORIZED_USER_ID", "0"))
    
    # Configuración de base de datos
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "finanzas.db")
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", "30"))
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "finance_bot.log")
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Configuración de memoria y rendimiento
    MAX_USER_STATES: int = int(os.getenv("MAX_USER_STATES", "100"))
    CLEANUP_INTERVAL: int = int(os.getenv("CLEANUP_INTERVAL", "3600"))  # 1 hora
    MAX_DB_CONNECTIONS: int = int(os.getenv("MAX_DB_CONNECTIONS", "5"))
    
    # Configuración del servidor Flask (para Render)
    FLASK_PORT: int = int(os.getenv("PORT", "5000"))
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    
    # Configuración de backups
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Valida la configuración"""
        if not self.BOT_TOKEN:
            return False, "BOT_TOKEN no configurado"
            
        if not self.AUTHORIZED_USER_ID:
            return False, "AUTHORIZED_USER_ID no configurado"
            
        if self.DATABASE_TIMEOUT <= 0:
            return False, "DATABASE_TIMEOUT debe ser mayor a 0"
            
        return True, None

def setup_logging():
    """Configura el sistema de logging con rotación"""
    from logging.handlers import RotatingFileHandler
    
    config = BotConfig()
    
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.MAX_LOG_SIZE,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger principal
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reducir logging de telebot
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telebot").setLevel(logging.WARNING)

# Constantes para el bot
class BotConstants:
    """Constantes utilizadas en el bot"""
    
    # Emojis
    MONEY = "💰"
    INCOME = "💵"
    EXPENSE = "💸"
    SAVINGS = "💳"
    CHART = "📊"
    CALENDAR = "📅"
    SETTINGS = "⚙️"
    HOME = "🏠"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "💡"
    BACK = "◀️"
    
    # Tipos de movimientos
    MOVEMENT_TYPES = ["ingreso", "gasto", "ahorro"]
    
    # Categorías predeterminadas
    DEFAULT_INCOME_CATEGORIES = [
        "Salario", "Freelance", "Negocio", "Inversiones", "Otros"
    ]
    
    DEFAULT_EXPENSE_CATEGORIES = [
        "Vivienda", "Comida", "Transporte", "Ropa", "Salud", 
        "Entretenimiento", "Educación", "Servicios"
    ]
    
    # Límites del sistema
    MAX_AMOUNT = 999999999.99
    MIN_AMOUNT = 0.01
    MAX_DESCRIPTION_LENGTH = 500
    MAX_CATEGORY_NAME_LENGTH = 50
    MAX_SUBSCRIPTION_NAME_LENGTH = 100
    
    # Mensajes de estado
    STATUS_MESSAGES = {
        "processing": "⏳ Procesando...",
        "success": "✅ Operación exitosa",
        "error": "❌ Error en la operación",
        "unauthorized": "🚫 No autorizado",
        "invalid_input": "❌ Entrada inválida",
        "not_found": "❌ No encontrado"
    }