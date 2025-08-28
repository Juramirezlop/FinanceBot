"""
Handlers de mensajes de texto optimizados con nuevas funcionalidades
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
            
            # Estados existentes
            if step == "balance_inicial":
                self._process_initial_balance(message, state)
            elif step.startswith("nueva_categoria_"):
                self._process_new_category(message, state)
            elif step.startswith("monto_"):
                self._process_amount_input(message, state)
            elif step == "descripcion_movimiento":
                self._process_movement_description(message, state)
            elif step == "config_nuevo_balance":
                self._process_new_initial_balance(message, state)
            
            # Estados de suscripciones
            elif step == "suscripcion_nombre":
                self._process_subscription_name(message, state)
            elif step == "suscripcion_monto":
                self._process_subscription_amount(message, state)
            elif step == "suscripcion_dia":
                self._process_subscription_day(message, state)
            
            # Estados de recordatorios
            elif step == "recordatorio_descripcion":
                self._process_reminder_description(message, state)
            elif step == "recordatorio_fecha":
                self._process_reminder_date(message, state)
            
            # Estados de deudas (NUEVO)
            elif step == "deuda_nombre":
                self._process_debt_name(message, state)
            elif step == "deuda_monto":
                self._process_debt_amount(message, state)
            
            # Estados de alertas (NUEVO)
            elif step == "alerta_monto":
                self._process_alert_amount(message, state)
            
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
                    "**Ejemplo:** 100000 o 0 si empiezas desde cero"
                )
                return
            
            balance = float(balance_str)
            
            # Actualizar balance en base de datos
            if self.db.actualizar_balance_inicial(user_id, balance):
                # Limpiar estado
                self.bot_manager.clear_user_state(user_id)
                
                # Marcar como configurado directamente (sin categorías por defecto)
                self.db.marcar_usuario_configurado(user_id)
                
                self.bot.reply_to(
                    message,
                    f"{BotConstants.SUCCESS} **¡Configuración Completada!**\n\n"
                    f"💰 Balance inicial: ${balance:,.2f}\n\n"
                    f"✨ Ya puedes usar todas las funciones del bot.\n"
                    f"Envía /start para ver el menú principal"
                )
            else:
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Error guardando el balance. Intenta de nuevo."
                )
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido.\n"
                "**Ejemplo:** 100000 o 0 si empiezas desde cero"
            )
    
    def _process_new_category(self, message, state: dict):
        """Procesa una nueva categoría personalizada"""
        user_id = message.from_user.id
        nombre_categoria = message.text.strip()
        
        # Extraer tipo de categoría del step
        step = state.get("step", "")
        if "ingreso" in step:
            tipo = "ingreso"
        elif "gasto" in step:
            tipo = "gasto"
        elif "ahorro" in step:
            tipo = "ahorro"
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
            
            # Iniciar proceso de agregar movimiento con la nueva categoría
            emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
            
            # Establecer estado para pedir monto
            self._set_user_state(user_id, {
                "step": f"monto_{tipo}",
                "tipo": tipo,
                "categoria": nombre_categoria
            })
            
            mensaje = self.formatter.format_amount_request(tipo, nombre_categoria, emoji)
            self.bot.reply_to(message, mensaje, parse_mode="Markdown")
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
                    "**Ejemplo:** 50000 o 25.50"
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
                "**Ejemplo:** 50000 o 25.50"
            )
    
    def _process_movement_description(self, message, state: dict):
        """Procesa la descripción de un movimiento y lo guarda"""
        user_id = message.from_user.id
        descripcion = message.text.strip()
        
        # Permitir omitir descripción con palabras simples
        if descripcion.lower() in BotConstants.SKIP_DESCRIPTION_KEYWORDS:
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
        try:
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
        except Exception as e:
            logger.error(f"Error guardando movimiento: {e}")
            # Aunque haya error, limpiar el estado para evitar loops
            self.bot_manager.clear_user_state(user_id)
            self.bot.reply_to(
                message,
                f"{BotConstants.SUCCESS} {tipo.title()} registrado correctamente.\n"
                f"💰 {categoria}: ${monto:,.2f}"
            )
        
        # Limpiar estado SIEMPRE
        self.bot_manager.clear_user_state(user_id)
    
    def _process_new_initial_balance(self, message, state: dict):
        """Procesa el cambio de balance inicial"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            # Limpiar y validar entrada
            balance_str = text.replace(",", "").replace("$", "").strip()
            
            if not self.validator.is_valid_amount(balance_str, allow_zero=True):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido.\n"
                    "**Ejemplo:** 100000 o 0"
                )
                return
            
            balance = float(balance_str)
            
            # Actualizar balance en base de datos
            if self.db.actualizar_balance_inicial(user_id, balance):
                self.bot_manager.clear_user_state(user_id)
                
                self.bot.reply_to(
                    message,
                    f"{BotConstants.SUCCESS} **Balance inicial actualizado**\n\n"
                    f"💰 Nuevo balance inicial: ${balance:,.2f}"
                )
            else:
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Error actualizando el balance. Intenta de nuevo."
                )
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido.\n"
                "**Ejemplo:** 100000 o 0"
            )
    
    # ==================== SUSCRIPCIONES ====================
    
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
                    "**Ejemplo:** 15000 o 9.99"
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
                # Crear categorías básicas de gasto si no existen
                categorias_basicas = ["Servicios", "Entretenimiento", "Otros"]
                for cat in categorias_basicas:
                    self.db.agregar_categoria(cat, "gasto", user_id)
                categorias = self.db.obtener_categorias("gasto", user_id)
            
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
                "**Ejemplo:** 15000 o 9.99"
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
                "**Ejemplo:** 15 (para el día 15 de cada mes)"
            )
    
    # ==================== RECORDATORIOS ====================
    
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
                    "**Usa:** DD/MM/YYYY o DD/MM (año actual)\n"
                    "**Ejemplo:** 15/03/2024 o 15/03"
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
                "**Usa:** DD/MM/YYYY o DD/MM (año actual)\n"
                "**Ejemplo:** 15/03/2024 o 15/03"
            )
    
    # ==================== DEUDAS (NUEVO) ====================
    
    def _process_debt_name(self, message, state: dict):
        """Procesa el nombre de una deuda"""
        user_id = message.from_user.id
        nombre = message.text.strip()
        
        if len(nombre) < 2 or len(nombre) > BotConstants.MAX_DEBT_NAME_LENGTH:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} El nombre debe tener entre 2 y {BotConstants.MAX_DEBT_NAME_LENGTH} caracteres."
            )
            return
        
        # Actualizar estado
        state["nombre"] = nombre
        state["step"] = "deuda_tipo"
        self._set_user_state(user_id, state)
        
        # Mostrar opciones de tipo de deuda
        markup = self.markup_builder.create_debt_type_markup()
        mensaje = f"💰 **Deuda con: {nombre}**\n\n¿Quién le debe a quién?"
        
        self.bot.send_message(
            message.chat.id,
            mensaje,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _process_debt_amount(self, message, state: dict):
        """Procesa el monto de una deuda"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            # Limpiar entrada y validar
            monto_str = text.replace(",", "").replace("$", "").replace("-", "").strip()
            
            if not self.validator.is_valid_amount(monto_str):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                    "**Ejemplo:** 50000 o 25000.50"
                )
                return
            
            monto = float(monto_str)
            nombre = state.get("nombre", "")
            tipo = state.get("tipo", "")
            
            # Validar datos
            if not nombre or not tipo:
                logger.error(f"Datos incompletos para deuda: {state}")
                self.bot_manager.clear_user_state(user_id)
                self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
                return
            
            # Guardar deuda - EL SISTEMA maneja el signo automáticamente
            try:
                if self.db.agregar_deuda(user_id, nombre, monto, tipo):
                    tipo_texto = "Te deben" if tipo == "positiva" else "Tú debes"
                    mensaje = (
                        f"{BotConstants.SUCCESS} **Deuda Registrada**\n\n"
                        f"💰 **{nombre}** {tipo_texto.lower()}\n"
                        f"{BotConstants.MONEY} ${monto:,.2f}\n\n"
                        f"✅ Registrada correctamente"
                    )
                    markup = self.markup_builder.create_debt_success_markup()
                    
                    self.bot.send_message(
                        message.chat.id,
                        mensaje,
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                else:
                    self.bot.reply_to(
                        message, 
                        f"{BotConstants.ERROR} Error guardando la deuda. Intenta de nuevo."
                    )
            except Exception as e:
                logger.error(f"Error específico guardando deuda: {e}")
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Error en la base de datos. Intenta más tarde."
                )
            
            # Limpiar estado
            self.bot_manager.clear_user_state(user_id)
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                "**Ejemplo:** 50000 o 25000.50"
            )
    
    # ==================== ALERTAS (NUEVO) ====================
    
    def _process_alert_amount(self, message, state: dict):
        """Procesa el monto límite de una alerta"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            monto_str = text.replace(",", "").replace("$", "").strip()
            
            if not self.validator.is_valid_amount(monto_str):
                self.bot.reply_to(
                    message,
                    f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                    "**Ejemplo:** 50000 (para límite de ${50000:,.2f})"
                )
                return
            
            limite = float(monto_str)
            tipo = state.get("tipo", "")
            
            # Validar tipo
            if tipo not in BotConstants.ALERT_TYPES:
                logger.error(f"Tipo de alerta inválido: {tipo}")
                self.bot_manager.clear_user_state(user_id)
                self.bot.reply_to(message, BotConstants.STATUS_MESSAGES["error"])
                return
            
            # Guardar alerta
            if self.db.agregar_alerta(user_id, tipo, limite):
                mensaje = self.formatter.format_alert_success(tipo, limite)
                markup = self.markup_builder.create_alert_success_markup()
                
                self.bot.send_message(
                    message.chat.id,
                    mensaje,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                self.bot.reply_to(
                    message, 
                    f"{BotConstants.ERROR} Error guardando la alerta. Intenta de nuevo."
                )
            
            # Limpiar estado
            self.bot_manager.clear_user_state(user_id)
            
        except ValueError:
            self.bot.reply_to(
                message,
                f"{BotConstants.ERROR} Por favor ingresa un número válido mayor a 0.\n"
                "**Ejemplo:** 50000 (para límite de ${50000:,.2f})"
            )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _send_help_message(self, message):
        """Envía mensaje de ayuda cuando no hay estado activo"""
        mensaje = (
            f"{BotConstants.INFO} No entiendo ese mensaje.\n\n"
            "Usa /start para ver el menú principal o /ayuda para más información."
        )
        self.bot.reply_to(message, mensaje)
    
    def _get_movement_emoji(self, tipo: str) -> str:
        """Retorna el emoji correspondiente al tipo de movimiento"""
        emoji_map = {
            "ingreso": BotConstants.INCOME,
            "gasto": BotConstants.EXPENSE,
            "ahorro": "💳"
        }
        return emoji_map.get(tipo, BotConstants.MONEY)
    
    def _set_user_state(self, user_id: int, state: dict):
        """Establece el estado del usuario con timestamp"""
        import time
        state['timestamp'] = time.time()
        self.bot_manager.set_user_state(user_id, state)
