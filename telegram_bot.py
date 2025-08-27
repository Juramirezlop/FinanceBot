"""
Bot de Telegram para Economía Personal Avanzado
Autor: Juan David Ramirez
Versión: 1.0
Descripción: Bot completo para manejo de finanzas personales con categorías,
            suscripciones, recordatorios y análisis mensual.
"""

import sqlite3
import logging
import schedule
import time
import threading
import csv
from datetime import datetime, date
from typing import Dict, List, Tuple
import os
from dataclasses import dataclass
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== CONFIGURACIÓN ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID"))
bot = telebot.TeleBot(BOT_TOKEN)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finance_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== MODELOS DE DATOS ====================

@dataclass
class Usuario:
    user_id: int
    balance_inicial: float
    fecha_creacion: datetime
    configurado: bool = False

@dataclass
class Categoria:
    id: int
    nombre: str
    tipo: str  # 'ingreso' o 'gasto'
    activa: bool
    user_id: int

@dataclass
class Movimiento:
    id: int
    fecha: date
    tipo: str  # 'ingreso', 'gasto', 'ahorro'
    categoria: str
    monto: float
    descripcion: str
    mes: int
    año: int
    user_id: int

@dataclass
class Suscripcion:
    id: int
    nombre: str
    monto: float
    categoria: str
    dia_cobro: int
    activo: bool
    proximo_cobro: date
    user_id: int

# ==================== BASE DE DATOS ====================

