"""
Constructor de markups de botones inline optimizado
"""

from typing import List
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import BotConstants

class MarkupBuilder:
    """Clase para construir todos los markups de botones de forma consistente"""
    
    @staticmethod
    def create_main_menu_markup() -> InlineKeyboardMarkup:
        """Crea el markup del menú principal con mejor distribución"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Fila 1: Balance y Resumen
        markup.add(
            InlineKeyboardButton(f"{BotConstants.MONEY} Balance", callback_data="balance_actual"),
            InlineKeyboardButton(f"{BotConstants.CHART} Resumen", callback_data="resumen_mes")
        )
        
        # Fila 2: Ingresos y Gastos
        markup.add(
            InlineKeyboardButton(f"{BotConstants.INCOME} Ingresos", callback_data="menu_ingresos"),
            InlineKeyboardButton(f"{BotConstants.EXPENSE} Gastos", callback_data="menu_gastos")
        )
        
        # Fila 3: Ahorros y Suscripciones
        markup.add(
            InlineKeyboardButton("💳 Ahorros", callback_data="menu_ahorros"),
            InlineKeyboardButton("🔄 Suscripciones", callback_data="menu_suscripciones")
        )
        
        # Fila 4: Recordatorios y Deudas
        markup.add(
            InlineKeyboardButton("🔔 Recordatorios", callback_data="menu_recordatorios"),
            InlineKeyboardButton("💰 Deudas", callback_data="menu_deudas")
        )
        
        # Fila 5: Alertas e Histórico
        markup.add(
            InlineKeyboardButton("🚨 Alertas", callback_data="menu_alertas"),
            InlineKeyboardButton("📊 Histórico", callback_data="menu_historico")
        )
        
        # Fila 6: Configuración (centrada)
        markup.add(
            InlineKeyboardButton(f"{BotConstants.SETTINGS} Configurar", callback_data="menu_configuracion")
        )
        
        return markup
    
    @staticmethod
    def create_back_to_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para volver al menú principal"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu"))
        return markup
    
    @staticmethod
    def create_movement_menu_markup(tipo: str) -> InlineKeyboardMarkup:
        """Crea markup para menús de movimientos"""
        markup = InlineKeyboardMarkup(row_width=1)
        
        tipo_title = tipo.title()
        markup.add(
            InlineKeyboardButton(f"Agregar {tipo_title}", callback_data=f"agregar_{tipo}"),
            InlineKeyboardButton(f"Ver {tipo_title}s del Mes", callback_data=f"ver_{tipo}s_mes"),
            InlineKeyboardButton(f"Ver Categorías", callback_data=f"ver_categorias_{tipo}"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        
        return markup
    
    @staticmethod
    def create_category_selection_markup(tipo: str, categorias: List[str]) -> InlineKeyboardMarkup:
        """Crea markup para selección de categoría con opción de agregar nueva"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
        
        for categoria in categorias[:12]:  # Límite de 12 para evitar overflow
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {categoria}", 
                    callback_data=f"select_cat_{tipo}_{categoria}"
                )
            )
        
        # Botón para agregar nueva categoría
        markup.add(
            InlineKeyboardButton("✨ Nueva Categoría", callback_data=f"nueva_categoria_{tipo}")
        )
        
        markup.add(
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        
        return markup
    
    @staticmethod
    def create_categories_view_markup(tipo: str) -> InlineKeyboardMarkup:
        """Crea markup para ver categorías con totales"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✨ Nueva Categoría", callback_data=f"nueva_categoria_{tipo}"),
            InlineKeyboardButton(f"Agregar {tipo.title()}", callback_data=f"agregar_{tipo}"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_movement_success_markup(tipo: str) -> InlineKeyboardMarkup:
        """Crea markup para después de registrar un movimiento exitosamente"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            InlineKeyboardButton(f"Agregar Otro {tipo.title()}", callback_data=f"agregar_{tipo}"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        
        return markup
    
    @staticmethod
    def create_summary_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de resumen"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Ver Ingresos", callback_data="ver_ingresos_mes"),
            InlineKeyboardButton("Ver Gastos", callback_data="ver_gastos_mes"),
            InlineKeyboardButton("Ver Ahorros", callback_data="ver_ahorros_mes"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    # ==================== SUSCRIPCIONES ====================
    
    @staticmethod
    def create_subscriptions_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de suscripciones"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔄 Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton("📋 Ver Suscripciones", callback_data="ver_suscripciones"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_subscriptions_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver suscripciones"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔄 Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_subscription_category_markup(categorias: List[str]) -> InlineKeyboardMarkup:
        """Crea markup para seleccionar categoría de suscripción"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        for categoria in categorias[:10]:  # Límite para evitar overflow
            markup.add(
                InlineKeyboardButton(categoria, callback_data=f"suscripcion_cat_{categoria}")
            )
        
        markup.add(
            InlineKeyboardButton("❌ Cancelar", callback_data="back_to_menu")
        )
        
        return markup
    
    @staticmethod
    def create_subscription_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de crear una suscripción"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔄 Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton("📋 Ver Suscripciones", callback_data="ver_suscripciones"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    # ==================== RECORDATORIOS ====================
    
    @staticmethod
    def create_reminders_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de recordatorios"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔔 Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton("📋 Ver Recordatorios", callback_data="ver_recordatorios"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_reminders_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver recordatorios"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔔 Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_reminder_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de crear un recordatorio"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔔 Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton("📋 Ver Recordatorios", callback_data="ver_recordatorios"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    # ==================== DEUDAS ====================
    
    @staticmethod
    def create_debts_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de deudas"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💰 Nueva Deuda", callback_data="agregar_deuda"),
            InlineKeyboardButton("📋 Ver Deudas", callback_data="ver_deudas"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_debts_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver deudas"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("💰 Nueva Deuda", callback_data="agregar_deuda"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_debt_type_markup() -> InlineKeyboardMarkup:
        """Crea markup para seleccionar tipo de deuda"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📈 Me deben", callback_data="deuda_tipo_positiva"),
            InlineKeyboardButton("📉 Yo debo", callback_data="deuda_tipo_negativa"),
            InlineKeyboardButton("❌ Cancelar", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_debt_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de registrar una deuda"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💰 Nueva Deuda", callback_data="agregar_deuda"),
            InlineKeyboardButton("📋 Ver Deudas", callback_data="ver_deudas"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    # ==================== ALERTAS ====================
    
    @staticmethod
    def create_alerts_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de alertas"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🚨 Nueva Alerta", callback_data="agregar_alerta"),
            InlineKeyboardButton("📋 Ver Alertas", callback_data="ver_alertas"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_alert_type_markup() -> InlineKeyboardMarkup:
        """Crea markup para seleccionar tipo de alerta"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📅 Límite Diario", callback_data="alerta_tipo_diario"),
            InlineKeyboardButton("📊 Límite Mensual", callback_data="alerta_tipo_mensual"),
            InlineKeyboardButton("❌ Cancelar", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_alerts_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver alertas"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🚨 Nueva Alerta", callback_data="agregar_alerta"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_alert_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de crear una alerta"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🚨 Nueva Alerta", callback_data="agregar_alerta"),
            InlineKeyboardButton("📋 Ver Alertas", callback_data="ver_alertas"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    # ==================== CONFIGURACIÓN ====================
    
    @staticmethod
    def create_config_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de configuración mejorado SIN exportar datos"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💰 Cambiar Balance Inicial", callback_data="config_balance_inicial"),
            InlineKeyboardButton("📊 Estadísticas del Bot", callback_data="config_estadisticas"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_cancel_markup() -> InlineKeyboardMarkup:
        """Crea markup para cancelar operación"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("❌ Cancelar", callback_data="back_to_menu")
        )
        return markup
