"""
Gestor de base de datos optimizado con pool de conexiones y manejo de memoria
"""

import sqlite3
import logging
import threading
from typing import List, Dict, Optional, Any
from datetime import date
from contextlib import contextmanager
import gc
from config.settings import BotConstants

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Pool de conexiones SQLite thread-safe"""
    
    def __init__(self, database_path: str, max_connections: int = 5):
        self.database_path = database_path
        self.max_connections = max_connections
        self._connections = []
        self._lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """Obtiene una conexión del pool"""
        conn = None
        try:
            with self._lock:
                if self._connections:
                    conn = self._connections.pop()
                else:
                    conn = sqlite3.connect(
                        self.database_path,
                        timeout=30,
                        check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    # Optimizaciones SQLite
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=10000")
                    conn.execute("PRAGMA temp_store=MEMORY")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                try:
                    conn.commit()
                    with self._lock:
                        if len(self._connections) < self.max_connections:
                            self._connections.append(conn)
                        else:
                            conn.close()
                except Exception as e:
                    logger.error(f"Error devolviendo conexión al pool: {e}")
                    try:
                        conn.close()
                    except:
                        pass
    
    def close_all(self):
        """Cierra todas las conexiones del pool"""
        with self._lock:
            while self._connections:
                try:
                    conn = self._connections.pop()
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")

class DatabaseManager:
    """Gestor optimizado de base de datos"""
    
    def __init__(self, database_path: str = "finanzas.db", timeout: int = 30):
        self.database_path = database_path
        self.timeout = timeout
        self.pool = ConnectionPool(database_path, max_connections=5)
        
    def initialize(self) -> bool:
        """Inicializa todas las tablas de la base de datos"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Ejecutar todas las creaciones de tablas
                self._create_tables(cursor)
                conn.commit()
                
                # Crear índices para optimizar consultas
                self._create_indexes(cursor)
                conn.commit()
                
                logger.info("Base de datos inicializada correctamente")
                return True
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            return False
    
    def close(self):
        """Cierra el pool de conexiones"""
        self.pool.close_all()
    
    def _create_tables(self, cursor):
        """Crea todas las tablas necesarias"""
        
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
        
        # Tabla resumen mensual (cache para optimizar consultas)
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
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id),
                UNIQUE(mes, año, user_id)
            )
        ''')
    
    def _create_indexes(self, cursor):
        """Crea índices para optimizar las consultas más frecuentes"""
        
        indexes = [
            # Índices para movimientos (consulta más frecuente)
            "CREATE INDEX IF NOT EXISTS idx_movimientos_user_fecha ON movimientos(user_id, fecha)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_user_mes_año ON movimientos(user_id, mes, año)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos(tipo)",
            
            # Índices para suscripciones
            "CREATE INDEX IF NOT EXISTS idx_suscripciones_user_activo ON suscripciones(user_id, activo)",
            "CREATE INDEX IF NOT EXISTS idx_suscripciones_proximo_cobro ON suscripciones(proximo_cobro, activo)",
            
            # Índices para recordatorios
            "CREATE INDEX IF NOT EXISTS idx_recordatorios_user_activo ON recordatorios(user_id, activo)",
            "CREATE INDEX IF NOT EXISTS idx_recordatorios_fecha ON recordatorios(fecha_vencimiento, activo)",
            
            # Índices para categorías
            "CREATE INDEX IF NOT EXISTS idx_categorias_ingresos_user ON categorias_ingresos(user_id, activa)",
            "CREATE INDEX IF NOT EXISTS idx_categorias_gastos_user ON categorias_gastos(user_id, activa)",
            
            # Índices para resumen mensual
            "CREATE INDEX IF NOT EXISTS idx_resumen_user_periodo ON resumen_mensual(user_id, año, mes)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creando índice: {e}")
    
    # ==================== OPERACIONES DE USUARIO ====================
    
    def crear_usuario(self, user_id: int, balance_inicial: float = 0.0) -> bool:
        """Crea un nuevo usuario"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO usuarios (user_id, balance_inicial, configurado)
                    VALUES (?, ?, 0)
                ''', (user_id, balance_inicial))
                return True
                
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return False
    
    def usuario_existe(self, user_id: int) -> bool:
        """Verifica si un usuario existe"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM usuarios WHERE user_id = ? LIMIT 1', (user_id,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error verificando usuario: {e}")
            return False
    
    def usuario_configurado(self, user_id: int) -> bool:
        """Verifica si un usuario está configurado"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT configurado FROM usuarios WHERE user_id = ? LIMIT 1', 
                    (user_id,)
                )
                result = cursor.fetchone()
                return bool(result[0]) if result else False
                
        except Exception as e:
            logger.error(f"Error verificando configuración: {e}")
            return False
    
    def marcar_usuario_configurado(self, user_id: int) -> bool:
        """Marca un usuario como configurado"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE usuarios SET configurado = 1 WHERE user_id = ?', 
                    (user_id,)
                )
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marcando usuario configurado: {e}")
            return False
    
    def actualizar_balance_inicial(self, user_id: int, balance: float) -> bool:
        """Actualiza el balance inicial del usuario"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE usuarios SET balance_inicial = ? WHERE user_id = ?',
                    (balance, user_id)
                )
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error actualizando balance inicial: {e}")
            return False
    
    # ==================== OPERACIONES DE CATEGORÍAS ====================
    
    def agregar_categoria(self, nombre: str, tipo: str, user_id: int) -> bool:
        """Agrega una nueva categoría"""
        if tipo not in ['ingreso', 'gasto']:
            logger.error(f"Tipo de categoría inválido: {tipo}")
            return False
            
        if len(nombre.strip()) > BotConstants.MAX_CATEGORY_NAME_LENGTH:
            logger.error(f"Nombre de categoría muy largo: {len(nombre)}")
            return False
        
        try:
            tabla = f"categorias_{tipo}s"
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT INTO {tabla} (nombre, user_id) VALUES (?, ?)
                ''', (nombre.strip(), user_id))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error agregando categoría: {e}")
            return False
    
    def obtener_categorias(self, tipo: str, user_id: int) -> List[str]:
        """Obtiene las categorías activas de un tipo"""
        if tipo not in ['ingreso', 'gasto']:
            logger.error(f"Tipo de categoría inválido: {tipo}")
            return []
        
        try:
            tabla = f"categorias_{tipo}s"
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT nombre FROM {tabla} 
                    WHERE user_id = ? AND activa = 1
                    ORDER BY nombre
                    LIMIT 50
                ''', (user_id,))
                
                categorias = [row[0] for row in cursor.fetchall()]
                
                # Liberar memoria explícitamente
                cursor.close()
                gc.collect()
                
                return categorias
                
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return []
    
    def desactivar_categoria(self, nombre: str, tipo: str, user_id: int) -> bool:
        """Desactiva una categoría"""
        if tipo not in ['ingreso', 'gasto']:
            return False
            
        try:
            tabla = f"categorias_{tipo}s"
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE {tabla} SET activa = 0 
                    WHERE nombre = ? AND user_id = ?
                ''', (nombre, user_id))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error desactivando categoría: {e}")
            return False
    
    # ==================== OPERACIONES DE MOVIMIENTOS ====================
    
    def agregar_movimiento(self, user_id: int, tipo: str, categoria: str, 
                          monto: float, descripcion: str = "") -> bool:
        """Agrega un nuevo movimiento de forma optimizada"""
        
        if tipo not in BotConstants.MOVEMENT_TYPES:
            logger.error(f"Tipo de movimiento inválido: {tipo}")
            return False
            
        if not (BotConstants.MIN_AMOUNT <= monto <= BotConstants.MAX_AMOUNT):
            logger.error(f"Monto inválido: {monto}")
            return False
        
        # Truncar descripción si es muy larga
        if len(descripcion) > BotConstants.MAX_DESCRIPTION_LENGTH:
            descripcion = descripcion[:BotConstants.MAX_DESCRIPTION_LENGTH] + "..."
        
        try:
            hoy = date.today()
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO movimientos 
                    (fecha, tipo, categoria, monto, descripcion, mes, año, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (hoy, tipo, categoria, monto, descripcion.strip(), 
                     hoy.month, hoy.year, user_id))
                
                # Invalidar cache del resumen mensual
                self._invalidar_resumen_mensual(cursor, user_id, hoy.month, hoy.year)
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error agregando movimiento: {e}")
            return False
    
    def obtener_movimientos_mes(self, user_id: int, mes: int = None, 
                               año: int = None, tipo: str = None) -> List[Dict[str, Any]]:
        """Obtiene movimientos del mes de forma optimizada"""
        if not mes or not año:
            hoy = date.today()
            mes, año = hoy.month, hoy.year
        
        try:
            query = '''
                SELECT id, fecha, tipo, categoria, monto, descripcion
                FROM movimientos 
                WHERE user_id = ? AND mes = ? AND año = ?
            '''
            params = [user_id, mes, año]
            
            if tipo and tipo in BotConstants.MOVEMENT_TYPES:
                query += ' AND tipo = ?'
                params.append(tipo)
            
            query += ' ORDER BY fecha DESC, id DESC LIMIT 100'
            
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                movimientos = []
                for row in cursor.fetchall():
                    movimientos.append({
                        'id': row[0],
                        'fecha': row[1],
                        'tipo': row[2],
                        'categoria': row[3],
                        'monto': row[4],
                        'descripcion': row[5] or ""
                    })
                
                cursor.close()
                return movimientos
                
        except Exception as e:
            logger.error(f"Error obteniendo movimientos: {e}")
            return []
    
    def eliminar_movimiento(self, movimiento_id: int, user_id: int) -> bool:
        """Elimina un movimiento específico"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener datos del movimiento antes de eliminarlo
                cursor.execute('''
                    SELECT mes, año FROM movimientos 
                    WHERE id = ? AND user_id = ?
                ''', (movimiento_id, user_id))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                mes, año = result[0], result[1]
                
                # Eliminar movimiento
                cursor.execute('''
                    DELETE FROM movimientos 
                    WHERE id = ? AND user_id = ?
                ''', (movimiento_id, user_id))
                
                if cursor.rowcount > 0:
                    # Invalidar cache del resumen mensual
                    self._invalidar_resumen_mensual(cursor, user_id, mes, año)
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando movimiento: {e}")
            return False
    
    # ==================== OPERACIONES DE BALANCE Y RESÚMENES ====================
    
    def obtener_balance_actual(self, user_id: int) -> float:
        """Calcula el balance actual del usuario de forma optimizada"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener balance inicial
                cursor.execute(
                    'SELECT balance_inicial FROM usuarios WHERE user_id = ? LIMIT 1',
                    (user_id,)
                )
                result = cursor.fetchone()
                balance_inicial = result[0] if result else 0.0
                
                # Calcular todos los movimientos usando una sola query optimizada
                cursor.execute('''
                    SELECT SUM(CASE 
                        WHEN tipo = 'ingreso' THEN monto 
                        WHEN tipo = 'gasto' THEN -monto 
                        WHEN tipo = 'ahorro' THEN -monto 
                        ELSE 0 
                    END) as total_movimientos
                    FROM movimientos 
                    WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                total_movimientos = result[0] if result and result[0] else 0.0
                
                return balance_inicial + total_movimientos
                
        except Exception as e:
            logger.error(f"Error calculando balance: {e}")
            return 0.0
    
    def obtener_resumen_mes(self, user_id: int, mes: int = None, año: int = None) -> Dict[str, Any]:
        """Obtiene el resumen del mes usando cache cuando es posible"""
        if not mes or not año:
            hoy = date.today()
            mes, año = hoy.month, hoy.year
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Intentar obtener del cache primero
                cursor.execute('''
                    SELECT total_ingresos, total_gastos, total_ahorros, balance_final,
                           fecha_actualizacion
                    FROM resumen_mensual 
                    WHERE user_id = ? AND mes = ? AND año = ?
                ''', (user_id, mes, año))
                
                cached = cursor.fetchone()
                
                # Verificar si el cache es reciente (menos de 1 hora para mes actual)
                cache_valid = False
                if cached:
                    if mes != date.today().month or año != date.today().year:
                        # Mes pasado, cache siempre válido
                        cache_valid = True
                    else:
                        # Mes actual, verificar tiempo
                        from datetime import datetime, timedelta
                        cache_time = datetime.fromisoformat(cached[4])
                        if datetime.now() - cache_time < timedelta(hours=1):
                            cache_valid = True
                
                if cache_valid:
                    return {
                        "mes": mes,
                        "año": año,
                        "ingresos": cached[0] or 0,
                        "gastos": cached[1] or 0,
                        "ahorros": cached[2] or 0,
                        "balance": cached[3] or 0
                    }
                
                # Calcular resumen desde movimientos
                return self._calcular_resumen_mensual(cursor, user_id, mes, año)
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen mensual: {e}")
            return {"mes": mes, "año": año, "ingresos": 0, "gastos": 0, "ahorros": 0, "balance": 0}
    
    def _calcular_resumen_mensual(self, cursor, user_id: int, mes: int, año: int) -> Dict[str, Any]:
        """Calcula y cachea el resumen mensual"""
        try:
            # Calcular totales del mes
            cursor.execute('''
                SELECT tipo, SUM(monto) 
                FROM movimientos 
                WHERE user_id = ? AND mes = ? AND año = ?
                GROUP BY tipo
            ''', (user_id, mes, año))
            
            totales = {"ingreso": 0, "gasto": 0, "ahorro": 0}
            for tipo, total in cursor.fetchall():
                if tipo in totales:
                    totales[tipo] = total or 0
            
            # Calcular balance final acumulativo
            balance_final = self._calcular_balance_hasta_mes(cursor, user_id, mes, año)
            
            # Guardar en cache
            cursor.execute('''
                INSERT OR REPLACE INTO resumen_mensual 
                (mes, año, total_ingresos, total_gastos, total_ahorros, 
                 balance_final, user_id, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (mes, año, totales["ingreso"], totales["gasto"], 
                 totales["ahorro"], balance_final, user_id))
            
            return {
                "mes": mes,
                "año": año,
                "ingresos": totales["ingreso"],
                "gastos": totales["gasto"],
                "ahorros": totales["ahorro"],
                "balance": balance_final
            }
            
        except Exception as e:
            logger.error(f"Error calculando resumen mensual: {e}")
            return {"mes": mes, "año": año, "ingresos": 0, "gastos": 0, "ahorros": 0, "balance": 0}
    
    def _calcular_balance_hasta_mes(self, cursor, user_id: int, mes: int, año: int) -> float:
        """Calcula el balance acumulado hasta un mes específico"""
        try:
            # Obtener balance inicial
            cursor.execute(
                'SELECT balance_inicial FROM usuarios WHERE user_id = ? LIMIT 1',
                (user_id,)
            )
            result = cursor.fetchone()
            balance_inicial = result[0] if result else 0.0
            
            # Calcular movimientos hasta la fecha
            cursor.execute('''
                SELECT SUM(CASE 
                    WHEN tipo = 'ingreso' THEN monto 
                    WHEN tipo = 'gasto' THEN -monto 
                    WHEN tipo = 'ahorro' THEN -monto 
                    ELSE 0 
                END) as balance_movimientos
                FROM movimientos 
                WHERE user_id = ? AND (año < ? OR (año = ? AND mes <= ?))
            ''', (user_id, año, año, mes))
            
            result = cursor.fetchone()
            balance_movimientos = result[0] if result and result[0] else 0.0
            
            return balance_inicial + balance_movimientos
            
        except Exception as e:
            logger.error(f"Error calculando balance hasta mes: {e}")
            return 0.0
    
    def _invalidar_resumen_mensual(self, cursor, user_id: int, mes: int, año: int):
        """Invalida el cache del resumen mensual"""
        try:
            cursor.execute('''
                DELETE FROM resumen_mensual 
                WHERE user_id = ? AND mes = ? AND año = ?
            ''', (user_id, mes, año))
        except Exception as e:
            logger.error(f"Error invalidando cache resumen: {e}")
    
    # ==================== OPERACIONES DE SUSCRIPCIONES ====================
    
    def agregar_suscripcion(self, user_id: int, nombre: str, monto: float, 
                           categoria: str, dia_cobro: int) -> bool:
        """Agrega una nueva suscripción"""
        
        if not (1 <= dia_cobro <= 31):
            logger.error(f"Día de cobro inválido: {dia_cobro}")
            return False
            
        if not (BotConstants.MIN_AMOUNT <= monto <= BotConstants.MAX_AMOUNT):
            logger.error(f"Monto de suscripción inválido: {monto}")
            return False
        
        if len(nombre.strip()) > BotConstants.MAX_SUBSCRIPTION_NAME_LENGTH:
            logger.error(f"Nombre de suscripción muy largo: {len(nombre)}")
            return False
        
        try:
            # Calcular próximo cobro
            hoy = date.today()
            if dia_cobro <= hoy.day:
                # Próximo mes
                if hoy.month == 12:
                    proximo_cobro = date(hoy.year + 1, 1, min(dia_cobro, 31))
                else:
                    proximo_mes = hoy.month + 1
                    # Ajustar día para meses con menos días
                    import calendar
                    max_dia = calendar.monthrange(hoy.year, proximo_mes)[1]
                    dia_ajustado = min(dia_cobro, max_dia)
                    proximo_cobro = date(hoy.year, proximo_mes, dia_ajustado)
            else:
                # Este mes
                proximo_cobro = date(hoy.year, hoy.month, dia_cobro)
            
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO suscripciones 
                    (nombre, monto, categoria, dia_cobro, proximo_cobro, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (nombre.strip(), monto, categoria, dia_cobro, proximo_cobro, user_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error agregando suscripción: {e}")
            return False
    
    def obtener_suscripciones_activas(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene las suscripciones activas del usuario"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nombre, monto, categoria, dia_cobro, proximo_cobro
                    FROM suscripciones 
                    WHERE user_id = ? AND activo = 1
                    ORDER BY dia_cobro
                    LIMIT 50
                ''', (user_id,))
                
                suscripciones = []
                for row in cursor.fetchall():
                    suscripciones.append({
                        'id': row[0],
                        'nombre': row[1],
                        'monto': row[2],
                        'categoria': row[3],
                        'dia_cobro': row[4],
                        'proximo_cobro': row[5]
                    })
                
                cursor.close()
                return suscripciones
                
        except Exception as e:
            logger.error(f"Error obteniendo suscripciones: {e}")
            return []
    
    def obtener_suscripciones_pendientes(self) -> List[tuple]:
        """Obtiene suscripciones que deben cobrarse hoy"""
        try:
            hoy = date.today()
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nombre, monto, categoria, user_id, dia_cobro
                    FROM suscripciones 
                    WHERE activo = 1 AND proximo_cobro <= ?
                    LIMIT 100
                ''', (hoy,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error obteniendo suscripciones pendientes: {e}")
            return []
    
    def procesar_suscripcion(self, suscripcion_id: int) -> Optional[Dict[str, Any]]:
        """Procesa el cobro de una suscripción y retorna datos del procesamiento"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener datos de la suscripción
                cursor.execute('''
                    SELECT nombre, monto, categoria, dia_cobro, user_id
                    FROM suscripciones 
                    WHERE id = ? AND activo = 1
                    LIMIT 1
                ''', (suscripcion_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                nombre, monto, categoria, dia_cobro, user_id = result
                
                # Registrar el gasto
                hoy = date.today()
                cursor.execute('''
                    INSERT INTO movimientos 
                    (fecha, tipo, categoria, monto, descripcion, mes, año, user_id)
                    VALUES (?, 'gasto', ?, ?, ?, ?, ?, ?)
                ''', (hoy, categoria, monto, f"Suscripción: {nombre}", 
                     hoy.month, hoy.year, user_id))
                
                # Calcular próximo cobro
                import calendar
                if hoy.month == 12:
                    proximo_año = hoy.year + 1
                    proximo_mes = 1
                else:
                    proximo_año = hoy.year
                    proximo_mes = hoy.month + 1
                
                # Ajustar día para meses con menos días
                max_dia = calendar.monthrange(proximo_año, proximo_mes)[1]
                dia_ajustado = min(dia_cobro, max_dia)
                proximo_cobro = date(proximo_año, proximo_mes, dia_ajustado)
                
                # Actualizar próximo cobro
                cursor.execute('''
                    UPDATE suscripciones 
                    SET proximo_cobro = ? 
                    WHERE id = ?
                ''', (proximo_cobro, suscripcion_id))
                
                # Invalidar cache del resumen mensual
                self._invalidar_resumen_mensual(cursor, user_id, hoy.month, hoy.year)
                
                return {
                    'nombre': nombre,
                    'monto': monto,
                    'categoria': categoria,
                    'user_id': user_id
                }
                
        except Exception as e:
            logger.error(f"Error procesando suscripción: {e}")
            return None
    
    def desactivar_suscripcion(self, suscripcion_id: int, user_id: int) -> bool:
        """Desactiva una suscripción"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE suscripciones 
                    SET activo = 0 
                    WHERE id = ? AND user_id = ?
                ''', (suscripcion_id, user_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error desactivando suscripción: {e}")
            return False
    
    # ==================== OPERACIONES DE RECORDATORIOS ====================
    
    def agregar_recordatorio(self, user_id: int, descripcion: str, 
                            fecha_vencimiento: date, monto: Optional[float] = None) -> bool:
        """Agrega un nuevo recordatorio"""
        
        if len(descripcion.strip()) > BotConstants.MAX_DESCRIPTION_LENGTH:
            descripcion = descripcion.strip()[:BotConstants.MAX_DESCRIPTION_LENGTH] + "..."
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO recordatorios 
                    (descripcion, monto, fecha_vencimiento, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (descripcion.strip(), monto, fecha_vencimiento, user_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error agregando recordatorio: {e}")
            return False
    
    def obtener_recordatorios_pendientes(self) -> List[Dict[str, Any]]:
        """Obtiene recordatorios que vencen hoy"""
        try:
            hoy = date.today()
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, descripcion, monto, user_id
                    FROM recordatorios 
                    WHERE activo = 1 AND fecha_vencimiento <= ?
                    ORDER BY fecha_vencimiento
                    LIMIT 50
                ''', (hoy,))
                
                recordatorios = []
                for row in cursor.fetchall():
                    recordatorios.append({
                        'id': row[0],
                        'descripcion': row[1],
                        'monto': row[2],
                        'user_id': row[3]
                    })
                
                cursor.close()
                return recordatorios
                
        except Exception as e:
            logger.error(f"Error obteniendo recordatorios pendientes: {e}")
            return []
    
    def marcar_recordatorio_procesado(self, recordatorio_id: int) -> bool:
        """Marca un recordatorio como procesado (lo desactiva)"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE recordatorios 
                    SET activo = 0 
                    WHERE id = ?
                ''', (recordatorio_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marcando recordatorio procesado: {e}")
            return False
    
    # ==================== OPERACIONES DE MANTENIMIENTO ====================
    
    def limpiar_datos_antiguos(self, dias_antiguedad: int = 90):
        """Limpia datos antiguos para optimizar la base de datos"""
        try:
            from datetime import timedelta
            fecha_limite = date.today() - timedelta(days=dias_antiguedad)
            
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Limpiar recordatorios procesados antiguos
                cursor.execute('''
                    DELETE FROM recordatorios 
                    WHERE activo = 0 AND fecha_vencimiento < ?
                ''', (fecha_limite,))
                recordatorios_limpiados = cursor.rowcount
                
                # Limpiar cache de resúmenes muy antiguos
                cursor.execute('''
                    DELETE FROM resumen_mensual 
                    WHERE fecha_actualizacion < ?
                ''', (fecha_limite,))
                resumenes_limpiados = cursor.rowcount
                
                # VACUUM para reclamar espacio
                cursor.execute('VACUUM')
                
                logger.info(f"Limpieza completada: {recordatorios_limpiados} recordatorios, "
                           f"{resumenes_limpiados} resumenes")
                
                return True
                
        except Exception as e:
            logger.error(f"Error en limpieza de datos: {e}")
            return False
    
    def obtener_estadisticas_db(self) -> Dict[str, int]:
        """Obtiene estadísticas de la base de datos"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                tablas = ['usuarios', 'movimientos', 'suscripciones', 'recordatorios', 
                        'categorias_ingresos', 'categorias_gastos', 'resumen_mensual']
                
                for tabla in tablas:
                    cursor.execute(f'SELECT COUNT(*) FROM {tabla}')
                    stats[tabla] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}