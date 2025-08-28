"""
Handlers de callbacks (botones inline) optimizados
"""

import logging
import gc
from config.settings import BotConstants
from utils.message_formatter import MessageFormatter
from utils.markup_builder import MarkupBuilder
from utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

class CallbackHandlers:
    """Gestiona todos los callbacks del bot de forma optimizada"""
    
    def __init__(self, bot_manager):
        from core.bot_manager import BotManager
        self.bot_manager: BotManager = bot_manager
        self.bot = bot_manager.bot
        self.db = bot_manager.db
        self.formatter = MessageFormatter()
        self.markup_builder = MarkupBuilder()
    
    @handle_errors
    def handle_callback_query(self, call):
        """Manejador principal de todos los callbacks"""
        user_id = call.from_user.id
        
        # Verificar autorización
        if not self.bot_manager.is_authorized(user_id):
            self.bot.answer_callback_query(call.id, BotConstants.STATUS_MESSAGES["unauthorized"])
            return
        
        try:
            data = call.data
            
            # Responder al callback inmediatamente para mejor UX
            self.bot.answer_callback_query(call.id)
            
            # Procesar según el tipo de callback
            if data.startswith("add_cat_"):
                self._handle_add_category(call, data)
            elif data.startswith("select_cat_"):
                self._handle_select_category(call, data)
            elif data.startswith("suscripcion_"):
                self._handle_subscription_action(call, data)
            elif data in ["config_next_gastos", "config_complete"]:
                self._handle_config_navigation(call, data)
            elif data.startswith("menu_"):
                self._handle_menu_navigation(call, data)
            elif data in ["back_to_menu", "balance_actual", "resumen_mes"]:
                self._handle_main_actions(call, data)
            elif data.startswith("ver_"):
                self._handle_view_actions(call, data)
            elif data.startswith("agregar_"):
                self._handle_add_actions(call, data)
            elif data.startswith("config_"):
                self._handle_config_actions(call, data)
            else:
                logger.warning(f"Callback no reconocido: {data}")
                self._show_main_menu(call)
            
        except Exception as e:
            logger.error(f"Error procesando callback {call.data}: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
        finally:
            # Limpiar memoria
            gc.collect()
    
    def _handle_add_category(self, call, data: str):
        """Maneja la adición de categorías durante la configuración"""
        user_id = call.from_user.id
        parts = data.split("_", 3)
        
        if len(parts) < 3:
            logger.error(f"Formato de callback inválido: {data}")
            return
        
        tipo = parts[2]  # ingreso o gasto
        
        if len(parts) > 3 and parts[3] != "custom":
            # Categoría predefinida
            categoria = parts[3]
            if self.db.agregar_categoria(categoria, tipo, user_id):
                self.bot.answer_callback_query(
                    call.id, 
                    f"{BotConstants.SUCCESS} '{categoria}' agregada"
                )
            else:
                self.bot.answer_callback_query(
                    call.id, 
                    f"{BotConstants.ERROR} Error agregando categoría"
                )
        else:
            # Categoría personalizada
            self._set_user_state(user_id, {"step": f"custom_category_{tipo}"})
            self.bot.edit_message_text(
                f"Escribe el nombre de la categoría personalizada de {tipo}:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
    
    def _handle_select_category(self, call, data: str):
        """Maneja la selección de categoría para movimientos"""
        user_id = call.from_user.id
        parts = data.split("_", 3)
        
        if len(parts) < 4:
            logger.error(f"Formato de callback inválido: {data}")
            return
        
        tipo = parts[2]
        categoria = parts[3]
        
        # Guardar estado para pedir monto
        state = {
            "step": f"monto_{tipo}",
            "tipo": tipo,
            "categoria": categoria,
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }
        self._set_user_state(user_id, state)
        
        # Mostrar solicitud de monto
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else BotConstants.SAVINGS
        mensaje = self.formatter.format_amount_request(tipo, categoria, emoji)
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _handle_subscription_action(self, call, data: str):
        """Maneja las acciones relacionadas con suscripciones"""
        user_id = call.from_user.id
        
        if data == "suscripcion_cat_":
            # Falta implementar selección de categoría para suscripción
            self._handle_subscription_category_selection(call, data)
        elif data.startswith("suscripcion_cat_"):
            # Selección de categoría para suscripción
            categoria = data.replace("suscripcion_cat_", "")
            self._process_subscription_category(call, categoria)
    
    def _handle_config_navigation(self, call, data: str):
        """Maneja la navegación del wizard de configuración"""
        user_id = call.from_user.id
        
        if data == "config_next_gastos":
            self._show_expense_categories_setup(call)
        elif data == "config_complete":
            if self.db.marcar_usuario_configurado(user_id):
                self.bot.edit_message_text(
                    f"{BotConstants.SUCCESS} Configuración completada!\n\nYa puedes usar todas las funciones del bot.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
                self._show_main_menu(call)
            else:
                self.bot.edit_message_text(
                    f"{BotConstants.ERROR} Error completando configuración",
                    call.message.chat.id,
                    call.message.message_id
                )
    
    def _handle_menu_navigation(self, call, data: str):
        """Maneja la navegación entre menús"""
        menu_map = {
            "menu_ingresos": self._show_income_menu,
            "menu_gastos": self._show_expense_menu,
            "menu_ahorros": self._show_savings_menu,
            "menu_suscripciones": self._show_subscriptions_menu,
            "menu_recordatorios": self._show_reminders_menu,
            "menu_historico": self._show_history_menu,
            "menu_configuracion": self._show_config_menu
        }
        
        handler = menu_map.get(data)
        if handler:
            handler(call)
        else:
            logger.warning(f"Menú no encontrado: {data}")
            self._show_main_menu(call)
    
    def _handle_main_actions(self, call, data: str):
        """Maneja las acciones principales del menú"""
        user_id = call.from_user.id
        
        if data == "back_to_menu":
            self._show_main_menu(call)
        elif data == "balance_actual":
            self._show_current_balance(call, user_id)
        elif data == "resumen_mes":
            self._show_monthly_summary(call, user_id)
    
    def _handle_view_actions(self, call, data: str):
        """Maneja las acciones de visualización"""
        user_id = call.from_user.id
        
        if data == "ver_suscripciones":
            self._show_active_subscriptions(call, user_id)
        elif data == "ver_recordatorios":
            self._show_active_reminders(call, user_id)
        elif data.endswith("_mes"):
            tipo = data.replace("ver_", "").replace("_mes", "")
            self._show_month_movements(call, user_id, tipo)
    
    def _handle_add_actions(self, call, data: str):
        """Maneja las acciones de agregar elementos"""
        user_id = call.from_user.id
        
        if data == "agregar_ingreso":
            self._start_add_movement(call, user_id, "ingreso")
        elif data == "agregar_gasto":
            self._start_add_movement(call, user_id, "gasto")
        elif data == "agregar_ahorro":
            self._start_add_movement(call, user_id, "ahorro")
        elif data == "agregar_suscripcion":
            self._start_add_subscription(call, user_id)
        elif data == "agregar_recordatorio":
            self._start_add_reminder(call, user_id)
    
    # ==================== MÉTODOS DE VISUALIZACIÓN ====================
    
    def _show_main_menu(self, call):
        """Muestra el menú principal"""
        user_id = call.from_user.id
        
        try:
            balance = self.db.obtener_balance_actual(user_id)
            resumen = self.db.obtener_resumen_mes(user_id)
            
            mensaje = self.formatter.format_menu_principal(balance, resumen)
            markup = self.markup_builder.create_main_menu_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando menú principal: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_current_balance(self, call, user_id: int):
        """Muestra el balance actual"""
        try:
            balance = self.db.obtener_balance_actual(user_id)
            mensaje = self.formatter.format_balance(balance)
            markup = self.markup_builder.create_back_to_menu_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando balance: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_monthly_summary(self, call, user_id: int):
        """Muestra el resumen mensual"""
        try:
            resumen = self.db.obtener_resumen_mes(user_id)
            balance_actual = self.db.obtener_balance_actual(user_id)
            
            # Obtener resumen del mes anterior para comparación
            mes_anterior = resumen["mes"] - 1 if resumen["mes"] > 1 else 12
            año_anterior = resumen["año"] if resumen["mes"] > 1 else resumen["año"] - 1
            resumen_anterior = self.db.obtener_resumen_mes(user_id, mes_anterior, año_anterior)
            
            mensaje = self.formatter.format_resumen_detallado(resumen, balance_actual, resumen_anterior)
            markup = self.markup_builder.create_summary_menu_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando resumen mensual: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_income_menu(self, call):
        """Muestra el menú de ingresos"""
        mensaje = self.formatter.format_movement_menu("ingreso")
        markup = self.markup_builder.create_movement_menu_markup("ingreso")
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_expense_menu(self, call):
        """Muestra el menú de gastos"""
        mensaje = self.formatter.format_movement_menu("gasto")
        markup = self.markup_builder.create_movement_menu_markup("gasto")
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_savings_menu(self, call):
        """Muestra el menú de ahorros"""
        mensaje = self.formatter.format_movement_menu("ahorro")
        markup = self.markup_builder.create_movement_menu_markup("ahorro")
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_subscriptions_menu(self, call):
        """Muestra el menú de suscripciones"""
        mensaje = self.formatter.format_subscriptions_menu()
        markup = self.markup_builder.create_subscriptions_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_reminders_menu(self, call):
        """Muestra el menú de recordatorios"""
        mensaje = self.formatter.format_reminders_menu()
        markup = self.markup_builder.create_reminders_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_history_menu(self, call):
        """Muestra el menú de historial"""
        user_id = call.from_user.id
        
        try:
            # Obtener datos históricos
            historico = self._get_historical_data(user_id)
            mensaje = self.formatter.format_historical_data(historico)
            markup = self.markup_builder.create_back_to_menu_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando histórico: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_config_menu(self, call):
        """Muestra el menú de configuración"""
        mensaje = self.formatter.format_config_menu()
        markup = self.markup_builder.create_config_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    # ==================== MÉTODOS DE CONFIGURACIÓN ====================
    
    def _show_expense_categories_setup(self, call):
        """Muestra la configuración de categorías de gasto"""
        markup = self.markup_builder.create_categories_setup_markup(
            "gasto", 
            BotConstants.DEFAULT_EXPENSE_CATEGORIES
        )
        mensaje = self.formatter.format_categorias_setup("gasto")
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    # ==================== MÉTODOS DE ACCIONES ====================
    
    def _start_add_movement(self, call, user_id: int, tipo: str):
        """Inicia el proceso para agregar un movimiento"""
        try:
            # Obtener categorías según el tipo
            if tipo in ["ingreso", "gasto"]:
                categorias = self.db.obtener_categorias(tipo, user_id)
            else:  # ahorro
                categorias = ["Ahorro Programado", "Inversión", "Emergencia", "Meta Específica"]
            
            if not categorias:
                self.bot.edit_message_text(
                    f"{BotConstants.ERROR} No tienes categorías de {tipo} configuradas.\n"
                    "Ve a Configuración para agregar categorías.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.markup_builder.create_back_to_menu_markup()
                )
                return
            
            # Crear botones de categorías
            markup = self.markup_builder.create_category_selection_markup(tipo, categorias)
            mensaje = self.formatter.format_category_selection(tipo)
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error iniciando agregar {tipo}: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _start_add_subscription(self, call, user_id: int):
        """Inicia el proceso para agregar una suscripción"""
        self._set_user_state(user_id, {
            "step": "suscripcion_nombre",
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        })
        
        mensaje = self.formatter.format_subscription_name_request()
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _start_add_reminder(self, call, user_id: int):
        """Inicia el proceso para agregar un recordatorio"""
        self._set_user_state(user_id, {
            "step": "recordatorio_descripcion",
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        })
        
        mensaje = self.formatter.format_reminder_description_request()
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _show_active_subscriptions(self, call, user_id: int):
        """Muestra las suscripciones activas del usuario"""
        try:
            suscripciones = self.db.obtener_suscripciones_activas(user_id)
            mensaje = self.formatter.format_active_subscriptions(suscripciones)
            markup = self.markup_builder.create_subscriptions_view_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando suscripciones: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_active_reminders(self, call, user_id: int):
        """Muestra los recordatorios activos del usuario"""
        try:
            # Implementar cuando se cree el método en DB
            mensaje = self.formatter.format_active_reminders([])
            markup = self.markup_builder.create_reminders_view_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando recordatorios: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_month_movements(self, call, user_id: int, tipo: str):
        """Muestra los movimientos del mes por tipo"""
        try:
            movimientos = self.db.obtener_movimientos_mes(user_id, tipo=tipo)
            mensaje = self.formatter.format_month_movements(movimientos, tipo)
            markup = self.markup_builder.create_back_to_menu_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando movimientos {tipo}: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _process_subscription_category(self, call, categoria: str):
        """Procesa la selección de categoría para suscripción"""
        user_id = call.from_user.id
        state = self.bot_manager.get_user_state(user_id)
        
        if not state or state.get("step") != "suscripcion_categoria":
            logger.warning(f"Estado inválido para categoría de suscripción: {state}")
            self._show_main_menu(call)
            return
        
        # Actualizar estado
        state["categoria"] = categoria
        state["step"] = "suscripcion_dia"
        self._set_user_state(user_id, state)
        
        mensaje = self.formatter.format_subscription_day_request(state)
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _handle_subscription_category_selection(self, call, data: str):
        """Maneja cuando se necesita seleccionar categoría para suscripción"""
        user_id = call.from_user.id
        state = self.bot_manager.get_user_state(user_id)
        
        if not state or state.get("step") != "suscripcion_monto":
            logger.warning(f"Estado inválido para selección de categoría: {state}")
            return
        
        # Obtener categorías de gasto
        categorias = self.db.obtener_categorias("gasto", user_id)
        
        if not categorias:
            self.bot.edit_message_text(
                f"{BotConstants.ERROR} No tienes categorías de gasto configuradas.\n"
                "Ve a Configuración para agregar categorías.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.markup_builder.create_back_to_menu_markup()
            )
            return
        
        # Crear markup para selección de categoría
        markup = self.markup_builder.create_subscription_category_markup(categorias)
        mensaje = self.formatter.format_subscription_category_selection(state)
        
        # Actualizar estado
        state["step"] = "suscripcion_categoria"
        self._set_user_state(user_id, state)
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _get_historical_data(self, user_id: int) -> list:
        """Obtiene datos históricos de los últimos 6 meses"""
        try:
            from datetime import date, timedelta
            
            # Calcular últimos 6 meses
            hoy = date.today()
            meses_historico = []
            
            for i in range(6):
                if hoy.month - i > 0:
                    mes = hoy.month - i
                    año = hoy.year
                else:
                    mes = 12 + (hoy.month - i)
                    año = hoy.year - 1
                
                resumen = self.db.obtener_resumen_mes(user_id, mes, año)
                if resumen["ingresos"] > 0 or resumen["gastos"] > 0:
                    meses_historico.append(resumen)
            
            return meses_historico
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            return []
    
    def _set_user_state(self, user_id: int, state: dict):
        """Establece el estado del usuario con timestamp"""
        import time
        state['timestamp'] = time.time()
        self.bot_manager.set_user_state(user_id, state)
    
    def _handle_config_actions(self, call, data):
        """Maneja las acciones de configuración"""
        if data == "config_categorias":
            self.bot.edit_message_text(
                "⚙️ **Gestión de Categorías**\n\n"
                "Funcionalidad en desarrollo.\n"
                "Por ahora puedes agregar categorías durante el registro de movimientos.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.markup_builder.create_back_to_menu_markup()
            )
        elif data == "config_balance":
            self.bot.edit_message_text(
                "💰 **Cambiar Balance Inicial**\n\n"
                "Funcionalidad en desarrollo.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.markup_builder.create_back_to_menu_markup()
            )
        elif data == "ver_configuracion":
            user_id = call.from_user.id
            balance_inicial = "Configurado"  # Podrías obtener el valor real de la DB
            self.bot.edit_message_text(
                "📊 **Tu Configuración Actual**\n\n"
                f"💰 Balance inicial: {balance_inicial}\n"
                f"👤 Usuario autorizado: {user_id}\n"
                "📱 Bot configurado correctamente",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.markup_builder.create_back_to_menu_markup()
            )