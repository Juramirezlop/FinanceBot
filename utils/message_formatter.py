"""
Formateador de mensajes para el bot - centraliza todos los textos
"""

from config.settings import BotConstants

class MessageFormatter:
    """Clase para formatear todos los mensajes del bot de forma consistente"""
    
    def format_balance(self, balance: float) -> str:
        """Formatea el mensaje de balance actual"""
        return f"{BotConstants.MONEY} **Balance Actual**\n${balance:,.2f}"
    
    def format_daily_balance(self, balance_diario: dict) -> str:
        """Formatea el balance diario para el menú principal"""
        return (
            f"{BotConstants.MONEY} Balance Hoy: **${balance_diario['balance_actual']:,.2f}**\n"
            f"📅 Movimientos de Hoy:\n"
            f"   {BotConstants.INCOME} +${balance_diario['ingresos_hoy']:,.2f}\n"
            f"   {BotConstants.EXPENSE} -${balance_diario['gastos_hoy']:,.2f}"
        )
    
    def format_menu_principal(self, balance_diario: dict, resumen: dict) -> str:
        """Formatea el mensaje del menú principal con balance diario REAL"""
        # Mostrar solo los movimientos del DÍA, no el balance total
        balance_dia = balance_diario['ingresos_hoy'] - balance_diario['gastos_hoy'] - balance_diario['ahorros_hoy']
        
        return (
            f"{BotConstants.MONEY} **Mi Centro Financiero Personal**\n\n"
            f"📅 **Hoy ({date.today().strftime('%d/%m/%Y')}):**\n"
            f"   {BotConstants.INCOME} Ingresos: ${balance_diario['ingresos_hoy']:,.2f}\n"
            f"   {BotConstants.EXPENSE} Gastos: ${balance_diario['gastos_hoy']:,.2f}\n"
            f"   💳 Ahorros: ${balance_diario['ahorros_hoy']:,.2f}\n"
            f"   📊 Balance del día: ${balance_dia:,.2f}\n\n"
            f"{BotConstants.CHART} **Este Mes:**\n"
            f"   {BotConstants.INCOME} Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   {BotConstants.EXPENSE} Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💳 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"¿Qué deseas hacer?"
        )
    
    def format_resumen_mensual(self, resumen: dict, balance: float) -> str:
        """Formatea el resumen mensual básico"""
        return (
            f"{BotConstants.CHART} **Resumen {resumen['mes']:02d}/{resumen['año']}**\n\n"
            f"{BotConstants.MONEY} Balance Total: ${balance:,.2f}\n\n"
            f"{BotConstants.CHART} Movimientos del Mes:\n"
            f"   {BotConstants.INCOME} Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   {BotConstants.EXPENSE} Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💳 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"{BotConstants.INFO} Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}"
        )
    
    def format_ayuda(self) -> str:
        """Formatea el mensaje de ayuda actualizado"""
        return (
            "**🤖 Bot de Finanzas Personales - Guía Completa**\n\n"
            "**📱 Comandos Rápidos:**\n"
            "`/start` - Menú principal\n"
            "`/balance` - Ver balance total\n"
            "`/gasto 5000 almuerzo` - Registro rápido\n"
            "`/ingreso 50000 salario` - Registro rápido\n"
            "`/resumen` - Resumen del mes\n"
            "`/backup` - Generar backup manual\n\n"
            "**✨ Funcionalidades Principales:**\n"
            f"💰 **Balance Diario** - Ve movimientos del día en el menú\n"
            f"{BotConstants.INCOME} **Ingresos** - Categorías personalizables\n"
            f"{BotConstants.EXPENSE} **Gastos** - Control total con alertas\n"
            f"💳 **Ahorros** - Separados de gastos\n"
            f"🔄 **Suscripciones** - Descuentos automáticos mensuales\n"
            f"🔔 **Recordatorios** - Alertas de pagos importantes\n"
            f"💰 **Deudas** - Controla quién te debe y a quién debes\n"
            f"🚨 **Alertas** - Límites diarios y mensuales de gastos\n"
            f"📊 **Histórico** - Análisis de últimos 6 meses\n\n"
            "**🎯 Tips de Uso:**\n"
            "• Las **categorías se crean automáticamente** al agregar movimientos\n"
            "• Escribe **'no'** para omitir descripciones\n"
            "• Los **ahorros se descuentan** del balance (no son gastos)\n"
            "• Las **suscripciones se cobran automáticamente** cada mes\n"
            "• Configura **alertas de límites** para controlar gastos\n"
            "• Usa **Ver Categorías** para ver totales acumulados\n\n"
            "**🔄 ¿Necesitas ayuda?**\n"
            "Envía `/start` para volver al menú principal"
        )
    
    def format_bienvenida_configuracion(self) -> str:
        """Formatea el mensaje de bienvenida para configuración inicial"""
        return (
            f"**¡Bienvenido a tu Bot de Finanzas Personales!**\n\n"
            "Para comenzar, ingresa tu balance inicial (puede ser 0):\n\n"
            f"{BotConstants.MONEY} **Ejemplo:** 100000 o 0"
        )
    
    def format_movement_menu(self, tipo: str) -> str:
        """Formatea el menú de gestión de movimientos"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
        titulo = tipo.title() + "s"
        
        return f"{emoji} **Gestión de {titulo}**\n\n¿Qué deseas hacer?"
    
    def format_category_selection(self, tipo: str, show_add_category: bool = True) -> str:
        """Formatea el mensaje para seleccionar categoría"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
        mensaje = f"{emoji} **Agregar {tipo.title()}**\n\nSelecciona una categoría:"
        
        if show_add_category:
            mensaje += f"\n\n{BotConstants.INFO} *Puedes crear nuevas categorías desde aquí*"
        
        return mensaje
    
    def format_amount_request(self, tipo: str, categoria: str, emoji: str) -> str:
        """Formatea la solicitud de monto"""
        return (
            f"{emoji} **{tipo.title()}: {categoria}**\n\n"
            f"{BotConstants.MONEY} Ingresa el monto (solo números):\n"
            f"**Ejemplo:** 50000 o 50000.50"
        )
    
    def format_description_request(self, tipo: str, categoria: str, monto: float, emoji: str) -> str:
        """Formatea la solicitud de descripción"""
        return (
            f"{emoji} **{tipo.title()}: {categoria}**\n"
            f"{BotConstants.MONEY} Monto: ${monto:,.2f}\n\n"
            f"Ingresa una descripción (opcional):\n"
            f"Escribe **'no'** para omitir"
        )
    
    def format_movement_success(self, tipo: str, categoria: str, monto: float, 
                               descripcion: str, nuevo_balance: float) -> str:
        """Formatea el mensaje de éxito al registrar movimiento"""
        emoji = BotConstants.INCOME if tipo == "ingreso" else BotConstants.EXPENSE if tipo == "gasto" else "💳"
        
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
            f"**Uso:** /{tipo} 5000 descripción\n"
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
    
    def format_categories_by_type(self, tipo: str, categorias_con_totales: list) -> str:
        """Formatea las categorías con sus totales acumulados"""
        emoji_map = {
            "ingreso": BotConstants.INCOME,
            "gasto": BotConstants.EXPENSE,
            "ahorro": "💳"
        }
        emoji = emoji_map.get(tipo, BotConstants.MONEY)
        
        mensaje = f"{emoji} **Categorías de {tipo.title()}s**\n\n"
        
        if not categorias_con_totales:
            mensaje += f"❌ No hay categorías de {tipo}s registradas"
        else:
            for categoria in categorias_con_totales:
                mensaje += f"• **{categoria['nombre']}**: ${categoria['total']:,.2f}\n"
        
        return mensaje
    
    # ==================== SUSCRIPCIONES ====================
    
    def format_subscriptions_menu(self) -> str:
        """Formatea el menú de suscripciones"""
        return "🔄 **Suscripciones Automáticas**\n\nGestiona tus pagos recurrentes que se descuentan automáticamente cada mes."
    
    def format_subscription_name_request(self) -> str:
        """Solicita el nombre de la suscripción"""
        return (
            "🔄 **Nueva Suscripción**\n\n"
            "Ingresa el nombre de la suscripción:\n"
            "**Ejemplos:** Netflix, Spotify, Gym, Internet"
        )
    
    def format_subscription_amount_request(self, nombre: str) -> str:
        """Solicita el monto de la suscripción"""
        return (
            f"🔄 **Suscripción: {nombre}**\n\n"
            f"{BotConstants.MONEY} Ingresa el monto mensual:\n"
            "**Ejemplo:** 15000 o 9.99"
        )
    
    def format_subscription_category_selection(self, state: dict) -> str:
        """Formatea la selección de categoría para suscripción"""
        return (
            f"🔄 **Suscripción: {state.get('nombre', '')}**\n"
            f"{BotConstants.MONEY} Monto: ${state.get('monto', 0):,.2f}\n\n"
            "Selecciona la categoría de gasto:"
        )
    
    def format_subscription_day_request(self, state: dict) -> str:
        """Solicita el día de cobro de la suscripción"""
        return (
            f"🔄 **Suscripción: {state.get('nombre', '')}**\n"
            f"{BotConstants.MONEY} Monto: ${state.get('monto', 0):,.2f}\n"
            f"🏷️ Categoría: {state.get('categoria', '')}\n\n"
            "¿Qué día del mes se cobra?\n"
            "**Ingresa un número del 1 al 31**"
        )
    
    def format_subscription_success(self, nombre: str, monto: float, categoria: str, dia: int) -> str:
        """Formatea el mensaje de éxito al crear suscripción"""
        return (
            f"{BotConstants.SUCCESS} **Suscripción Creada**\n\n"
            f"🔄 **{nombre}**\n"
            f"{BotConstants.MONEY} Monto: ${monto:,.2f}\n"
            f"🏷️ Categoría: {categoria}\n"
            f"📅 Día de cobro: {dia}\n\n"
            f"Se cobrará automáticamente cada mes el día {dia}"
        )
    
    def format_active_subscriptions(self, suscripciones: list) -> str:
        """Formatea las suscripciones activas"""
        if not suscripciones:
            return "🔄 **Suscripciones Activas**\n\n❌ No tienes suscripciones registradas"
        
        mensaje = f"🔄 **Suscripciones Activas** ({len(suscripciones)})\n\n"
        total_mensual = 0
        
        for sub in suscripciones:
            total_mensual += sub['monto']
            mensaje += (
                f"• **{sub['nombre']}**\n"
                f"  💰 ${sub['monto']:,.2f} - Día {sub['dia_cobro']}\n"
                f"  🏷️ {sub['categoria']}\n\n"
            )
        
        mensaje += f"💳 **Total mensual: ${total_mensual:,.2f}**"
        return mensaje
    
    # ==================== RECORDATORIOS ====================
    
    def format_reminders_menu(self) -> str:
        """Formatea el menú de recordatorios"""
        return "🔔 **Recordatorios**\n\nConfigura alertas para pagos importantes y gestiona recordatorios automáticos de suscripciones."
    
    def format_reminder_description_request(self) -> str:
        """Solicita la descripción del recordatorio"""
        return (
            "🔔 **Nuevo Recordatorio**\n\n"
            "Ingresa la descripción del recordatorio:\n"
            "**Ejemplos:** Pagar tarjeta de crédito, Renovar documento, Comprar medicinas"
        )
    
    def format_reminder_date_request(self) -> str:
        """Solicita la fecha del recordatorio"""
        return (
            "🔔 **Fecha del Recordatorio**\n\n"
            "Ingresa la fecha (DD/MM/YYYY o DD/MM):\n"
            "**Ejemplos:** 15/03/2024 o 15/03"
        )
    
    def format_reminder_success(self, descripcion: str, fecha) -> str:
        """Formatea el mensaje de éxito al crear recordatorio"""
        from datetime import datetime
        fecha_str = fecha.strftime("%d/%m/%Y") if hasattr(fecha, 'strftime') else str(fecha)
        
        return (
            f"{BotConstants.SUCCESS} **Recordatorio Creado**\n\n"
            f"🔔 **{descripcion}**\n"
            f"📅 Fecha: {fecha_str}\n\n"
            f"Recibirás una notificación ese día"
        )
    
    def format_active_reminders(self, recordatorios: list) -> str:
        """Formatea los recordatorios activos"""
        if not recordatorios:
            return "🔔 **Recordatorios Activos**\n\n❌ No tienes recordatorios pendientes"
        
        mensaje = f"🔔 **Recordatorios Activos** ({len(recordatorios)})\n\n"
        
        for recordatorio in recordatorios:
            fecha_str = recordatorio.get('fecha_vencimiento', '')
            mensaje += (
                f"• **{recordatorio['descripcion']}**\n"
                f"  📅 {fecha_str}\n\n"
            )
        
        return mensaje
    
    # ==================== DEUDAS ====================
    
    def format_debts_menu(self) -> str:
        """Formatea el menú de deudas"""
        return "💳 **Control de Deudas**\n\nRegistra y gestiona las deudas que tienes con otras personas o entidades."
    
    def format_debt_name_request(self) -> str:
        """Solicita el nombre de la deuda"""
        return (
            "💳 **Nueva Deuda**\n\n"
            "¿A quién le debes o quién te debe?\n"
            "**Ejemplos:** Juan, Banco Nacional, María, Tienda XYZ"
        )
    
    def format_debt_amount_request(self, nombre: str) -> str:
        """Solicita el monto de la deuda"""
        return (
            f"💳 **Deuda con: {nombre}**\n\n"
            f"{BotConstants.MONEY} Ingresa el monto:\n"
            "**Número positivo:** Te deben\n"
            "**Número negativo:** Tú debes\n\n"
            "**Ejemplos:** 50000 (te deben) o -25000 (tú debes)"
        )
    
    def format_debt_success(self, nombre: str, monto: float, tipo: str) -> str:
        """Formatea el mensaje de éxito al registrar deuda"""
        emoji = "📈" if monto > 0 else "📉"
        accion = "te debe" if monto > 0 else "le debes"
        
        return (
            f"{BotConstants.SUCCESS} **Deuda Registrada**\n\n"
            f"{emoji} **{nombre}** {accion}\n"
            f"{BotConstants.MONEY} ${abs(monto):,.2f}\n\n"
            f"Tipo: {tipo}"
        )
    
    def format_active_debts(self, deudas: list) -> str:
        """Formatea las deudas activas"""
        if not deudas:
            return "💳 **Deudas Activas**\n\n✅ No tienes deudas registradas"
        
        mensaje = "💳 **Control de Deudas**\n\n"
        deudas_a_favor = []
        deudas_en_contra = []
        
        for deuda in deudas:
            if deuda['monto'] > 0:
                deudas_a_favor.append(deuda)
            else:
                deudas_en_contra.append(deuda)
        
        if deudas_a_favor:
            mensaje += "📈 **Te deben:**\n"
            for deuda in deudas_a_favor:
                mensaje += f"• {deuda['nombre']}: ${deuda['monto']:,.2f}\n"
            mensaje += "\n"
        
        if deudas_en_contra:
            mensaje += "📉 **Tú debes:**\n"
            for deuda in deudas_en_contra:
                mensaje += f"• {deuda['nombre']}: ${abs(deuda['monto']):,.2f}\n"
        
        return mensaje
    
    # ==================== ALERTAS ====================
    
    def format_alerts_menu(self) -> str:
        """Formatea el menú de alertas"""
        return (
            "🚨 **Sistema de Alertas**\n\n"
            "Configura límites de gastos y recibe notificaciones automáticas cuando los superes."
        )
    
    def format_alert_type_selection(self) -> str:
        """Solicita el tipo de alerta"""
        return (
            "🚨 **Nueva Alerta**\n\n"
            "¿Qué tipo de límite quieres configurar?"
        )
    
    def format_alert_amount_request(self, tipo: str) -> str:
        """Solicita el monto límite para la alerta"""
        periodo = "diario" if tipo == "diario" else "mensual"
        return (
            f"🚨 **Alerta {tipo.title()}**\n\n"
            f"Ingresa el límite {periodo} de gastos:\n"
            f"**Ejemplo:** 50000 (${50000:,.2f})"
        )
    
    def format_alert_success(self, tipo: str, monto: float) -> str:
        """Formatea el mensaje de éxito al crear alerta"""
        return (
            f"{BotConstants.SUCCESS} **Alerta Configurada**\n\n"
            f"🚨 Límite {tipo}: ${monto:,.2f}\n\n"
            f"Recibirás una notificación si superas este límite"
        )
    
    def format_limit_exceeded_alert(self, tipo: str, limite: float, gastado: float) -> str:
        """Formatea alerta de límite superado"""
        return (
            f"🚨 **¡LÍMITE SUPERADO!**\n\n"
            f"Has excedido tu límite {tipo}:\n"
            f"🎯 Límite: ${limite:,.2f}\n"
            f"💸 Gastado: ${gastado:,.2f}\n"
            f"📊 Exceso: ${gastado - limite:,.2f}\n\n"
            f"💡 *Controla tus gastos para mantener tu presupuesto*"
        )
    
    def create_main_menu_markup(self):
        """Crea el markup del menú principal"""
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        markup = InlineKeyboardMarkup(row_width=2)
        # Fila 1
        markup.add(
            InlineKeyboardButton(f"{BotConstants.MONEY} Balance", callback_data="balance_actual"),
            InlineKeyboardButton(f"{BotConstants.CHART} Resumen", callback_data="resumen_mes")
        )
        # Fila 2
        markup.add(
            InlineKeyboardButton(f"{BotConstants.INCOME} Ingresos", callback_data="menu_ingresos"),
            InlineKeyboardButton(f"{BotConstants.EXPENSE} Gastos", callback_data="menu_gastos")
        )
        # Fila 3
        markup.add(
            InlineKeyboardButton("💳 Ahorros", callback_data="menu_ahorros"),
            InlineKeyboardButton("🔄 Suscripciones", callback_data="menu_suscripciones")
        )
        # Fila 4
        markup.add(
            InlineKeyboardButton("🔔 Recordatorios", callback_data="menu_recordatorios"),
            InlineKeyboardButton("💳 Deudas", callback_data="menu_deudas")
        )
        # Fila 5
        markup.add(
            InlineKeyboardButton("🚨 Alertas", callback_data="menu_alertas"),
            InlineKeyboardButton("📊 Histórico", callback_data="menu_historico")
        )
        # Fila 6 (configuración centrada)
        markup.add(
            InlineKeyboardButton(f"{BotConstants.SETTINGS} Configurar", callback_data="menu_configuracion")
        )
        return markup
    
    def format_resumen_detallado(self, resumen, balance_actual, resumen_anterior):
        """Formatea resumen detallado con comparación"""
        diferencia = balance_actual - resumen_anterior.get("balance", 0)
        emoji_diferencia = "📈" if diferencia >= 0 else "📉"
        
        return (
            f"📊 **Resumen {resumen['mes']:02d}/{resumen['año']}**\n\n"
            f"💰 Balance Total: **${balance_actual:,.2f}**\n"
            f"{emoji_diferencia} Cambio vs mes anterior: ${diferencia:,.2f}\n\n"
            f"📈 **Movimientos del Mes:**\n"
            f"   💵 Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   💸 Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💳 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"💡 Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}"
        )

    def format_month_movements(self, movimientos, tipo):
        """Formatea movimientos del mes por tipo"""
        emoji_map = {"ingreso": "💵", "gasto": "💸", "ahorro": "💳"}
        emoji = emoji_map.get(tipo, "💰")
        titulo = tipo.title() + "s"
        
        if not movimientos:
            return f"{emoji} **{titulo} del Mes**\n\n❌ No hay {tipo}s registrados este mes."
        
        texto = f"{emoji} **{titulo} del Mes**\n\n"
        total = 0
        
        for mov in movimientos[:10]:
            total += mov['monto']
            fecha_str = mov['fecha']
            
            texto += f"**{mov['categoria']}** - ${mov['monto']:,.2f}\n"
            if mov['descripcion']:
                texto += f"   {fecha_str} - {mov['descripcion']}\n\n"
            else:
                texto += f"   {fecha_str}\n\n"
        
        if len(movimientos) > 10:
            texto += f"... y {len(movimientos) - 10} más\n\n"
        
        texto += f"💰 **Total: ${total:,.2f}**"
        return texto

    def format_historical_data(self, historico):
        """Formatea datos históricos"""
        if not historico:
            return "📈 **Histórico Financiero**\n\nAún no hay datos históricos."
        
        texto = "📈 **Histórico Financiero**\n\n"
        
        for resumen in historico:
            neto = resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']
            emoji = "📈" if neto >= 0 else "📉"
            
            texto += (
                f"{emoji} **{resumen['mes']:02d}/{resumen['año']}**\n"
                f"   Balance: ${resumen['balance']:,.2f}\n"
                f"   Neto: ${neto:,.2f}\n\n"
            )
        
        return texto
    
    def format_new_category_request(self, tipo: str) -> str:
        """Solicita nueva categoría personalizada"""
        return (
            f"✨ **Nueva Categoría de {tipo.title()}**\n\n"
            "Ingresa el nombre de la nueva categoría:\n"
            "**Máximo 50 caracteres**"
        )
