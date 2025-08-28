"""
Handlers de callbacks (botones inline) optimizados con nuevas funcionalidades
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
            if data.startswith("nueva_categoria_"):
                self._handle_new_category_request(call, data)
            elif data.startswith("select_cat_"):
                self._handle_select_category(call, data)
            elif data.startswith("suscripcion_"):
                self._handle_subscription_action(call, data)
            elif data.startswith("deuda_"):
                self._handle_debt_action(call, data)
            elif data.startswith("alerta_"):
                self._handle_alert_action(call, data)
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
    
    def _handle_new_category_request(self, call, data: str):
        """Maneja la solicitud de crear nueva categoría"""
        user_id = call.from_user.id
        tipo = data.replace("nueva_categoria_", "")
        
        if tipo not in BotConstants.MOVEMENT_TYPES:
            logger.error(f"Tipo de categoría inválido: {tipo}")
            return
        
        # Establecer estado para nueva categoría
        self._set_user_state(user_id, {
            "step": f"nueva_categoria_{tipo}",
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        })
        
        # Mostrar solicitud de nombre
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
        """Muestra el menú de configuración mejorado"""
        mensaje = self.formatter.format_config_menu()
        markup = self.markup_builder.create_config_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    # ==================== SUSCRIPCIONES ====================
    
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
    
    def _show_active_subscriptions(self, call, user_id: int):
        """Muestra las suscripciones activas"""
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
    
    # ==================== RECORDATORIOS ====================
    
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
    
    def _show_active_reminders(self, call, user_id: int):
        """Muestra los recordatorios activos"""
        try:
            # Por ahora mostramos mensaje básico
            # En implementación completa se obtendría de la DB
            recordatorios = []  # self.db.obtener_recordatorios_activos(user_id)
            mensaje = self.formatter.format_active_reminders(recordatorios)
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
    
    # ==================== CONFIGURACIÓN ====================
    
    def _handle_config_actions(self, call, data):
        """Maneja las acciones de configuración mejoradas"""
        user_id = call.from_user.id
        
        if data == "config_balance_inicial":
            self._set_user_state(user_id, {
                "step": "config_nuevo_balance",
                "chat_id": call.message.chat.id,
                "message_id": call.message.message_id
            })
            
            self.bot.edit_message_text(
                "💰 **Cambiar Balance Inicial**\n\n"
                "Ingresa el nuevo balance inicial:\n"
                "**Ejemplo:** 100000 o 0",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            
        elif data == "config_estadisticas":
            try:
                stats = self.db.obtener_estadisticas_db()
                mensaje = (
                    "📊 **Estadísticas del Bot**\n\n"
                    f"👤 Usuarios: {stats.get('usuarios', 0)}\n"
                    f"💰 Movimientos: {stats.get('movimientos', 0)}\n"
                    f"🔄 Suscripciones: {stats.get('suscripciones', 0)}\n"
                    f"🔔 Recordatorios: {stats.get('recordatorios', 0)}\n"
                    f"💳 Deudas: {stats.get('deudas', 0)}\n"
                    f"🚨 Alertas: {stats.get('alertas', 0)}\n"
                    f"📂 Categorías: {stats.get('categorias', 0)}"
                )
                
                self.bot.edit_message_text(
                    mensaje,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=self.markup_builder.create_back_to_menu_markup()
                )
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                self.bot.edit_message_text(
                    "❌ Error obteniendo estadísticas",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.markup_builder.create_back_to_menu_markup()
                )
        
        elif data == "config_exportar":
            self.bot.edit_message_text(
                "📄 **Exportar Datos**\n\n"
                "Los backups automáticos se envían diariamente.\n"
                "Puedes solicitar un backup manual escribiendo /backup",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=self.markup_builder.create_back_to_menu_markup()
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
        self.bot.edit_message_text(
            mensaje,
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
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
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
        
        if data.startswith("suscripcion_cat_"):
            # Selección de categoría para suscripción
            categoria = data.replace("suscripcion_cat_", "")
            self._process_subscription_category(call, categoria)
    
    def _handle_debt_action(self, call, data: str):
        """Maneja las acciones relacionadas con deudas"""
        user_id = call.from_user.id
        
        if data.startswith("deuda_tipo_"):
            tipo = data.replace("deuda_tipo_", "")
            self._process_debt_type_selection(call, tipo)
    
    def _handle_alert_action(self, call, data: str):
        """Maneja las acciones relacionadas con alertas"""
        user_id = call.from_user.id
        
        if data.startswith("alerta_tipo_"):
            tipo = data.replace("alerta_tipo_", "")
            self._process_alert_type_selection(call, tipo)
    
    def _handle_menu_navigation(self, call, data: str):
        """Maneja la navegación entre menús"""
        menu_map = {
            "menu_ingresos": self._show_income_menu,
            "menu_gastos": self._show_expense_menu,
            "menu_ahorros": self._show_savings_menu,
            "menu_suscripciones": self._show_subscriptions_menu,
            "menu_recordatorios": self._show_reminders_menu,
            "menu_deudas": self._show_debts_menu,
            "menu_alertas": self._show_alerts_menu,
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
        elif data == "ver_deudas":
            self._show_active_debts(call, user_id)
        elif data == "ver_alertas":
            self._show_active_alerts(call, user_id)
        elif data.startswith("ver_categorias_"):
            tipo = data.replace("ver_categorias_", "")
            self._show_categories_with_totals(call, user_id, tipo)
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
        elif data == "agregar_deuda":
            self._start_add_debt(call, user_id)
        elif data == "agregar_alerta":
            self._start_add_alert(call, user_id)
    
    # ==================== MÉTODOS DE VISUALIZACIÓN ====================
    
    def _show_main_menu(self, call):
        """Muestra el menú principal con balance diario"""
        user_id = call.from_user.id
        
        try:
            # Obtener balance diario
            balance_diario = self.db.obtener_balance_diario(user_id)
            resumen = self.db.obtener_resumen_mes(user_id)
            
            mensaje = self.formatter.format_menu_principal(balance_diario, resumen)
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
        """Muestra el balance completo"""
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
    
    def _show_categories_with_totals(self, call, user_id: int, tipo: str):
        """Muestra categorías con sus totales acumulados"""
        try:
            categorias_con_totales = self.db.obtener_categorias_con_totales(tipo, user_id)
            mensaje = self.formatter.format_categories_by_type(tipo, categorias_con_totales)
            markup = self.markup_builder.create_categories_view_markup(tipo)
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando categorías: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    # ==================== NUEVOS MÉTODOS PARA FUNCIONALIDADES ====================
    
    def _show_debts_menu(self, call):
        """Muestra el menú de deudas"""
        mensaje = self.formatter.format_debts_menu()
        markup = self.markup_builder.create_debts_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_active_debts(self, call, user_id: int):
        """Muestra las deudas activas"""
        try:
            deudas = self.db.obtener_deudas_activas(user_id)
            mensaje = self.formatter.format_active_debts(deudas)
            markup = self.markup_builder.create_debts_view_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando deudas: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    def _show_alerts_menu(self, call):
        """Muestra el menú de alertas"""
        mensaje = self.formatter.format_alerts_menu()
        markup = self.markup_builder.create_alerts_menu_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _show_active_alerts(self, call, user_id: int):
        """Muestra las alertas activas"""
        try:
            alertas = self.db.obtener_alertas_activas(user_id)
            
            if not alertas:
                mensaje = "🚨 **Alertas Activas**\n\n❌ No tienes alertas configuradas"
            else:
                mensaje = f"🚨 **Alertas Activas** ({len(alertas)})\n\n"
                for alerta in alertas:
                    mensaje += f"• Límite {alerta['tipo']}: ${alerta['limite']:,.2f}\n"
            
            markup = self.markup_builder.create_alerts_view_markup()
            
            self.bot.edit_message_text(
                mensaje,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando alertas: {e}")
            self.bot.edit_message_text(
                BotConstants.STATUS_MESSAGES["error"],
                call.message.chat.id,
                call.message.message_id
            )
    
    # ==================== MÉTODOS DE INICIO DE PROCESOS ====================
    
    def _start_add_movement(self, call, user_id: int, tipo: str):
        """Inicia el proceso para agregar un movimiento"""
        try:
            # Obtener categorías del tipo
            categorias = self.db.obtener_categorias(tipo, user_id)
            
            if not categorias:
                # Si no hay categorías, crear algunas básicas
                if tipo == "ingreso":
                    categorias_basicas = ["Salario", "Freelance", "Otros"]
                elif tipo == "gasto":
                    categorias_basicas = ["Comida", "Transporte", "Otros"]
                else:  # ahorro
                    categorias_basicas = ["Ahorro General", "Inversión", "Emergencia"]
                
                for cat in categorias_basicas:
                    self.db.agregar_categoria(cat, tipo, user_id)
                
                categorias = self.db.obtener_categorias(tipo, user_id)
            
            # Crear botones de categorías
            markup = self.markup_builder.create_category_selection_markup(tipo, categorias)
            mensaje = self.formatter.format_category_selection(tipo, True)
            
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
    
    def _start_add_debt(self, call, user_id: int):
        """Inicia el proceso para agregar una deuda"""
        self._set_user_state(user_id, {
            "step": "deuda_nombre",
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        })
        
        mensaje = self.formatter.format_debt_name_request()
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _start_add_alert(self, call, user_id: int):
        """Inicia el proceso para agregar una alerta"""
        mensaje = self.formatter.format_alert_type_selection()
        markup = self.markup_builder.create_alert_type_markup()
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def _process_debt_type_selection(self, call, tipo: str):
        """Procesa la selección del tipo de deuda"""
        user_id = call.from_user.id
        state = self.bot_manager.get_user_state(user_id)
        
        if not state or state.get("step") != "deuda_nombre":
            # Continuar con el flujo normal
            estado_nuevo = {
                "step": "deuda_monto",
                "tipo": tipo,
                "chat_id": call.message.chat.id,
                "message_id": call.message.message_id
            }
            self._set_user_state(user_id, estado_nuevo)
        else:
            # Actualizar estado existente
            state["tipo"] = tipo
            state["step"] = "deuda_monto"
            self._set_user_state(user_id, state)
        
        # Mostrar solicitud de monto
        nombre = state.get("nombre", "") if state else ""
        mensaje = self.formatter.format_debt_amount_request(nombre)
        
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def _process_alert_type_selection(self, call, tipo: str):
        """Procesa la selección del tipo de alerta"""
        user_id = call.from_user.id
        
        self._set_user_state(user_id, {
            "step": "alerta_monto",
            "tipo": tipo,
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        })
        
        mensaje = self.formatter.format_alert_amount_request(tipo)
        self.bot.edit_message_text(
            mensaje,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    # ==================== MÉTODOS EXISTENTES ACTUALIZADOS ====================
    
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
        mensaje = self.formatter.
