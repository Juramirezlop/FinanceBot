"""
Formateador de mensajes para el bot - centraliza todos los textos
"""

from config.settings import BotConstants

class MessageFormatter:
    """Clase para formatear todos los mensajes del bot de forma consistente"""
    
    def format_balance(self, balance: float) -> str:
        """Formatea el mensaje de balance actual"""
        return f"{BotConstants.MONEY} **Balance Actual**\n${balance:,.2f}"
    
    def format_menu_principal(self, balance: float, resumen: dict) -> str:
        """Formatea el mensaje del menú principal"""
        return (
            f"{BotConstants.MONEY} **Mi Centro Financiero Personal**\n\n"
            f"{BotConstants.MONEY} Balance Actual: **${balance:,.2f}**\n"
            f"{BotConstants.CHART} Este Mes:\n"
            f"   {BotConstants.INCOME} Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   {BotConstants.EXPENSE} Gastos: ${resumen['gastos']:,.2f}\n"
            f"   {BotConstants.SAVINGS} Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"¿Qué deseas hacer?"
        )
    
    def format_resumen_mensual(self, resumen: dict, balance: float) -> str:
        """Formatea el resumen mensual básico"""
        return (
            f"{BotConstants.CHART} **Resumen {resumen['mes']:02d}/{resumen['año']}**\n\n"
            f"{BotConstants.MONEY} Balance Actual: ${balance:,.2f}\n\n"
            f"{BotConstants.CHART} Movimientos del Mes:\n"
            f"   {BotConstants.INCOME} Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   {BotConstants.EXPENSE} Gastos: ${resumen['gastos']:,.2f}\n"
            f"   {BotConstants.SAVINGS} Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"{BotConstants.INFO} Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}"
        )
    
    def format_ayuda(self) -> str:
        """Formatea el mensaje de ayuda"""
        return (
            "**Bot de Finanzas Personales - Guía**\n\n"
            "**Comandos Principales:**\n"
            "/start - Menú principal\n"
            "/balance - Ver balance actual\n"
            "/gasto 5000 descripción - Registro rápido\n"
            "/ingreso 50000 descripción - Registro rápido\n"
            "/resumen - Resumen del mes\n"
            "/config - Configuración\n\n"
            "**Funcionalidades:**\n"
            f"{BotConstants.SUCCESS} Balance en tiempo real\n"
            f"{BotConstants.SUCCESS} Categorías personalizables\n"
            f"{BotConstants.SUCCESS} Suscripciones automáticas\n"
            f"{BotConstants.SUCCESS} Histórico mensual\n"
            f"{BotConstants.SUCCESS} Recordatorios\n"
            f"{BotConstants.SUCCESS} Análisis de gastos\n\n"
            f"{BotConstants.INFO} **Tip:** Los ahorros se descuentan del balance pero no son gastos"
        )
    
    def format_bienvenida_configuracion(self) -> str:
        """Formatea el mensaje de bienvenida para configuración inicial"""
        return (
            f"**¡Bienvenido a tu Bot de Finanzas Personales!**\n\n"
            "Para comenzar, necesito configurar tu perfil financiero.\n\n"
            f"{BotConstants.MONEY} Primero, ingresa tu balance inicial (puede ser 0):"
        )
    
    def format_categorias_setup(self, tipo: str) -> str:
        """Formatea el mensaje para configurar categorías"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE
        titulo = "INGRESOS" if tipo == "ingreso" else "GASTOS"
        
        return (
            f"{emoji} **CONFIGURACIÓN: Categorías de {titulo.title()}**\n\n"
            f"Selecciona las categorías que usarás para tus {tipo}s.\n"
            "Puedes agregar tantas como necesites:"
        )
    
    def format_movement_menu(self, tipo: str) -> str:
        """Formatea el menú de gestión de movimientos"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else BotConstants.SAVINGS
        titulo = tipo.title() + "s"
        
        return f"{emoji} **Gestión de {titulo}**\n\n¿Qué deseas hacer?"
    
    def format_category_selection(self, tipo: str) -> str:
        """Formatea el mensaje para seleccionar categoría"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else BotConstants.SAVINGS
        return f"{emoji} **Agregar {tipo.title()}**\n\nSelecciona una categoría:"
    
    def format_amount_request(self, tipo: str, categoria: str, emoji: str) -> str:
        """Formatea la solicitud de monto"""
        return (
            f"{emoji} **{tipo.title()}: {categoria}**\n\n"
            f"{BotConstants.MONEY} Ingresa el monto (solo números):\n"
            f"Ejemplo: 50000 o 50000.50"
        )
    
    def format_description_request(self, tipo: str, categoria: str, monto: float, emoji: str) -> str:
        """Formatea la solicitud de descripción"""
        return (
            f"{emoji} **{tipo.title()}: {categoria}**\n"
            f"{BotConstants.MONEY} Monto: ${monto:,.2f}\n\n"
            f"Ingresa una descripción (opcional):\n"
            f"Puedes escribir 'sin descripcion' para omitir"
        )
    
    def format_movement_success(self, tipo: str, categoria: str, monto: float, 
                               descripcion: str, nuevo_balance: float) -> str:
        """Formatea el mensaje de éxito al registrar movimiento"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else BotConstants.SAVINGS
        
        return (
            f"{BotConstants.SUCCESS} **{tipo.title()} Registrado**\n\n"
            f"{emoji} Categoría: {categoria}\n"
            f"{BotConstants.MONEY} Monto: ${monto:,.2f}\n"
            f"Descripción: {descripcion or 'Sin descripción'}\n\n"
            f"{BotConstants.MONEY} **Nuevo balance: ${nuevo_balance:,.2f}**"
        )
    
    def format_error_comando_rapido(self, tipo: str) -> str:
        """Formatea mensaje de error para comando rápido"""
        return (
            f"{BotConstants.ERROR} Formato inválido.\n"
            f"Uso: /{tipo} 5000 descripción\n"
            f"O simplemente /{tipo} para usar el menú interactivo"
        )
    
    def format_movimiento_registrado(self, tipo: str, categoria: str, monto: float, 
                                   descripcion: str, balance: float) -> str:
        """Formatea mensaje de movimiento registrado (comando rápido)"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE
        
        return (
            f"{BotConstants.SUCCESS} {tipo.title()} registrado:\n"
            f"{emoji} ${monto:,.2f} - {descripcion}\n"
            f"{BotConstants.MONEY} Nuevo balance: ${balance:,.2f}"
        )
    
    def format_config_menu(self) -> str:
        """Formatea el menú de configuración"""
        return (
            f"{BotConstants.SETTINGS} **Configuración**\n\n"
            "Personaliza tu experiencia financiera:"
        )
    
    def create_main_menu_markup(self):
        """Crea el markup del menú principal"""
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(f"{BotConstants.MONEY} Balance", callback_data="balance_actual"),
            InlineKeyboardButton(f"{BotConstants.CHART} Resumen", callback_data="resumen_mes"),
            InlineKeyboardButton(f"{BotConstants.INCOME} Ingresos", callback_data="menu_ingresos"),
            InlineKeyboardButton(f"{BotConstants.EXPENSE} Gastos", callback_data="menu_gastos"),
            InlineKeyboardButton(f"{BotConstants.SAVINGS} Ahorros", callback_data="menu_ahorros"),
            InlineKeyboardButton("Suscripciones", callback_data="menu_suscripciones"),
            InlineKeyboardButton(f"{BotConstants.SETTINGS} Configurar", callback_data="menu_configuracion")
        )
        return markup