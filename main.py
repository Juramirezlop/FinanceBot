#!/usr/bin/env python3
"""
Bot de Telegram para Economía Personal - Versión Refactorizada
Autor: Juan David Ramirez
Versión: 2.0
Descripción: Bot optimizado con arquitectura modular y mejor manejo de recursos
"""

import os
import sys
import logging
from typing import Optional

# Añadir el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import BotConfig, setup_logging
from core.bot_manager import BotManager
from utils.memory_manager import MemoryManager
from utils.health_check import HealthChecker

logger = logging.getLogger(__name__)

class FinanceBot:
    """Clase principal del bot financiero"""
    
    def __init__(self):
        self.config = BotConfig()
        self.bot_manager: Optional[BotManager] = None
        self.memory_manager = MemoryManager()
        self.health_checker = HealthChecker()
        
    def validate_config(self) -> bool:
        """Valida la configuración del bot"""
        if not self.config.BOT_TOKEN:
            logger.error("BOT_TOKEN no configurado")
            print("❌ Error: Configura tu BOT_TOKEN en las variables de entorno")
            return False
            
        if not self.config.AUTHORIZED_USER_ID:
            logger.error("AUTHORIZED_USER_ID no configurado") 
            print("❌ Error: Configura tu AUTHORIZED_USER_ID en las variables de entorno")
            print("💡 Para obtener tu USER_ID, envía un mensaje a @userinfobot")
            return False
            
        return True
    
    def initialize(self) -> bool:
        """Inicializa todos los componentes del bot"""
        try:
            # Configurar logging
            setup_logging()
            
            # Validar configuración
            if not self.validate_config():
                return False
            
            # Inicializar gestor del bot
            self.bot_manager = BotManager(self.config)

            if not self.bot_manager.initialize_bot():
                logger.error("Error inicializando bot de Telegram")
                return False
            
            # Inicializar base de datos
            if not self.bot_manager.initialize_database():
                logger.error("Error inicializando base de datos")
                return False
            
            # Registrar handlers
            self.bot_manager.register_handlers()
            
            # Iniciar tareas programadas
            self.bot_manager.start_scheduler()
            
            # Iniciar monitor de salud
            self.health_checker.start_monitoring()
            
            logger.info("🤖 Bot inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando bot: {e}")
            return False
    
    def run(self):
        """Ejecuta el bot principal"""
        if not self.config.BOT_TOKEN or not self.config.AUTHORIZED_USER_ID:
            print("Error: BOT_TOKEN y AUTHORIZED_USER_ID deben estar configurados")
            return False

        if not self.initialize():
            return
            
        try:
            print("🚀 Bot iniciado! Presiona Ctrl+C para detener")
            print(f"📱 Usuario autorizado: {self.config.AUTHORIZED_USER_ID}")
            print("💡 Envía /start al bot para comenzar")
            
            # Iniciar polling del bot
            self.bot_manager.start_polling()
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por el usuario")
            print("\n🛑 Bot detenido correctamente")
            self.shutdown()
            
        except Exception as e:
            logger.error(f"❌ Error fatal en el bot: {e}")
            print(f"❌ Error fatal: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Cierra ordenadamente todos los componentes"""
        try:
            if self.bot_manager:
                self.bot_manager.shutdown()
            
            self.health_checker.stop_monitoring()
            self.memory_manager.cleanup_all()
            
            logger.info("🔄 Shutdown completado")
            
        except Exception as e:
            logger.error(f"Error durante shutdown: {e}")

def main():
    """Función principal"""
    app = FinanceBot()
    app.run()

if __name__ == "__main__":
    main()