class DatabaseManager:
    def __init__(self, db_path: str = "finanzas.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa todas las tablas de la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    user_id INTEGER PRIMARY KEY,
                    balance_inicial REAL DEFAULT 0,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    configurado BOOLEAN DEFAULT 0
                )
            ''')
            
            # Tabla categorías de ingresos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias_ingresos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    activa BOOLEAN DEFAULT 1,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla categorías de gastos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias_gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    activa BOOLEAN DEFAULT 1,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla presupuestos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS presupuestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT NOT NULL,
                    limite_mensual REAL NOT NULL,
                    mes INTEGER NOT NULL,
                    año INTEGER NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla movimientos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    tipo TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    monto REAL NOT NULL,
                    descripcion TEXT,
                    mes INTEGER NOT NULL,
                    año INTEGER NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla suscripciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suscripciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    monto REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    dia_cobro INTEGER NOT NULL,
                    activo BOOLEAN DEFAULT 1,
                    proximo_cobro DATE NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla recordatorios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recordatorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT NOT NULL,
                    monto REAL,
                    fecha_vencimiento DATE NOT NULL,
                    activo BOOLEAN DEFAULT 1,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
                )
            ''')
            
            # Tabla resumen mensual
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resumen_mensual (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mes INTEGER NOT NULL,
                    año INTEGER NOT NULL,
                    total_ingresos REAL DEFAULT 0,
                    total_gastos REAL DEFAULT 0,
                    total_ahorros REAL DEFAULT 0,
                    balance_final REAL DEFAULT 0,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (user_id),
                    UNIQUE(mes, año, user_id)
                )
            ''')
            
            conn.commit()
            logger.info("Base de datos inicializada correctamente")
    
    def crear_usuario(self, user_id: int, balance_inicial: float = 0.0) -> bool:
        """Crea un nuevo usuario"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO usuarios (user_id, balance_inicial, configurado)
                    VALUES (?, ?, 0)
                ''', (user_id, balance_inicial))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return False
    
    def usuario_existe(self, user_id: int) -> bool:
        """Verifica si un usuario existe"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM usuarios WHERE user_id = ?', (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando usuario: {e}")
            return False
    
    def usuario_configurado(self, user_id: int) -> bool:
        """Verifica si un usuario está configurado"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT configurado FROM usuarios WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Error verificando configuración: {e}")
            return False
    
    def marcar_usuario_configurado(self, user_id: int):
        """Marca un usuario como configurado"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE usuarios SET configurado = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error marcando usuario configurado: {e}")
    
    def agregar_categoria(self, nombre: str, tipo: str, user_id: int) -> bool:
        """Agrega una nueva categoría"""
        try:
            tabla = f"categorias_{tipo}s"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT INTO {tabla} (nombre, user_id) VALUES (?, ?)
                ''', (nombre, user_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error agregando categoría: {e}")
            return False
    
    def obtener_categorias(self, tipo: str, user_id: int) -> List[str]:
        """Obtiene las categorías activas de un tipo"""
        try:
            tabla = f"categorias_{tipo}s"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT nombre FROM {tabla} 
                    WHERE user_id = ? AND activa = 1
                    ORDER BY nombre
                ''', (user_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return []
    
    def agregar_movimiento(self, user_id: int, tipo: str, categoria: str, 
                          monto: float, descripcion: str = "") -> bool:
        """Agrega un nuevo movimiento"""
        try:
            hoy = date.today()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO movimientos 
                    (fecha, tipo, categoria, monto, descripcion, mes, año, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (hoy, tipo, categoria, monto, descripcion, hoy.month, hoy.year, user_id))
                conn.commit()
                
                # Actualizar resumen mensual
                self._actualizar_resumen_mensual(user_id, hoy.month, hoy.year)
                return True
        except Exception as e:
            logger.error(f"Error agregando movimiento: {e}")
            return False
    
    def _actualizar_resumen_mensual(self, user_id: int, mes: int, año: int):
        """Actualiza el resumen mensual basado en los movimientos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calcular totales del mes
                cursor.execute('''
                    SELECT tipo, SUM(monto) FROM movimientos 
                    WHERE user_id = ? AND mes = ? AND año = ?
                    GROUP BY tipo
                ''', (user_id, mes, año))
                
                totales = {"ingreso": 0, "gasto": 0, "ahorro": 0}
                for tipo, total in cursor.fetchall():
                    totales[tipo] = total or 0
                
                # Obtener balance inicial
                cursor.execute('SELECT balance_inicial FROM usuarios WHERE user_id = ?', (user_id,))
                balance_inicial = cursor.fetchone()[0] or 0
                
                # Calcular balance final (acumulativo)
                cursor.execute('''
                    SELECT SUM(CASE WHEN tipo = 'ingreso' THEN monto 
                                   WHEN tipo = 'gasto' THEN -monto 
                                   WHEN tipo = 'ahorro' THEN -monto 
                                   ELSE 0 END) as balance_acumulado
                    FROM movimientos 
                    WHERE user_id = ? AND (año < ? OR (año = ? AND mes <= ?))
                ''', (user_id, año, año, mes))
                
                balance_movimientos = cursor.fetchone()[0] or 0
                balance_final = balance_inicial + balance_movimientos
                
                # Insertar o actualizar resumen
                cursor.execute('''
                    INSERT OR REPLACE INTO resumen_mensual 
                    (mes, año, total_ingresos, total_gastos, total_ahorros, balance_final, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (mes, año, totales["ingreso"], totales["gasto"], 
                     totales["ahorro"], balance_final, user_id))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando resumen mensual: {e}")
    
    def obtener_balance_actual(self, user_id: int) -> float:
        """Calcula el balance actual del usuario"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener balance inicial
                cursor.execute('SELECT balance_inicial FROM usuarios WHERE user_id = ?', (user_id,))
                balance_inicial = cursor.fetchone()[0] or 0
                
                # Calcular todos los movimientos
                cursor.execute('''
                    SELECT SUM(CASE WHEN tipo = 'ingreso' THEN monto 
                                   WHEN tipo = 'gasto' THEN -monto 
                                   WHEN tipo = 'ahorro' THEN -monto 
                                   ELSE 0 END) as total_movimientos
                    FROM movimientos WHERE user_id = ?
                ''', (user_id,))
                
                total_movimientos = cursor.fetchone()[0] or 0
                return balance_inicial + total_movimientos
        except Exception as e:
            logger.error(f"Error calculando balance: {e}")
            return 0.0
    
    def obtener_resumen_mes(self, user_id: int, mes: int = None, año: int = None) -> Dict:
        """Obtiene el resumen de un mes específico"""
        if not mes or not año:
            hoy = date.today()
            mes, año = hoy.month, hoy.year
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT total_ingresos, total_gastos, total_ahorros, balance_final
                    FROM resumen_mensual 
                    WHERE user_id = ? AND mes = ? AND año = ?
                ''', (user_id, mes, año))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "mes": mes,
                        "año": año,
                        "ingresos": result[0] or 0,
                        "gastos": result[1] or 0,
                        "ahorros": result[2] or 0,
                        "balance": result[3] or 0
                    }
                else:
                    # Si no hay resumen, crearlo
                    self._actualizar_resumen_mensual(user_id, mes, año)
                    return self.obtener_resumen_mes(user_id, mes, año)
        except Exception as e:
            logger.error(f"Error obteniendo resumen mensual: {e}")
            return {"mes": mes, "año": año, "ingresos": 0, "gastos": 0, "ahorros": 0, "balance": 0}
    
    def agregar_suscripcion(self, user_id: int, nombre: str, monto: float, 
                           categoria: str, dia_cobro: int) -> bool:
        """Agrega una nueva suscripción"""
        try:
            # Calcular próximo cobro
            hoy = date.today()
            if dia_cobro <= hoy.day:
                # Próximo mes
                if hoy.month == 12:
                    proximo_cobro = date(hoy.year + 1, 1, dia_cobro)
                else:
                    proximo_cobro = date(hoy.year, hoy.month + 1, dia_cobro)
            else:
                # Este mes
                proximo_cobro = date(hoy.year, hoy.month, dia_cobro)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO suscripciones 
                    (nombre, monto, categoria, dia_cobro, proximo_cobro, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (nombre, monto, categoria, dia_cobro, proximo_cobro, user_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error agregando suscripción: {e}")
            return False
    
    def obtener_suscripciones_pendientes(self) -> List[Tuple]:
        """Obtiene suscripciones que deben cobrarse hoy"""
        try:
            hoy = date.today()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nombre, monto, categoria, user_id
                    FROM suscripciones 
                    WHERE activo = 1 AND proximo_cobro <= ?
                ''', (hoy,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error obteniendo suscripciones pendientes: {e}")
            return []
    
    def procesar_suscripcion(self, suscripcion_id: int) -> bool:
        """Procesa el cobro de una suscripción"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener datos de la suscripción
                cursor.execute('''
                    SELECT nombre, monto, categoria, dia_cobro, user_id
                    FROM suscripciones WHERE id = ?
                ''', (suscripcion_id,))
                
                suscripcion = cursor.fetchone()
                if not suscripcion:
                    return False
                
                nombre, monto, categoria, dia_cobro, user_id = suscripcion
                
                # Registrar el gasto
                hoy = date.today()
                cursor.execute('''
                    INSERT INTO movimientos 
                    (fecha, tipo, categoria, monto, descripcion, mes, año, user_id)
                    VALUES (?, 'gasto', ?, ?, ?, ?, ?, ?)
                ''', (hoy, categoria, monto, f"Suscripción: {nombre}", hoy.month, hoy.year, user_id))
                
                # Actualizar próximo cobro
                if hoy.month == 12:
                    proximo_cobro = date(hoy.year + 1, 1, dia_cobro)
                else:
                    proximo_cobro = date(hoy.year, hoy.month + 1, dia_cobro)
                
                cursor.execute('''
                    UPDATE suscripciones SET proximo_cobro = ? WHERE id = ?
                ''', (proximo_cobro, suscripcion_id))
                
                conn.commit()
                
                # Actualizar resumen mensual
                self._actualizar_resumen_mensual(user_id, hoy.month, hoy.year)
                return True
        except Exception as e:
            logger.error(f"Error procesando suscripción: {e}")
            return False

# ==================== BOT DE TELEGRAM ====================

class FinanceBot:
    def __init__(self, token: str, authorized_user: int):
        self.bot = telebot.TeleBot(token)
        self.authorized_user = authorized_user
        self.db = DatabaseManager()
        self.user_states = {}  # Para manejar estados de conversación
        self.setup_handlers()
        
    def setup_handlers(self):
        """Configura todos los manejadores del bot"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.command_start(message)
        
        @self.bot.message_handler(commands=['balance'])
        def handle_balance(message):
            self.command_balance(message)
        
        @self.bot.message_handler(commands=['gasto'])
        def handle_gasto(message):
            self.command_gasto_rapido(message)
        
        @self.bot.message_handler(commands=['ingreso'])
        def handle_ingreso(message):
            self.command_ingreso_rapido(message)
        
        @self.bot.message_handler(commands=['resumen'])
        def handle_resumen(message):
            self.command_resumen(message)
        
        @self.bot.message_handler(commands=['config'])
        def handle_config(message):
            self.command_config(message)
        
        @self.bot.message_handler(commands=['ayuda'])
        def handle_ayuda(message):
            self.command_ayuda(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.handle_callback_query(call)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            self.handle_text_input(message)
    
    def is_authorized(self, user_id: int) -> bool:
        """Verifica si el usuario está autorizado"""
        return user_id == self.authorized_user
    
    def command_start(self, message):
        """Comando /start - Punto de entrada principal"""
        if not self.is_authorized(message.from_user.id):
            self.bot.reply_to(message, "❌ No tienes permisos para usar este bot.")
            return
        
        user_id = message.from_user.id
        
        # Verificar si es usuario nuevo
        if not self.db.usuario_existe(user_id):
            self.iniciar_wizard_configuracion(message)
        elif not self.db.usuario_configurado(user_id):
            self.continuar_wizard_configuracion(message)
        else:
            self.mostrar_menu_principal(message)
    
    def iniciar_wizard_configuracion(self, message):
        """Inicia el wizard de configuración para usuarios nuevos"""
        user_id = message.from_user.id
        self.db.crear_usuario(user_id)
        
        self.bot.send_message(
            message.chat.id,
            "🎉 ¡Bienvenido a tu Bot de Finanzas Personales!\n\n"
            "Para comenzar, necesito configurar tu perfil financiero.\n\n"
            "💰 Primero, ingresa tu balance inicial (puede ser 0):"
        )
        
        self.user_states[user_id] = {"step": "balance_inicial"}
    
    def continuar_wizard_configuracion(self, message):
        """Continúa el wizard de configuración"""
        self.mostrar_paso_configuracion(message)
    
    def mostrar_paso_configuracion(self, message, paso_actual: str = None):
        """Muestra el paso actual del wizard de configuración"""
        user_id = message.from_user.id
        
        if not paso_actual:
            # Determinar paso actual basado en configuración existente
            categorias_ingreso = self.db.obtener_categorias("ingreso", user_id)
            categorias_gasto = self.db.obtener_categorias("gasto", user_id)
            
            if not categorias_ingreso:
                paso_actual = "categorias_ingreso"
            elif not categorias_gasto:
                paso_actual = "categorias_gasto"
            else:
                # Configuración completa
                self.db.marcar_usuario_configurado(user_id)
                self.mostrar_menu_principal(message)
                return
        
        if paso_actual == "categorias_ingreso":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("💼 Salario", callback_data="add_cat_ingreso_Salario"),
                InlineKeyboardButton("💰 Freelance", callback_data="add_cat_ingreso_Freelance"),
                InlineKeyboardButton("🏪 Negocio", callback_data="add_cat_ingreso_Negocio"),
                InlineKeyboardButton("📈 Inversiones", callback_data="add_cat_ingreso_Inversiones"),
                InlineKeyboardButton("🎁 Otros", callback_data="add_cat_ingreso_Otros"),
                InlineKeyboardButton("➕ Personalizada", callback_data="add_cat_ingreso_custom"),
                InlineKeyboardButton("✅ Continuar", callback_data="config_next_gastos")
            )
            
            self.bot.send_message(
                message.chat.id,
                "💵 **CONFIGURACIÓN: Categorías de Ingresos**\n\n"
                "Selecciona las categorías que usarás para tus ingresos.\n"
                "Puedes agregar tantas como necesites:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        
        elif paso_actual == "categorias_gasto":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🏠 Vivienda", callback_data="add_cat_gasto_Vivienda"),
                InlineKeyboardButton("🍽️ Comida", callback_data="add_cat_gasto_Comida"),
                InlineKeyboardButton("🚗 Transporte", callback_data="add_cat_gasto_Transporte"),
                InlineKeyboardButton("👔 Ropa", callback_data="add_cat_gasto_Ropa"),
                InlineKeyboardButton("🏥 Salud", callback_data="add_cat_gasto_Salud"),
                InlineKeyboardButton("🎮 Entretenimiento", callback_data="add_cat_gasto_Entretenimiento"),
                InlineKeyboardButton("📚 Educación", callback_data="add_cat_gasto_Educación"),
                InlineKeyboardButton("💡 Servicios", callback_data="add_cat_gasto_Servicios"),
                InlineKeyboardButton("➕ Personalizada", callback_data="add_cat_gasto_custom"),
                InlineKeyboardButton("✅ Finalizar Config", callback_data="config_complete")
            )
            
            self.bot.send_message(
                message.chat.id,
                "💸 **CONFIGURACIÓN: Categorías de Gastos**\n\n"
                "Selecciona las categorías para tus gastos.\n"
                "Estas te ayudarán a organizar mejor tu dinero:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
    
    def mostrar_menu_principal(self, message):
        """Muestra el menú principal del bot"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("💰 Balance Actual", callback_data="balance_actual"),
            InlineKeyboardButton("📊 Resumen Mes", callback_data="resumen_mes"),
            InlineKeyboardButton("💵 Ingresos", callback_data="menu_ingresos"),
            InlineKeyboardButton("💸 Gastos", callback_data="menu_gastos"),
            InlineKeyboardButton("💳 Ahorros", callback_data="menu_ahorros"),
            InlineKeyboardButton("🔄 Suscripciones", callback_data="menu_suscripciones"),
            InlineKeyboardButton("🔔 Recordatorios", callback_data="menu_recordatorios"),
            InlineKeyboardButton("📈 Histórico", callback_data="menu_historico"),
            InlineKeyboardButton("⚙️ Configurar", callback_data="menu_configuracion")
        )
        
        balance = self.db.obtener_balance_actual(message.from_user.id)
        resumen = self.db.obtener_resumen_mes(message.from_user.id)
        
        texto = (
            f"💰 **Mi Centro Financiero Personal**\n\n"
            f"💵 Balance Actual: **${balance:,.2f}**\n"
            f"📊 Este Mes:\n"
            f"   ↗️ Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   ↘️ Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💰 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"¿Qué deseas hacer?"
        )
        
        self.bot.send_message(message.chat.id, texto, reply_markup=markup, parse_mode="Markdown")
    
    def handle_callback_query(self, call):
        """Maneja todas las respuestas de botones inline"""
        if not self.is_authorized(call.from_user.id):
            self.bot.answer_callback_query(call.id, "❌ No autorizado")
            return
        
        data = call.data
        user_id = call.from_user.id
        
        # Configuración inicial - Agregar categorías
        if data.startswith("add_cat_"):
            parts = data.split("_", 3)
            tipo = parts[2]  # ingreso o gasto
            
            if len(parts) > 3:
                categoria = parts[3]
                self.db.agregar_categoria(categoria, tipo, user_id)
                self.bot.answer_callback_query(call.id, f"✅ Categoría '{categoria}' agregada")
            else:  # custom
                self.bot.answer_callback_query(call.id, "Escribe el nombre de la categoría personalizada:")
                self.user_states[user_id] = {"step": f"custom_category_{tipo}"}
        
        # Navegación del wizard
        elif data == "config_next_gastos":
            self.mostrar_paso_configuracion(call.message, "categorias_gasto")
        
        elif data == "config_complete":
            self.db.marcar_usuario_configurado(user_id)
            self.bot.edit_message_text(
                "🎉 ¡Configuración completada!\n\nYa puedes usar todas las funciones del bot.",
                call.message.chat.id,
                call.message.message_id
            )
            self.mostrar_menu_principal(call.message)
        
        # Menú principal
        elif data == "balance_actual":
            balance = self.db.obtener_balance_actual(user_id)
            self.bot.edit_message_text(
                f"💰 **Balance Actual**\n\n${balance:,.2f}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=self.get_back_to_menu_markup()
            )
        
        elif data == "resumen_mes":
            self.mostrar_resumen_mensual(call)
        
        elif data == "menu_ingresos":
            self.mostrar_menu_ingresos(call)
        
        elif data == "menu_gastos":
            self.mostrar_menu_gastos(call)
        
        elif data == "menu_ahorros":
            self.mostrar_menu_ahorros(call)
        
        elif data == "menu_suscripciones":
            self.mostrar_menu_suscripciones(call)
        
        elif data == "menu_recordatorios":
            self.mostrar_menu_recordatorios(call)
        
        elif data == "menu_historico":
            self.mostrar_menu_historico(call)
        
        elif data == "menu_configuracion":
            self.mostrar_menu_configuracion(call)
        
        elif data == "back_to_menu":
            self.bot.edit_message_text(
                "💰 **Mi Centro Financiero Personal**",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            self.mostrar_menu_principal(call.message)
        
        # Menú de ingresos
        elif data == "agregar_ingreso":
            self.iniciar_agregar_movimiento(call, "ingreso")
        
        # Menú de gastos
        elif data == "agregar_gasto":
            self.iniciar_agregar_movimiento(call, "gasto")
        
        # Menú de ahorros
        elif data == "agregar_ahorro":
            self.iniciar_agregar_movimiento(call, "ahorro")
        
        # Selección de categoría para movimientos
        elif data.startswith("select_cat_"):
            parts = data.split("_", 3)
            tipo = parts[2]
            categoria = parts[3]
            self.procesar_seleccion_categoria(call, tipo, categoria)
        
        # Suscripciones
        elif data == "agregar_suscripcion":
            self.iniciar_agregar_suscripcion(call)
        
        elif data == "ver_suscripciones":
            self.mostrar_suscripciones_activas(call)
        
        self.bot.answer_callback_query(call.id)
    
    def get_back_to_menu_markup(self):
        """Retorna markup para volver al menú principal"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu"))
        return markup
    
    def mostrar_resumen_mensual(self, call):
        """Muestra el resumen del mes actual"""
        user_id = call.from_user.id
        resumen = self.db.obtener_resumen_mes(user_id)
        balance_actual = self.db.obtener_balance_actual(user_id)
        
        # Calcular diferencia vs mes anterior
        mes_anterior = resumen["mes"] - 1 if resumen["mes"] > 1 else 12
        año_anterior = resumen["año"] if resumen["mes"] > 1 else resumen["año"] - 1
        resumen_anterior = self.db.obtener_resumen_mes(user_id, mes_anterior, año_anterior)
        
        diferencia = balance_actual - resumen_anterior["balance"]
        emoji_diferencia = "📈" if diferencia >= 0 else "📉"
        
        texto = (
            f"📊 **Resumen {resumen['mes']}/{resumen['año']}**\n\n"
            f"💰 Balance Actual: **${balance_actual:,.2f}**\n"
            f"{emoji_diferencia} Cambio vs mes anterior: ${diferencia:,.2f}\n\n"
            f"📈 **Movimientos del Mes:**\n"
            f"   ↗️ Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   ↘️ Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💰 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"💡 **Análisis:**\n"
            f"   Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📈 Ver Histórico", callback_data="menu_historico"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            texto,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_ingresos(self, call):
        """Muestra el menú de ingresos"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Ingreso", callback_data="agregar_ingreso"),
            InlineKeyboardButton("📊 Ver Ingresos del Mes", callback_data="ver_ingresos_mes"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "💵 **Gestión de Ingresos**\n\n"
            "¿Qué deseas hacer?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_gastos(self, call):
        """Muestra el menú de gastos"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Gasto", callback_data="agregar_gasto"),
            InlineKeyboardButton("📊 Ver Gastos del Mes", callback_data="ver_gastos_mes"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "💸 **Gestión de Gastos**\n\n"
            "¿Qué deseas hacer?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_ahorros(self, call):
        """Muestra el menú de ahorros"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Ahorro", callback_data="agregar_ahorro"),
            InlineKeyboardButton("📊 Ver Ahorros del Mes", callback_data="ver_ahorros_mes"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "💳 **Gestión de Ahorros**\n\n"
            "Los ahorros se restan de tu balance pero no son gastos.\n"
            "¿Qué deseas hacer?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_suscripciones(self, call):
        """Muestra el menú de suscripciones"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Nueva Suscripción", callback_data="agregar_suscripcion"),
            InlineKeyboardButton("👁️ Ver Suscripciones", callback_data="ver_suscripciones"),
            InlineKeyboardButton("⚙️ Gestionar", callback_data="gestionar_suscripciones"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "🔄 **Suscripciones Automáticas**\n\n"
            "Gestiona tus pagos recurrentes que se descuentan automáticamente.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_recordatorios(self, call):
        """Muestra el menú de recordatorios"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Nuevo Recordatorio", callback_data="agregar_recordatorio"),
            InlineKeyboardButton("👁️ Ver Recordatorios", callback_data="ver_recordatorios"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "🔔 **Recordatorios**\n\n"
            "Configura alertas para pagos importantes.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_historico(self, call):
        """Muestra el menú del histórico"""
        user_id = call.from_user.id
        
        # Obtener últimos 6 meses
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mes, año, total_ingresos, total_gastos, total_ahorros, balance_final
                FROM resumen_mensual 
                WHERE user_id = ? 
                ORDER BY año DESC, mes DESC 
                LIMIT 6
            ''', (user_id,))
            
            historico = cursor.fetchall()
        
        if not historico:
            texto = "📈 **Histórico Financiero**\n\nAún no hay datos históricos."
        else:
            texto = "📈 **Histórico Financiero**\n\n"
            for mes, año, ingresos, gastos, ahorros, balance in historico:
                neto = ingresos - gastos - ahorros
                emoji = "📈" if neto >= 0 else "📉"
                texto += (
                    f"{emoji} **{mes:02d}/{año}**\n"
                    f"   Balance: ${balance:,.2f}\n"
                    f"   Neto: ${neto:,.2f}\n\n"
                )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu"))
        
        self.bot.edit_message_text(
            texto,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def mostrar_menu_configuracion(self, call):
        """Muestra el menú de configuración"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏷️ Gestionar Categorías", callback_data="config_categorias"),
            InlineKeyboardButton("💰 Cambiar Balance Inicial", callback_data="config_balance"),
            InlineKeyboardButton("📊 Ver Configuración", callback_data="ver_configuracion"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
        )
        
        self.bot.edit_message_text(
            "⚙️ **Configuración**\n\n"
            "Personaliza tu experiencia financiera:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    def iniciar_agregar_movimiento(self, call, tipo: str):
        """Inicia el proceso para agregar un movimiento"""
        user_id = call.from_user.id
        
        # Obtener categorías según el tipo
        if tipo == "ingreso":
            categorias = self.db.obtener_categorias("ingreso", user_id)
            titulo = "💵 Agregar Ingreso"
            emoji = "💵"
        elif tipo == "gasto":
            categorias = self.db.obtener_categorias("gasto", user_id)
            titulo = "💸 Agregar Gasto"
            emoji = "💸"
        else:  # ahorro
            # Para ahorros usamos las mismas categorías que gastos
            categorias = ["Ahorro Programado", "Inversión", "Emergencia", "Meta Específica"]
            titulo = "💳 Agregar Ahorro"
            emoji = "💳"
        
        if not categorias:
            self.bot.edit_message_text(
                f"{titulo}\n\n❌ No tienes categorías configuradas.\n"
                "Ve a Configuración para agregar categorías.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.get_back_to_menu_markup()
            )
            return
        
        # Crear botones de categorías
        markup = InlineKeyboardMarkup(row_width=2)
        for categoria in categorias:
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {categoria}", 
                    callback_data=f"select_cat_{tipo}_{categoria}"
                )
            )
        markup.add(InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu"))
        
        self.bot.edit_message_text(
            f"{titulo}\n\nSelecciona una categoría:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def procesar_seleccion_categoria(self, call, tipo: str, categoria: str):
        """Procesa la selección de categoría y pide el monto"""
        user_id = call.from_user.id
        
        # Guardar estado
        self.user_states[user_id] = {
            "step": f"monto_{tipo}",
            "tipo": tipo,
            "categoria": categoria,
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }
        
        emoji = {"ingreso": "💵", "gasto": "💸", "ahorro": "💳"}[tipo]
        
        self.bot.edit_message_text(
            f"{emoji} **{tipo.title()}: {categoria}**\n\n"
            f"💰 Ingresa el monto (solo números):\n"
            f"Ejemplo: 50000 o 50000.50",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def iniciar_agregar_suscripcion(self, call):
        """Inicia el proceso para agregar una suscripción"""
        user_id = call.from_user.id
        
        self.user_states[user_id] = {
            "step": "suscripcion_nombre",
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }
        
        self.bot.edit_message_text(
            "🔄 **Nueva Suscripción**\n\n"
            "📝 Ingresa el nombre de la suscripción:\n"
            "Ejemplo: Netflix, Spotify, Gimnasio, etc.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def mostrar_suscripciones_activas(self, call):
        """Muestra las suscripciones activas del usuario"""
        user_id = call.from_user.id
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT nombre, monto, categoria, dia_cobro, proximo_cobro
                    FROM suscripciones 
                    WHERE user_id = ? AND activo = 1
                    ORDER BY dia_cobro
                ''', (user_id,))
                
                suscripciones = cursor.fetchall()
            
            if not suscripciones:
                texto = "🔄 **Suscripciones Activas**\n\n❌ No tienes suscripciones configuradas."
            else:
                texto = "🔄 **Suscripciones Activas**\n\n"
                total_mensual = 0
                
                for nombre, monto, categoria, dia_cobro, proximo_cobro in suscripciones:
                    total_mensual += monto
                    fecha_cobro = datetime.strptime(proximo_cobro, '%Y-%m-%d').date()
                    dias_restantes = (fecha_cobro - date.today()).days
                    
                    if dias_restantes <= 0:
                        estado = "🔴 Hoy"
                    elif dias_restantes <= 3:
                        estado = f"🟡 {dias_restantes}d"
                    else:
                        estado = f"🟢 {dias_restantes}d"
                    
                    texto += (
                        f"💳 **{nombre}**\n"
                        f"   💰 ${monto:,.2f} - {categoria}\n"
                        f"   📅 Día {dia_cobro} - {estado}\n\n"
                    )
                
                texto += f"💰 **Total mensual: ${total_mensual:,.2f}**"
            
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("➕ Nueva Suscripción", callback_data="agregar_suscripcion"),
                InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
            )
            
            self.bot.edit_message_text(
                texto,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except Exception as e:
            logger.error(f"Error mostrando suscripciones: {e}")
            self.bot.edit_message_text(
                "❌ Error al obtener suscripciones.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.get_back_to_menu_markup()
            )
    
    def handle_text_input(self, message):
        """Maneja las entradas de texto del usuario"""
        if not self.is_authorized(message.from_user.id):
            return
        
        user_id = message.from_user.id
        
        if user_id not in self.user_states:
            # No hay estado activo, mostrar ayuda
            self.bot.reply_to(message, 
                "❓ No entiendo ese mensaje.\n"
                "Usa /start para ver el menú principal o /ayuda para más información."
            )
            return
        
        state = self.user_states[user_id]
        step = state.get("step")
        
        if step == "balance_inicial":
            self.procesar_balance_inicial(message)
        
        elif step == "custom_category_ingreso" or step == "custom_category_gasto":
            self.procesar_categoria_personalizada(message, step)
        
        elif step.startswith("monto_"):
            self.procesar_monto_movimiento(message)
        
        elif step == "descripcion_movimiento":
            self.procesar_descripcion_movimiento(message)
        
        elif step == "suscripcion_nombre":
            self.procesar_nombre_suscripcion(message)
        
        elif step == "suscripcion_monto":
            self.procesar_monto_suscripcion(message)
        
        elif step == "suscripcion_dia":
            self.procesar_dia_suscripcion(message)
    
    def procesar_balance_inicial(self, message):
        """Procesa el balance inicial ingresado por el usuario"""
        try:
            balance = float(message.text.replace(",", "").replace("$", ""))
            user_id = message.from_user.id
            
            # Actualizar balance en base de datos
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE usuarios SET balance_inicial = ? WHERE user_id = ?',
                    (balance, user_id)
                )
                conn.commit()
            
            # Limpiar estado y continuar configuración
            del self.user_states[user_id]
            
            self.bot.reply_to(
                message,
                f"✅ Balance inicial configurado: ${balance:,.2f}\n\n"
                "Continuemos con la configuración de categorías..."
            )
            
            self.mostrar_paso_configuracion(message, "categorias_ingreso")
            
        except ValueError:
            self.bot.reply_to(
                message,
                "❌ Por favor ingresa un número válido.\n"
                "Ejemplo: 100000 o 0 si empiezas desde cero"
            )
    
    def procesar_categoria_personalizada(self, message, step):
        """Procesa una categoría personalizada"""
        nombre_categoria = message.text.strip()
        tipo = step.split("_")[-1]  # ingreso o gasto
        user_id = message.from_user.id
        
        if len(nombre_categoria) < 2:
            self.bot.reply_to(message, "❌ El nombre debe tener al menos 2 caracteres.")
            return
        
        if self.db.agregar_categoria(nombre_categoria, tipo, user_id):
            del self.user_states[user_id]
            self.bot.reply_to(
                message,
                f"✅ Categoría '{nombre_categoria}' agregada correctamente."
            )
            # Volver a mostrar el paso de configuración correspondiente
            paso = "categorias_ingreso" if tipo == "ingreso" else "categorias_gasto"
            self.mostrar_paso_configuracion(message, paso)
        else:
            self.bot.reply_to(message, "❌ Error agregando la categoría. Intenta de nuevo.")
    
    def procesar_monto_movimiento(self, message):
        """Procesa el monto de un movimiento"""
        try:
            monto = float(message.text.replace(",", "").replace("$", ""))
            if monto <= 0:
                raise ValueError("El monto debe ser positivo")
            
            user_id = message.from_user.id
            state = self.user_states[user_id]
            
            # Actualizar estado con el monto
            state["monto"] = monto
            state["step"] = "descripcion_movimiento"
            
            emoji = {"ingreso": "💵", "gasto": "💸", "ahorro": "💳"}[state["tipo"]]
            
            self.bot.send_message(
                message.chat.id,
                f"{emoji} **{state['tipo'].title()}: {state['categoria']}**\n"
                f"💰 Monto: ${monto:,.2f}\n\n"
                f"📝 Ingresa una descripción (opcional):\n"
                f"Puedes escribir 'sin descripcion' para omitir",
                parse_mode="Markdown"
            )
            
        except ValueError:
            self.bot.reply_to(
                message,
                "❌ Por favor ingresa un número válido mayor a 0.\n"
                "Ejemplo: 50000 o 25.50"
            )
    
    def procesar_descripcion_movimiento(self, message):
        """Procesa la descripción de un movimiento y lo guarda"""
        user_id = message.from_user.id
        state = self.user_states[user_id]
        
        descripcion = message.text.strip()
        if descripcion.lower() == "sin descripcion":
            descripcion = ""
        
        # Guardar el movimiento
        exito = self.db.agregar_movimiento(
            user_id,
            state["tipo"],
            state["categoria"],
            state["monto"],
            descripcion
        )
        
        if exito:
            emoji = {"ingreso": "💵", "gasto": "💸", "ahorro": "💳"}[state["tipo"]]
            nuevo_balance = self.db.obtener_balance_actual(user_id)
            
            mensaje_exito = (
                f"✅ **{state['tipo'].title()} Registrado**\n\n"
                f"{emoji} Categoría: {state['categoria']}\n"
                f"💰 Monto: ${state['monto']:,.2f}\n"
                f"📝 Descripción: {descripcion or 'Sin descripción'}\n\n"
                f"💰 **Nuevo balance: ${nuevo_balance:,.2f}**"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("➕ Agregar Otro", callback_data=f"menu_{state['tipo']}s"),
                InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
            )
            
            self.bot.send_message(
                message.chat.id,
                mensaje_exito,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            self.bot.reply_to(message, "❌ Error guardando el movimiento. Intenta de nuevo.")
        
        # Limpiar estado
        del self.user_states[user_id]
    
    def procesar_nombre_suscripcion(self, message):
        """Procesa el nombre de una suscripción"""
        nombre = message.text.strip()
        user_id = message.from_user.id
        
        if len(nombre) < 2:
            self.bot.reply_to(message, "❌ El nombre debe tener al menos 2 caracteres.")
            return
        
        # Actualizar estado
        self.user_states[user_id]["nombre"] = nombre
        self.user_states[user_id]["step"] = "suscripcion_monto"
        
        self.bot.reply_to(
            message,
            f"🔄 **Suscripción: {nombre}**\n\n"
            f"💰 Ingresa el monto mensual:\n"
            f"Ejemplo: 15000 o 9.99"
        )
    
    def procesar_monto_suscripcion(self, message):
        """Procesa el monto de una suscripción"""
        try:
            monto = float(message.text.replace(",", "").replace("$", ""))
            if monto <= 0:
                raise ValueError("El monto debe ser positivo")
            
            user_id = message.from_user.id
            state = self.user_states[user_id]
            
            # Actualizar estado
            state["monto"] = monto
            state["step"] = "suscripcion_categoria"
            
            # Mostrar categorías de gasto para seleccionar
            categorias = self.db.obtener_categorias("gasto", user_id)
            
            if not categorias:
                self.bot.reply_to(
                    message,
                    "❌ No tienes categorías de gasto configuradas.\n"
                    "Ve a Configuración para agregar categorías."
                )
                del self.user_states[user_id]
                return
            
            markup = InlineKeyboardMarkup(row_width=2)
            for categoria in categorias:
                markup.add(
                    InlineKeyboardButton(
                        categoria,
                        callback_data=f"suscripcion_cat_{categoria}"
                    )
                )
            
            self.bot.send_message(
                message.chat.id,
                f"🔄 **Suscripción: {state['nombre']}**\n"
                f"💰 Monto: ${monto:,.2f}\n\n"
                f"🏷️ Selecciona una categoría:",
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        except ValueError:
            self.bot.reply_to(
                message,
                "❌ Por favor ingresa un número válido mayor a 0.\n"
                "Ejemplo: 15000 o 9.99"
            )
    
    def procesar_dia_suscripcion(self, message):
        """Procesa el día de cobro de una suscripción"""
        try:
            dia = int(message.text.strip())
            if dia < 1 or dia > 31:
                raise ValueError("Día inválido")
            
            user_id = message.from_user.id
            state = self.user_states[user_id]
            
            # Guardar la suscripción
            exito = self.db.agregar_suscripcion(
                user_id,
                state["nombre"],
                state["monto"],
                state["categoria"],
                dia
            )
            
            if exito:
                # Calcular próximo cobro para mostrar
                hoy = date.today()
                if dia <= hoy.day:
                    if hoy.month == 12:
                        proximo_cobro = date(hoy.year + 1, 1, dia)
                    else:
                        proximo_cobro = date(hoy.year, hoy.month + 1, dia)
                else:
                    proximo_cobro = date(hoy.year, hoy.month, dia)
                
                mensaje_exito = (
                    f"✅ **Suscripción Creada**\n\n"
                    f"🔄 Nombre: {state['nombre']}\n"
                    f"💰 Monto: ${state['monto']:,.2f}\n"
                    f"🏷️ Categoría: {state['categoria']}\n"
                    f"📅 Día de cobro: {dia}\n"
                    f"🗓️ Próximo cobro: {proximo_cobro.strftime('%d/%m/%Y')}\n\n"
                    f"El bot cobrará automáticamente esta suscripción cada mes."
                )
                
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("➕ Nueva Suscripción", callback_data="agregar_suscripcion"),
                    InlineKeyboardButton("👁️ Ver Suscripciones", callback_data="ver_suscripciones"),
                    InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")
                )
                
                self.bot.send_message(
                    message.chat.id,
                    mensaje_exito,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                self.bot.reply_to(message, "❌ Error guardando la suscripción. Intenta de nuevo.")
            
            # Limpiar estado
            del self.user_states[user_id]
            
        except ValueError:
            self.bot.reply_to(
                message,
                "❌ Por favor ingresa un número válido entre 1 y 31.\n"
                "Ejemplo: 15 (para el día 15 de cada mes)"
            )
    
    # Manejador adicional para selección de categoría de suscripción
    def handle_suscripcion_categoria(self, call, categoria):
        """Maneja la selección de categoría para suscripción"""
        user_id = call.from_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        state["categoria"] = categoria
        state["step"] = "suscripcion_dia"
        
        self.bot.edit_message_text(
            f"🔄 **Suscripción: {state['nombre']}**\n"
            f"💰 Monto: ${state['monto']:,.2f}\n"
            f"🏷️ Categoría: {categoria}\n\n"
            f"📅 ¿Qué día del mes se cobra?\n"
            f"Ingresa un número del 1 al 31:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    
    def command_balance(self, message):
        """Comando /balance - Muestra balance rápido"""
        if not self.is_authorized(message.from_user.id):
            return
        
        balance = self.db.obtener_balance_actual(message.from_user.id)
        self.bot.reply_to(message, f"💰 **Balance Actual**\n${balance:,.2f}", parse_mode="Markdown")
    
    def command_gasto_rapido(self, message):
        """Comando /gasto - Registro rápido de gasto"""
        if not self.is_authorized(message.from_user.id):
            return
        
        # Extraer monto y descripción del comando si los hay
        texto = message.text.replace('/gasto', '').strip()
        
        if texto:
            # Intentar parsear: /gasto 5000 tinto
            partes = texto.split(' ', 1)
            try:
                monto = float(partes[0].replace(',', '').replace('$', '').strip())
                descripcion = partes[1] if len(partes) > 1 else ""
                
                # Usar categoría por defecto "Gastos Varios" o la primera disponible
                categorias = self.db.obtener_categorias("gasto", message.from_user.id)
                if categorias:
                    categoria = "Gastos Varios" if "Gastos Varios" in categorias else categorias[0]
                    
                    if self.db.agregar_movimiento(message.from_user.id, "gasto", categoria, monto, descripcion):
                        balance = self.db.obtener_balance_actual(message.from_user.id)
                        self.bot.reply_to(
                            message,
                            f"✅ Gasto registrado:\n"
                            f"💸 ${monto:,.2f} - {descripcion}\n"
                            f"💰 Nuevo balance: ${balance:,.2f}"
                        )
                    else:
                        self.bot.reply_to(message, "❌ Error registrando el gasto")
                else:
                    self.bot.reply_to(message, "❌ No tienes categorías de gasto configuradas")
                    
            except (ValueError, IndexError):
                self.bot.reply_to(message, 
                    "❌ Formato inválido.\nUso: /gasto 5000 descripción\n"
                    "O simplemente /gasto para usar el menú interactivo"
                )
        else:
            # Mostrar menú interactivo
            self.mostrar_menu_gastos_directo(message)
    
    def command_ingreso_rapido(self, message):
        """Comando /ingreso - Registro rápido de ingreso"""
        if not self.is_authorized(message.from_user.id):
            return
        
        texto = message.text.replace('/ingreso', '').strip()
        
        if texto:
            partes = texto.split(' ', 1)
            try:
                monto = float(partes[0].replace(',', '').replace('$', '').strip())
                descripcion = partes[1] if len(partes) > 1 else ""
                
                categorias = self.db.obtener_categorias("ingreso", message.from_user.id)
                if categorias:
                    categoria = "Otros Ingresos" if "Otros Ingresos" in categorias else categorias[0]
                    
                    if self.db.agregar_movimiento(message.from_user.id, "ingreso", categoria, monto, descripcion):
                        balance = self.db.obtener_balance_actual(message.from_user.id)
                        self.bot.reply_to(
                            message,
                            f"✅ Ingreso registrado:\n"
                            f"💵 ${monto:,.2f} - {descripcion}\n"
                            f"💰 Nuevo balance: ${balance:,.2f}"
                        )
                    else:
                        self.bot.reply_to(message, "❌ Error registrando el ingreso")
                else:
                    self.bot.reply_to(message, "❌ No tienes categorías de ingreso configuradas")
                    
            except (ValueError, IndexError):
                self.bot.reply_to(message, 
                    "❌ Formato inválido.\nUso: /ingreso 50000 descripción\n"
                    "O simplemente /ingreso para usar el menú interactivo"
                )
        else:
            self.mostrar_menu_ingresos_directo(message)
    
    def command_resumen(self, message):
        """Comando /resumen - Muestra resumen del mes"""
        if not self.is_authorized(message.from_user.id):
            return
        
        user_id = message.from_user.id
        resumen = self.db.obtener_resumen_mes(user_id)
        balance = self.db.obtener_balance_actual(user_id)
        
        texto = (
            f"📊 **Resumen {resumen['mes']:02d}/{resumen['año']}**\n\n"
            f"💰 Balance Actual: ${balance:,.2f}\n\n"
            f"📈 Movimientos del Mes:\n"
            f"   ↗️ Ingresos: ${resumen['ingresos']:,.2f}\n"
            f"   ↘️ Gastos: ${resumen['gastos']:,.2f}\n"
            f"   💰 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
            f"💡 Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}"
        )
        
        self.bot.reply_to(message, texto, parse_mode="Markdown")
    
    def command_config(self, message):
        """Comando /config - Acceso rápido a configuración"""
        if not self.is_authorized(message.from_user.id):
            return
        
        self.mostrar_menu_configuracion_directo(message)
    
    def command_ayuda(self, message):
        """Comando /ayuda - Guía de uso"""
        texto = (
            "🤖 **Bot de Finanzas Personales - Guía**\n\n"
            "**🔸 Comandos Principales:**\n"
            "/start - Menú principal\n"
            "/balance - Ver balance actual\n"
            "/gasto 5000 tinto - Registro rápido\n"
            "/ingreso 50000 sueldo - Registro rápido\n"
            "/resumen - Resumen del mes\n"
            "/config - Configuración\n\n"
            "**🔸 Funcionalidades:**\n"
            "✅ Balance en tiempo real\n"
            "✅ Categorías personalizables\n"
            "✅ Suscripciones automáticas\n"
            "✅ Histórico mensual\n"
            "✅ Recordatorios\n"
            "✅ Análisis de gastos\n\n"
            "**🔸 Cómo usar:**\n"
            "1. Configura tu balance inicial\n"
            "2. Crea categorías de ingresos y gastos\n"
            "3. Registra tus movimientos diarios\n"
            "4. Configura suscripciones recurrentes\n"
            "5. Revisa tu histórico y análisis\n\n"
            "💡 **Tip:** Los ahorros se descuentan del balance pero no son gastos"
        )
        
        self.bot.reply_to(message, texto, parse_mode="Markdown")
    
    def mostrar_menu_gastos_directo(self, message):
        """Muestra menú de gastos directamente"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Gasto", callback_data="agregar_gasto"),
            InlineKeyboardButton("📊 Ver Gastos del Mes", callback_data="ver_gastos_mes")
        )
        
        self.bot.reply_to(
            message,
            "💸 **Gestión de Gastos**\n\n¿Qué deseas hacer?",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    def mostrar_menu_ingresos_directo(self, message):
        """Muestra menú de ingresos directamente"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Ingreso", callback_data="agregar_ingreso"),
            InlineKeyboardButton("📊 Ver Ingresos del Mes", callback_data="ver_ingresos_mes")
        )
        
        self.bot.reply_to(
            message,
            "💵 **Gestión de Ingresos**\n\n¿Qué deseas hacer?",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    def mostrar_menu_configuracion_directo(self, message):
        """Muestra menú de configuración directamente"""
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏷️ Gestionar Categorías", callback_data="config_categorias"),
            InlineKeyboardButton("💰 Cambiar Balance Inicial", callback_data="config_balance"),
            InlineKeyboardButton("📊 Ver Configuración", callback_data="ver_configuracion")
        )
        
        self.bot.reply_to(
            message,
            "⚙️ **Configuración**\n\nPersonaliza tu experiencia financiera:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

# ==================== SISTEMA DE TAREAS PROGRAMADAS ====================

class TaskScheduler:
    def __init__(self, bot_instance, db_manager):
        self.bot = bot_instance
        self.db = db_manager
        self.setup_scheduled_tasks()
    
    def setup_scheduled_tasks(self):
        """Configura las tareas programadas"""
        # Ejecutar verificaciones cada hora
        schedule.every().hour.do(self.verificar_suscripciones)
        schedule.every().hour.do(self.verificar_recordatorios)
        
        # Backup diario a las 2 AM
        schedule.every().day.at("02:00").do(self.realizar_backup)
        
        # Resumen mensual el día 1 a las 9 AM
        schedule.every().day.at("08:00").do(self.generar_resumen_mensual)

    
    def verificar_suscripciones(self):
        """Verifica y procesa suscripciones pendientes"""
        try:
            suscripciones_pendientes = self.db.obtener_suscripciones_pendientes()
            
            for suscripcion in suscripciones_pendientes:
                suscripcion_id, nombre, monto, categoria, user_id = suscripcion
                
                if self.db.procesar_suscripcion(suscripcion_id):
                    # Notificar al usuario
                    mensaje = (
                        f"🔄 **Suscripción Cobrada**\n\n"
                        f"💳 {nombre}\n"
                        f"💰 ${monto:,.2f}\n"
                        f"🏷️ Categoría: {categoria}\n\n"
                        f"Se ha descontado automáticamente de tu balance."
                    )
                    
                    try:
                        self.bot.bot.send_message(user_id, mensaje, parse_mode="Markdown")
                    except Exception as e:
                        logger.error(f"Error enviando notificación de suscripción: {e}")
                    
                    logger.info(f"Suscripción procesada: {nombre} - ${monto} para usuario {user_id}")
                else:
                    logger.error(f"Error procesando suscripción {suscripcion_id}")
                    
        except Exception as e:
            logger.error(f"Error verificando suscripciones: {e}")
    
    def verificar_recordatorios(self):
        """Verifica y envía recordatorios pendientes"""
        try:
            hoy = date.today()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, descripcion, monto, user_id
                    FROM recordatorios 
                    WHERE activo = 1 AND fecha_vencimiento <= ?
                ''', (hoy,))
                
                recordatorios_pendientes = cursor.fetchall()
            
            for recordatorio in recordatorios_pendientes:
                recordatorio_id, descripcion, monto, user_id = recordatorio
                
                mensaje = f"🔔 **Recordatorio**\n\n{descripcion}"
                if monto:
                    mensaje += f"\n💰 Monto estimado: ${monto:,.2f}"
                
                try:
                    self.bot.bot.send_message(user_id, mensaje, parse_mode="Markdown")
                    
                    # Marcar recordatorio como procesado (desactivar)
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('UPDATE recordatorios SET activo = 0 WHERE id = ?', (recordatorio_id,))
                        conn.commit()
                    
                    logger.info(f"Recordatorio enviado: {descripcion} para usuario {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error enviando recordatorio: {e}")
                    
        except Exception as e:
            logger.error(f"Error verificando recordatorios: {e}")
    
    def realizar_backup(self):
        try:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_finanzas_{fecha}.csv"

            # Exportar movimientos a CSV
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM movimientos WHERE user_id = ?', (self.bot.authorized_user,))
                rows = cursor.fetchall()

                if rows:
                    with open(backup_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        # Cabeceras
                        writer.writerow(rows[0].keys())
                        # Datos
                        for row in rows:
                            writer.writerow(list(row))
                
                    # Enviar CSV al usuario
                    with open(backup_path, "rb") as f:
                        self.bot.bot.send_document(self.bot.authorized_user, f)
                    
                    logger.info(f"Backup CSV generado y enviado: {backup_path}")
                else:
                    self.bot.bot.send_message(self.bot.authorized_user, "🔔 No hay movimientos para respaldar todavía.")
        except Exception as e:
            logger.error(f"Error realizando backup CSV: {e}")
    
    def limpiar_backups_antiguos(self):
        """Elimina backups antiguos, manteniendo solo los últimos 7"""
        try:
            import glob
            backups = glob.glob("backup_finanzas_*.db")
            backups.sort(reverse=True)
            
            # Eliminar backups antiguos (mantener solo 7)
            for backup in backups[7:]:
                os.remove(backup)
                logger.info(f"Backup antiguo eliminado: {backup}")
                
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {e}")
    
    def generar_resumen_mensual(self):
        """Genera y envía resumen mensual automático (solo día 1)"""
        try:
            hoy = date.today()
            if hoy.day != 1:
                # No es primer día del mes → salir
                return  

            # Obtener todos los usuarios activos
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM usuarios WHERE configurado = 1')
                usuarios = cursor.fetchall()
            
            mes_anterior = hoy.month - 1 if hoy.month > 1 else 12
            año = hoy.year if hoy.month > 1 else hoy.year - 1
            
            for (user_id,) in usuarios:
                try:
                    resumen = self.db.obtener_resumen_mes(user_id, mes_anterior, año)
                    
                    mensaje = (
                        f"📊 **Resumen Mensual {mes_anterior:02d}/{año}**\n\n"
                        f"📈 **Movimientos:**\n"
                        f"   ↗️ Ingresos: ${resumen['ingresos']:,.2f}\n"
                        f"   ↘️ Gastos: ${resumen['gastos']:,.2f}\n"
                        f"   💰 Ahorros: ${resumen['ahorros']:,.2f}\n\n"
                        f"💰 **Balance final: ${resumen['balance']:,.2f}**\n"
                        f"💡 Neto del mes: ${(resumen['ingresos'] - resumen['gastos'] - resumen['ahorros']):,.2f}\n\n"
                        f"¡Nuevo mes, nuevas oportunidades! 💪"
                    )
                    
                    self.bot.bot.send_message(user_id, mensaje, parse_mode="Markdown")
                    logger.info(f"Resumen mensual enviado a usuario {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error enviando resumen mensual a usuario {user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error generando resúmenes mensuales: {e}")
        
    def run_scheduler(self):
        """Ejecuta el programador de tareas en un hilo separado"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logger.error(f"Error en programador de tareas: {e}")
                time.sleep(60)

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """Función principal para iniciar el bot"""
    
    # Verificar configuración
    if not BOT_TOKEN:
        logger.error("❌ Debes configurar tu BOT_TOKEN real")
        print("❌ Error: Configura tu BOT_TOKEN en la variable BOT_TOKEN")
        return
    
    if not AUTHORIZED_USER_ID:
        logger.error("❌ Debes configurar tu USER_ID real")
        print("❌ Error: Configura tu USER_ID en la variable AUTHORIZED_USER_ID")
        print("💡 Para obtener tu USER_ID, envía un mensaje a @userinfobot")
        return
    
    try:
        # Crear instancia del bot
        finance_bot = FinanceBot(BOT_TOKEN, AUTHORIZED_USER_ID)
        
        # Crear y iniciar programador de tareas en hilo separado
        scheduler = TaskScheduler(finance_bot, finance_bot.db)
        scheduler_thread = threading.Thread(target=scheduler.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("🤖 Bot de Finanzas iniciado correctamente")
        print("🚀 Bot iniciado! Presiona Ctrl+C para detener")
        print(f"📱 Usuario autorizado: {AUTHORIZED_USER_ID}")
        print("💡 Envía /start al bot para comenzar")
        
        # Iniciar polling del bot
        finance_bot.bot.polling(non_stop=True, interval=0, timeout=20)
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por el usuario")
        print("\n🛑 Bot detenido correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error fatal en el bot: {e}")
        print(f"❌ Error fatal: {e}")

# Hilo para el polling del bot
def run_bot():
    print("🤖 Iniciando bot de Telegram...")
    bot.infinity_polling(timeout=90, skip_pending=True)

# Hilo del scheduler
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Mini servidor Flask para Render
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Bot de Finanzas corriendo en Render 🚀"

if __name__ == "__main__":
    # Crear instancia del bot
    finance_bot = FinanceBot(BOT_TOKEN, AUTHORIZED_USER_ID)

    # Scheduler en thread
    scheduler = TaskScheduler(finance_bot, finance_bot.db)
    threading.Thread(target=scheduler.run_scheduler, daemon=True).start()

    # Bot en thread
    threading.Thread(target=lambda: finance_bot.bot.infinity_polling(timeout=90, skip_pending=True), daemon=True).start()

    # Mantener proceso vivo con Flask
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)