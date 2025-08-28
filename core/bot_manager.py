"""
Gestor principal del bot de Telegram - CORREGIDO COMPLETAMENTE
"""

import threading
import logging
import time
from typing import Optional, Dict, Any
import telebot
from telebot.types import BotCommand
from config.settings import BotConfig
from db.database_manager import DatabaseManager
from handlers.command_handlers import CommandHandlers
from handlers.callback_handlers import CallbackHandlers
from handlers.message_handlers import MessageHandlers
from core.scheduler import TaskScheduler
from utils.memory_manager import MemoryManager
from utils.error_handler import ErrorHandler
from core.flask_server import create_flask_app

logger = logging.getLogger(__name__)

class BotManager:
    """Clase que gestiona toda la funcionalidad del bot"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.bot: Optional[telebot.TeleBot] = None
        self.db: Optional[DatabaseManager] = None
        self.scheduler: Optional[TaskScheduler] = None
        self.memory_manager = MemoryManager()
        self.error_handler = ErrorHandler()
        
        # Handlers
        self.command_handlers: Optional[CommandHandlers] = None
        self.callback_handlers: Optional[CallbackHandlers] = None
        self.message_handlers: Optional[MessageHandlers] = None
        
        # Estados y control
        self.user_states: Dict[int, Dict[str, Any]] = {}
        self.is_running = False
        self.flask_thread: Optional[threading.Thread] = None
        
    def initialize_bot(self) -> bool:
        """Inicializa el bot de Telegram"""
        try:
            self.bot = telebot.TeleBot(
                self.config.BOT_TOKEN,
                parse_mode=None,  # No usar parse_mode por defecto para evitar errores
                threaded=True
            )
            
            # Configurar comandos del bot
            self._set_bot_commands()
            
            # Configurar manejo de errores CORRECTO
            def exception_handler(exception):
                logger.error(f"Error no manejado en telebot: {exception}")
                return True  # Continuar funcionando
            
            self.bot.exception_handler = exception_handler
            
            logger.info("Bot de Telegram inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando bot: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Inicializa la base de datos"""
        try:
            self.db = DatabaseManager(
                self.config.DATABASE_PATH,
                self.config.DATABASE_TIMEOUT
            )
            
            if not self.db.initialize():
                logger.error("Error inicializando base de datos")
                return False
                
            logger.info("Base de datos inicializada")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando database: {e}")
            return False
    
    def register_handlers(self):
        """Registra todos los handlers del bot"""
        if not self.bot or not self.db:
            raise RuntimeError("Bot o DB no inicializados")
        
        # Inicializar handlers
        self.command_handlers = CommandHandlers(self)
        self.callback_handlers = CallbackHandlers(self)
        self.message_handlers = MessageHandlers(self)
        
        # Registrar comandos (SIN /reset ni /config)
        self.bot.message_handler(commands=['start'])(
            self.command_handlers.handle_start
        )
        self.bot.message_handler(commands=['balance'])(
            self.command_handlers.handle_balance
        )
        self.bot.message_handler(commands=['gasto'])(
            self.command_handlers.handle_gasto_rapido
        )
        self.bot.message_handler(commands=['ingreso'])(
            self.command_handlers.handle_ingreso_rapido
        )
        self.bot.message_handler(commands=['resumen'])(
            self.command_handlers.handle_resumen
        )
        self.bot.message_handler(commands=['backup'])(
            self.command_handlers.handle_backup
        )
        self.bot.message_handler(commands=['ayuda', 'help'])(
            self.command_handlers.handle_ayuda
        )
        
        # Registrar callbacks
        self.bot.callback_query_handler(func=lambda call: True)(
            self.callback_handlers.handle_callback_query
        )
        
        # Registrar mensajes de texto (último para capturar todo)
        self.bot.message_handler(
            func=lambda message: True,
            content_types=['text']
        )(self.message_handlers.handle_text_input)
        
        logger.info("Handlers registrados correctamente")
    
    def start_scheduler(self):
        """Inicia el programador de tareas"""
        try:
            self.scheduler = TaskScheduler(self)
            self.scheduler.start()
            logger.info("Scheduler iniciado")
            
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
    
    def start_flask_server(self):
        """Inicia el servidor Flask en un hilo separado"""
        try:
            app = create_flask_app()
            
            def run_flask():
                app.run(
                    host=self.config.FLASK_HOST,
                    port=self.config.FLASK_PORT,
                    debug=False,
                    use_reloader=False
                )
            
            self.flask_thread = threading.Thread(target=run_flask, daemon=True)
            self.flask_thread.start()
            logger.info(f"Servidor Flask iniciado en puerto {self.config.FLASK_PORT}")
            
        except Exception as e:
            logger.error(f"Error iniciando Flask: {e}")
    
    def start_polling(self):
        """Inicia el polling del bot con manejo mejorado de conflictos"""
        if not self.bot:
            raise RuntimeError("Bot no inicializado")
        
        try:
            self.is_running = True
            
            # Iniciar servidor Flask para Render
            self.start_flask_server()
            
            # Intentar polling con reintentos para error 409
            max_retries = 3
            retry_delay = 30
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Iniciando polling (intento {attempt + 1}/{max_retries})")
                    
                    # Iniciar polling SIN none_stop para mejor manejo de errores
                    self.bot.infinity_polling(
                        timeout=60,
                        skip_pending=True,
                        allowed_updates=["message", "callback_query"]
                    )
                    break
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    if "409" in error_msg or "conflict" in error_msg:
                        if attempt < max_retries - 1:
                            logger.warning(f"Error 409. Reintentando en {retry_delay} segundos...")
                            print(f"⚠️  Otra instancia detectada. Esperando {retry_delay}s...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error("Máximo de reintentos alcanzado para error 409")
                    
                    # Para otros errores, lanzar inmediatamente
                    raise e
        
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por el usuario")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Error fatal en el bot: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Cierra ordenadamente el bot"""
        try:
            self.is_running = False
            
            if self.bot:
                self.bot.stop_polling()
            
            if self.scheduler:
                self.scheduler.stop()
            
            if self.db:
                self.db.close()
            
            # Limpiar estados de usuario
            self.user_states.clear()
            
            # Limpiar memoria
            self.memory_manager.cleanup_all()
            
            logger.info("Bot cerrado correctamente")
            
        except Exception as e:
            logger.error(f"Error durante shutdown: {e}")
    
    def is_authorized(self, user_id: int) -> bool:
        """Verifica si el usuario está autorizado"""
        return user_id == self.config.AUTHORIZED_USER_ID
    
    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el estado actual del usuario"""
        return self.user_states.get(user_id)
    
    def set_user_state(self, user_id: int, state: Dict[str, Any]):
        """Establece el estado del usuario con límite de memoria"""
        # Limpiar estados antiguos si hay demasiados
        if len(self.user_states) >= self.config.MAX_USER_STATES:
            # Eliminar el estado más antiguo
            oldest_user = next(iter(self.user_states))
            del self.user_states[oldest_user]
            logger.warning(f"Estado limpiado para usuario {oldest_user} (límite alcanzado)")
        
        self.user_states[user_id] = state
    
    def clear_user_state(self, user_id: int):
        """Limpia el estado del usuario"""
        self.user_states.pop(user_id, None)
    
    def cleanup_old_states(self):
        """Limpia estados antiguos de usuarios inactivos"""
        current_time = time.time()
        timeout = 7200  # 2 horas
        
        to_remove = []
        for user_id, state in self.user_states.items():
            if 'timestamp' in state:
                if current_time - state['timestamp'] > timeout:
                    to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.user_states[user_id]
            logger.debug(f"Estado expirado limpiado para usuario {user_id}")
    
    def _set_bot_commands(self):
        """Configura los comandos del bot en Telegram - LIMPIADOS"""
        commands = [
            BotCommand("start", "Menú principal"),
            BotCommand("balance", "Ver balance total"),
            BotCommand("gasto", "Registro rápido de gasto"),
            BotCommand("ingreso", "Registro rápido de ingreso"),
            BotCommand("resumen", "Resumen del mes actual"),
            BotCommand("backup", "Generar backup manual"),
            BotCommand("ayuda", "Guía completa de uso")
        ]
        
        try:
            self.bot.set_my_commands(commands)
            logger.info("Comandos del bot configurados")
        except Exception as e:
            logger.error(f"Error configurando comandos: {e}")
