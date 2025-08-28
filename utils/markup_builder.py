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
        """Crea el markup del menú principal"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(f"{BotConstants.MONEY} Balance", callback_data="balance_actual"),
            InlineKeyboardButton(f"{BotConstants.CHART} Resumen", callback_data="resumen_mes"),
            InlineKeyboardButton(f"{BotConstants.INCOME} Ingresos", callback_data="menu_ingresos"),
            InlineKeyboardButton(f"{BotConstants.EXPENSE} Gastos", callback_data="menu_gastos"),
            InlineKeyboardButton(f"{BotConstants.SAVINGS} Ahorros", callback_data="menu_ahorros"),
            InlineKeyboardButton("Suscripciones", callback_data="menu_suscripciones"),
            InlineKeyboardButton("Recordatorios", callback_data="menu_recordatorios"),
            InlineKeyboardButton(f"{BotConstants.CHART} Histórico", callback_data="menu_historico"),
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
    def create_categories_setup_markup(tipo: str, categorias_default: List[str]) -> InlineKeyboardMarkup:
        """Crea markup para configurar categorías"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Agregar botones de categorías predefinidas
        for categoria in categorias_default:
            markup.add(
                InlineKeyboardButton(categoria, callback_data=f"add_cat_{tipo}_{categoria}")
            )
        
        # Botones adicionales
        markup.add(
            InlineKeyboardButton("Personalizada", callback_data=f"add_cat_{tipo}_custom")
        )
        
        if tipo == "ingreso":
            markup.add(
                InlineKeyboardButton(f"{BotConstants.SUCCESS} Continuar", callback_data="config_next_gastos")
            )
        else:  # gasto
            markup.add(
                InlineKeyboardButton(f"{BotConstants.SUCCESS} Finalizar", callback_data="config_complete")
            )
        
        return markup
    
    @staticmethod
    def create_movement_menu_markup(tipo: str) -> InlineKeyboardMarkup:
        """Crea markup para menús de movimientos"""
        markup = InlineKeyboardMarkup(row_width=1)
        
        tipo_title = tipo.title()
        markup.add(
            InlineKeyboardButton(f"Agregar {tipo_title}", callback_data=f"agregar_{tipo}"),
            InlineKeyboardButton(f"Ver {tipo_title}s del Mes", callback_data=f"ver_{tipo}s_mes"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        
        return markup
    
    @staticmethod
    def create_category_selection_markup(tipo: str, categorias: List[str]) -> InlineKeyboardMarkup:
        """Crea markup para selección de categoría"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else BotConstants.SAVINGS
        
        for categoria in categorias[:10]:  # Límite de 10 para evitar overflow
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {categoria}", 
                    callback_data=f"select_cat_{tipo}_{categoria}"
                )
            )
        
        markup.add(
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
    def create_subscriptions_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de suscripciones"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton("Ver Suscripciones", callback_data="ver_suscripciones"),
            InlineKeyboardButton("Gestionar", callback_data="gestionar_suscripciones"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_subscriptions_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver suscripciones"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_subscription_category_markup(categorias: List[str]) -> InlineKeyboardMarkup:
        """Crea markup para seleccionar categoría de suscripción"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        for categoria in categorias[:8]:  # Límite para evitar overflow
            markup.add(
                InlineKeyboardButton(categoria, callback_data=f"suscripcion_cat_{categoria}")
            )
        
        return markup
    
    @staticmethod
    def create_subscription_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de crear una suscripción"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton("Ver Suscripciones", callback_data="ver_suscripciones"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_reminders_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de recordatorios"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton("Ver Recordatorios", callback_data="ver_recordatorios"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_reminders_view_markup() -> InlineKeyboardMarkup:
        """Crea markup para ver recordatorios"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_reminder_success_markup() -> InlineKeyboardMarkup:
        """Crea markup para después de crear un recordatorio"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton("Ver Recordatorios", callback_data="ver_recordatorios"),
            InlineKeyboardButton(f"{BotConstants.HOME} Menú Principal", callback_data="back_to_menu")
        )
        return markup
    
    @staticmethod
    def create_config_menu_markup() -> InlineKeyboardMarkup:
        """Crea markup para el menú de configuración"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Gestionar Categorías", callback_data="config_categorias"),
            InlineKeyboardButton("Cambiar Balance Inicial", callback_data="config_balance"),
            InlineKeyboardButton("Ver Configuración", callback_data="ver_configuracion"),
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