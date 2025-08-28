"""
Handlers de mensajes de texto optimizados
"""

import logging
import gc
from config.settings import BotConstants
from utils.message_formatter import MessageFormatter
from utils.markup_builder import MarkupBuilder
from utils.validator import InputValidator
from utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

class MessageHandlers:
    """Gestiona todos los mensajes de texto del bot"""
    
    def __init__(self, bot_manager):
        from core.bot_manager import BotManager
        self.bot_manager: BotManager = bot_manager
        self.bot = bot_manager.bot
        self.db = bot_manager.db
        self.formatter = MessageFormatter()
        self.markup_builder = MarkupBuilder()
        self.validator = InputValidator()
    
    @handle_errors
    def handle_text_input(self, message):
        """Manejador principal de mensajes de texto"""
        user_id = message.from_user.id
        
        # Verificar autorización
        if not self.bot_manager.is_authorized(user_id):
            return
        
        try:
            # Obtener estado actual del usuario
            state = self.bot_manager.get_user_state(user_id)
            
            if not state:
                # No hay estado activo, mostrar ayuda
                self._send_help_message(message)
                return
            
            # Procesar según el paso actual
            step = state.get("step", "")
            
            if step == "balance_inicial":
                self._process_initial_balance(message, state)
            elif step.startswith("custom_category_"):
                self._process_custom_category(message, state)
            elif step.startswith("monto_"):
                self._process_amount_input(message, state)
            elif step == "descripcion_movimiento":
                self._process_movement_description(message, state)
            elif step == "suscripcion_nombre":
                self._process_subscription_name(message, state)
            elif step == "suscripcion_monto":
                self._process_subscription_amount(message, state)
            elif step == "suscripcion_dia":
                self._process_subscription_day(message, state)
            elif step == "recordatorio_descripcion":
                self._process_reminder_description(message, state)
            elif step == "recordatorio_fecha":
                self._process_reminder_date(message, state)
            else:
                logger.warning(f"Paso no reconocido: {step}")
                self._send_help_message(message)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de texto: {e}")
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
        finally:
            # Limpiar memoria
            gc.collect()
    
    def _process_initial_balance(self, message, state: dict):
        """Procesa el balance inicial ingresado"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            # Limpiar y validar entrada
            balance_str = text.replace(",", "").replace("$", "").strip()
            
            if not self.validator.is_valid_amount(balance_str, allow_zero=True):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido.\n"
                    "Ejemplo: 100000 o 0 si empiezas desde cero"
                )
                return
            
            balance = float(balance_str)
            
            # Actualizar balance en base de datos
            if self.db.actualizar_balance_inicial(user_id, balance):
                # Limpiar estado y continuar configuración
                self.bot_manager.clear_user_state(user_id)
                
                self.bot.reply_to(
                    message,
                    f"{BotConstants.SUCCESS} Balance inicial configurado: ${balance:,.2f}\n\n"
                    "Continuemos con la configuración de categorías..."
                )
                
                self._show_income_categories_setup(message)
            else:
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Error guardando el balance. Intenta de nuevo."
                )
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido.\n"
                "Ejemplo: 100000 o 0 si empiezas desde cero"
            )
    
    def _process_custom_category(self, message, state: dict):
        """Procesa una categoría personalizada"""
        user_id = message.from_user.id
        nombre_categoria = message.text.strip()
        
        # Extraer tipo de categoría del step
        step = state.get("step", "")
        if "ingreso" in step:
            tipo = "ingreso"
        elif "gasto" in step:
            tipo = "gasto"
        else:
            logger.error(f"Tipo de categoría no válido en step: {step}")
            self.bot_manager.clear_user_state(user_id)
            return
        
        # Validar nombre
        if not self.validator.is_valid_category_name(nombre_categoria):
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} El nombre debe tener entre 2 y {BotConstants.MAX_CATEGORY_NAME_LENGTH} caracteres."
            )
            return
        
        # Agregar categoría
        if self.db.agregar_categoria(nombre_categoria, tipo, user_id):
            self.bot_manager.clear_user_state(user_id)
            self.bot.reply_to(
                message,
                f"{BotConstants.SUCCESS} Categoría '{nombre_categoria}' agregada correctamente."
            )
            
            # Mostrar paso de configuración correspondiente
            if tipo == "ingreso":
                self._show_income_categories_setup(message)
            else:
                self._show_expense_categories_setup(message)
        else:
            self.bot.reply_to(
                message, 
                f"{BotConstants.ERROR} Error agregando la categoría. Intenta de nuevo."
            )
    
    def _process_amount_input(self, message, state: dict):
        """Procesa la entrada de monto para un movimiento"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            # Limpiar y validar monto
            monto_str = text.replace(",", "").replace("$", "").strip()
            
            if not self.validator.is_valid_amount(monto_str):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                    "Ejemplo: 50000 o 25.50"
                )
                return
            
            monto = float(monto_str)
            
            # Actualizar estado
            state["monto"] = monto
            state["step"] = "descripcion_movimiento"
            self._set_user_state(user_id, state)
            
            # Solicitar descripción
            tipo = state.get("tipo", "")
            categoria = state.get("categoria", "")
            emoji = self._get_movement_emoji(tipo)
            
            mensaje = self.formatter.format_description_request(tipo, categoria, monto, emoji)
            self.bot.send_message(message.chat.id, mensaje, parse_mode="Markdown")
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                "Ejemplo: 50000 o 25.50"
            )
    
    def _process_movement_description(self, message, state: dict):
        """Procesa la descripción de un movimiento y lo guarda"""
        user_id = message.from_user.id
        descripcion = message.text.strip()
        
        # Permitir omitir descripción
        if descripcion.lower() in ["sin descripcion", "skip", "omitir", "no"]:
            descripcion = ""
        
        # Obtener datos del estado
        tipo = state.get("tipo", "")
        categoria = state.get("categoria", "")
        monto = state.get("monto", 0)
        
        # Validar que tenemos todos los datos
        if not tipo or not categoria or not monto:
            logger.error(f"Datos incompletos en estado: {state}")
            self.bot_manager.clear_user_state(user_id)
            self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
            return
        
        # Guardar el movimiento
        if self.db.agregar_movimiento(user_id, tipo, categoria, monto, descripcion):
            nuevo_balance = self.db.obtener_balance_actual(user_id)
            
            mensaje = self.formatter.format_movement_success(
                tipo, categoria, monto, descripcion, nuevo_balance
            )
            markup = self.markup_builder.create_movement_success_markup(tipo)
            
            self.bot.send_message(
                message.chat.id,
                mensaje,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            self.bot.reply_to(
                message, 
                f"{BotConstants.ERROR} Error guardando el {tipo}. Intenta de nuevo."
            )
        
        # Limpiar estado
        self.bot_manager.clear_user_state(user_id)
    
    def _process_subscription_name(self, message, state: dict):
        """Procesa el nombre de una suscripción"""
        user_id = message.from_user.id
        nombre = message.text.strip()
        
        if not self.validator.is_valid_subscription_name(nombre):
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} El nombre debe tener entre 2 y {BotConstants.MAX_SUBSCRIPTION_NAME_LENGTH} caracteres."
            )
            return
        
        # Actualizar estado
        state["nombre"] = nombre
        state["step"] = "suscripcion_monto"
        self._set_user_state(user_id, state)
        
        mensaje = self.formatter.format_subscription_amount_request(nombre)
        self.bot.reply_to(message, mensaje, parse_mode="Markdown")
    
    def _process_subscription_amount(self, message, state: dict):
        """Procesa el monto de una suscripción"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            monto_str = text.replace(",", "").replace("$", "").strip()
            
            if not self.validator.is_valid_amount(monto_str):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                    "Ejemplo: 15000 o 9.99"
                )
                return
            
            monto = float(monto_str)
            
            # Actualizar estado
            state["monto"] = monto
            state["step"] = "suscripcion_categoria"
            self._set_user_state(user_id, state)
            
            # Mostrar categorías de gasto para seleccionar
            categorias = self.db.obtener_categorias("gasto", user_id)
            
            if not categorias:
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} No tienes categorías de gasto configuradas.\n"
                    "Ve a Configuración para agregar categorías."
                )
                self.bot_manager.clear_user_state(user_id)
                return
            
            markup = self.markup_builder.create_subscription_category_markup(categorias)
            mensaje = self.formatter.format_subscription_category_selection(state)
            
            self.bot.send_message(
                message.chat.id,
                mensaje,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                "Ejemplo: 15000 o 9.99"
            )
    
    def _process_subscription_day(self, message, state: dict):
        """Procesa el día de cobro de una suscripción"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            dia = int(text)
            
            if not (1 <= dia <= 31):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un día válido entre 1 y 31."
                )
                return
            
            # Obtener datos del estado
            nombre = state.get("nombre", "")
            monto = state.get("monto", 0)
            categoria = state.get("categoria", "")
            
            # Validar que tenemos todos los datos
            if not nombre or not monto or not categoria:
                logger.error(f"Datos incompletos para suscripción: {state}")
                self.bot_manager.clear_user_state(user_id)
                self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
                return
            
            # Guardar la suscripción
            if self.db.agregar_suscripcion(user_id, nombre, monto, categoria, dia):
                mensaje = self.formatter.format_subscription_success(nombre, monto, categoria, dia)
                markup = self.markup_builder.create_subscription_success_markup()
                
                self.bot.send_message(
                    message.chat.id,
                    mensaje,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                self.bot.reply_to(
                    message, 
                    f"{BotConstants.ERROR} Error guardando la suscripción. Intenta de nuevo."
                )
            
            # Limpiar estado
            self.bot_manager.clear_user_state(user_id)
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido entre 1 y 31.\n"
                "Ejemplo: 15 (para el día 15 de cada mes)"
            )
    
    def _process_reminder_description(self, message, state: dict):
        """Procesa la descripción de un recordatorio"""
        user_id = message.from_user.id
        descripcion = message.text.strip()
        
        if not self.validator.is_valid_description(descripcion):
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} La descripción debe tener entre 2 y {BotConstants.MAX_DESCRIPTION_LENGTH} caracteres."
            )
            return
        
        # Actualizar estado
        state["descripcion"] = descripcion
        state["step"] = "recordatorio_fecha"
        self._set_user_state(user_id, state)
        
        mensaje = self.formatter.format_reminder_date_request()
        self.bot.reply_to(message, mensaje, parse_mode="Markdown")
    
    def _process_reminder_date(self, message, state: dict):
        """Procesa la fecha de un recordatorio"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            # Validar y parsear fecha
            fecha = self.validator.parse_date(text)
            if not fecha:
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Formato de fecha inválido.\n"
                    "Usa: DD/MM/YYYY o DD/MM (año actual)\n"
                    "Ejemplo: 15/03/2024 o 15/03"
                )
                return
            
            # Obtener descripción del estado
            descripcion = state.get("descripcion", "")
            
            if not descripcion:
                logger.error(f"Descripción faltante en recordatorio: {state}")
                self.bot_manager.clear_user_state(user_id)
                self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
                return
            
            # Guardar recordatorio
            if self.db.agregar_recordatorio(user_id, descripcion, fecha):
                mensaje = self.formatter.format_reminder_success(descripcion, fecha)
                markup = self.markup_builder.create_reminder_success_markup()
                
                self.bot.send_message(
                    message.chat.id,
                    mensaje,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                self.bot.reply_to(
                    message, 
                    f"{BotConstants.ERROR} Error guardando el recordatorio. Intenta de nuevo."
                )
            
            # Limpiar estado
            self.bot_manager.clear_user_state(user_id)
            
        except Exception as e:
            logger.error(f"Error procesando fecha de recordatorio: {e}")
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Formato de fecha inválido.\n"
                "Usa: DD/MM/YYYY o DD/MM (año actual)\n"
                "Ejemplo: 15/03/2024 o 15/03"
            )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _send_help_message(self, message):
        """Envía mensaje de ayuda cuando no hay estado activo"""
        mensaje = (
            f"{BotConstants.INFO} No entiendo ese mensaje.\n\n"
            "Usa /start para ver el menú principal o /ayuda para más información."
        )
        self.bot.reply_to(message, mensaje)
    
    def _show_income_categories_setup(self, message):
        """Muestra la configuración de categorías de ingreso"""
        markup = self.markup_builder.create_categories_setup_markup(
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
    
    def _show_expense_categories_setup(self, message):
        """Muestra la configuración de categorías de gasto"""
        markup = self.markup_builder.create_categories_setup_markup(
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
    
    def _get_movement_emoji(self, tipo: str) -> str:
        """Retorna el emoji correspondiente al tipo de movimiento"""
        emoji_map = {
            "ingreso": BotConstants.INCOME,
            "gasto": BotConstants.EXPENSE,
            "ahorro": BotConstants.SAVINGS
        }
        return emoji_map.get(tipo, BotConstants.MONEY)
    
    def _set_user_state(self, user_id: int, state: dict):
        """Establece el estado del usuario con timestamp"""
        import time
        state['timestamp'] = time.time()
        self.bot_manager.set_user_state(user_id, state)