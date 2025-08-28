"""
Handlers de comandos del bot optimizados para mejor rendimiento y estabilidad
"""

import logging
import gc
from config.settings import BotConstants
from utils.message_formatter import MessageFormatter
from utils.validator import InputValidator
from utils.error_handler import handle_errors
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Gestiona todos los comandos del bot de forma optimizada"""
    
    def __init__(self, bot_manager):
        from core.bot_manager import BotManager
        self.bot_manager: BotManager = bot_manager
        self.bot = bot_manager.bot
        self.db = bot_manager.db
        self.formatter = MessageFormatter()
        self.validator = InputValidator()
    
    @handle_errors
    def handle_start(self, message):
        """Comando /start - Punto de entrada principal optimizado"""
        user_id = message.from_user.id
        
        # Verificar autorización
        if not self.bot_manager.is_authorized(user_id):
            self._send_unauthorized_message(message)
            return
        
        try:
            # Limpiar estado previo del usuario
            self.bot_manager.clear_user_state(user_id)
            
            # Verificar si es usuario nuevo o no configurado
            if not self.db.usuario_existe(user_id):
                self._iniciar_wizard_configuracion(message)
            elif not self.db.usuario_configurado(user_id):
                self._continuar_wizard_configuracion(message)
            else:
                self._mostrar_menu_principal(message)
                
        except Exception as e:
            logger.error(f"Error en comando start: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
        finally:
            # Limpiar referencias para liberar memoria
            gc.collect()
    
    @handle_errors
    def handle_balance(self, message):
        """Comando /balance - Muestra balance rápido"""
        user_id = message.from_user.id
        
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            balance = self.db.obtener_balance_actual(user_id)
            mensaje = self.formatter.format_balance(balance)
            self.bot.reply_to(message, mensaje, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    @handle_errors
    def handle_gasto_rapido(self, message):
        """Comando /gasto - Registro rápido de gasto"""
        user_id = message.from_user.id
        
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            texto = message.text.replace('/gasto', '').strip()
            
            if texto:
                self._procesar_comando_rapido(message, texto, "gasto")
            else:
                self._mostrar_menu_gastos_directo(message)
                
        except Exception as e:
            logger.error(f"Error en comando gasto: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    @handle_errors
    def handle_ingreso_rapido(self, message):
        """Comando /ingreso - Registro rápido de ingreso"""
        user_id = message.from_user.id
        
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            texto = message.text.replace('/ingreso', '').strip()
            
            if texto:
                self._procesar_comando_rapido(message, texto, "ingreso")
            else:
                self._mostrar_menu_ingresos_directo(message)
                
        except Exception as e:
            logger.error(f"Error en comando ingreso: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    @handle_errors
    def handle_resumen(self, message):
        """Comando /resumen - Muestra resumen del mes"""
        user_id = message.from_user.id
        
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            resumen = self.db.obtener_resumen_mes(user_id)
            balance = self.db.obtener_balance_actual(user_id)
            
            mensaje = self.formatter.format_resumen_mensual(resumen, balance)
            self.bot.reply_to(message, mensaje, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    @handle_errors
    def handle_config(self, message):
        """Comando /config - Acceso rápido a configuración"""
        user_id = message.from_user.id
        
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            self._mostrar_menu_configuracion_directo(message)
            
        except Exception as e:
            logger.error(f"Error en comando config: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    @handle_errors
    def handle_ayuda(self, message):
        """Comando /ayuda - Guía de uso"""
        try:
            mensaje = self.formatter.format_ayuda()
            self.bot.reply_to(message, mensaje, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error en comando ayuda: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _send_unauthorized_message(self, message):
        """Envía mensaje de no autorizado"""
        self.bot.reply_to(message, f"{BotConstants.ERROR} No tienes permisos para usar este bot.")
    
    def _iniciar_wizard_configuracion(self, message):
        """Inicia el wizard de configuración para usuarios nuevos"""
        user_id = message.from_user.id
        
        # Crear usuario en DB
        if not self.db.crear_usuario(user_id):
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
            return
        
        # Establecer estado inicial
        self._set_user_state(user_id, {"step": "balance_inicial"})
        
        mensaje = self.formatter.format_bienvenida_configuracion()
        self.bot.send_message(message.chat.id, mensaje, parse_mode="Markdown")
    
    def _continuar_wizard_configuracion(self, message):
        """Continúa el wizard de configuración"""
        user_id = message.from_user.id
        
        # Determinar paso actual
        categorias_ingreso = self.db.obtener_categorias("ingreso", user_id)
        categorias_gasto = self.db.obtener_categorias("gasto", user_id)
        
        if not categorias_ingreso:
            self._mostrar_paso_categorias_ingreso(message)
        elif not categorias_gasto:
            self._mostrar_paso_categorias_gasto(message)
        else:
            # Configuración completa
            self.db.marcar_usuario_configurado(user_id)
            self._mostrar_menu_principal(message)
    
    def _mostrar_menu_principal(self, message):
        """Muestra el menú principal optimizado"""
        user_id = message.from_user.id
        
        try:
            # Obtener datos necesarios de forma eficiente
            balance = self.db.obtener_balance_actual(user_id)
            resumen = self.db.obtener_resumen_mes(user_id)
            
            # Crear mensaje y markup
            mensaje = self.formatter.format_menu_principal(balance, resumen)
            markup = self.formatter.create_main_menu_markup()
            
            self.bot.send_message(
                message.chat.id, 
                mensaje, 
                reply_markup=markup, 
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error mostrando menu principal: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
    
    def _mostrar_paso_categorias_ingreso(self, message):
        """Muestra el paso de configuración de categorías de ingreso"""
        from utils.markup_builder import MarkupBuilder
        
        markup = MarkupBuilder.create_categories_setup_markup(
            "ingreso", 
            BotConstants.DEFAULT_INCOME_CATEGORIES
        )
        
        mensaje = self.formatter.format_categorias_setup("ingreso")
        self.bot.send_message(
            message.chat.id, 
            mensaje, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    
    def _mostrar_paso_categorias_gasto(self, message):
        """Muestra el paso de configuración de categorías de gasto"""
        from utils.markup_builder import MarkupBuilder
        
        markup = MarkupBuilder.create_categories_setup_markup(
            "gasto", 
            BotConstants.DEFAULT_EXPENSE_CATEGORIES
        )
        
        mensaje = self.formatter.format_categorias_setup("gasto")
        self.bot.send_message(
            message.chat.id, 
            mensaje, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    
    def _procesar_comando_rapido(self, message, texto: str, tipo: str):
        """Procesa un comando rápido de ingreso/gasto"""
        user_id = message.from_user.id
        
        try:
            partes = texto.split(' ', 1)
            monto_str = partes[0].replace(',', '').replace('$', '').strip()
            
            # Validar y convertir monto
            if not self.validator.is_valid_amount(monto_str):
                mensaje_error = self.formatter.format_error_comando_rapido(tipo)
                self.bot.reply_to(message, mensaje_error, parse_mode="Markdown")
                return
            
            monto = float(monto_str)
            descripcion = partes[1] if len(partes) > 1 else ""
            
            # Obtener categoría por defecto
            categorias = self.db.obtener_categorias(tipo, user_id)
            if not categorias:
                mensaje = f"{BotConstants.ERROR} No tienes categorías de {tipo} configuradas"
                self.bot.reply_to(message, mensaje)
                return
            
            # Usar categoría por defecto o primera disponible
            categoria_default = f"{tipo.title()}s Varios"
            categoria = categoria_default if categoria_default in categorias else categorias[0]
            
            # Registrar movimiento
            if self.db.agregar_movimiento(user_id, tipo, categoria, monto, descripcion):
                balance = self.db.obtener_balance_actual(user_id)
                mensaje = self.formatter.format_movimiento_registrado(
                    tipo, categoria, monto, descripcion, balance
                )
                self.bot.reply_to(message, mensaje, parse_mode="Markdown")
            else:
                self.bot.reply_to(message, f"{BotConstants.ERROR} Error registrando el {tipo}")
                
        except Exception as e:
            logger.error(f"Error procesando comando rápido {tipo}: {e}")
            mensaje_error = self.formatter.format_error_comando_rapido(tipo)
            self.bot.reply_to(message, mensaje_error, parse_mode="Markdown")
    
    def _mostrar_menu_gastos_directo(self, message):
        """Muestra menú de gastos directamente"""
        from utils.markup_builder import MarkupBuilder
        
        markup = MarkupBuilder.create_movement_menu_markup("gasto")
        mensaje = self.formatter.format_movement_menu("gasto")
        
        self.bot.reply_to(
            message, 
            mensaje, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    
    def _mostrar_menu_ingresos_directo(self, message):
        """Muestra menú de ingresos directamente"""
        from utils.markup_builder import MarkupBuilder
        
        markup = MarkupBuilder.create_movement_menu_markup("ingreso")
        mensaje = self.formatter.format_movement_menu("ingreso")
        
        self.bot.reply_to(
            message, 
            mensaje, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    
    def _mostrar_menu_configuracion_directo(self, message):
        """Muestra menú de configuración directamente"""
        from utils.markup_builder import MarkupBuilder
        
        markup = MarkupBuilder.create_config_menu_markup()
        mensaje = self.formatter.format_config_menu()
        
        self.bot.reply_to(
            message, 
            mensaje, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    
    def _set_user_state(self, user_id: int, state: Dict[str, Any]):
        """Establece el estado del usuario con timestamp"""
        import time
        state['timestamp'] = time.time()
        self.bot_manager.set_user_state(user_id, state)
    
    def _get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del usuario"""
        return self.bot_manager.get_user_state(user_id)