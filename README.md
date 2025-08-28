# Bot de Telegram para Finanzas Personales - Versión Refactorizada

Bot de Telegram avanzado para gestión de finanzas personales con arquitectura modular optimizada para Render.

## Características

- ✅ Gestión completa de ingresos, gastos y ahorros
- ✅ Categorías personalizables
- ✅ Suscripciones automáticas
- ✅ Recordatorios de pagos
- ✅ Resúmenes mensuales automáticos
- ✅ Backups automáticos en CSV
- ✅ Arquitectura modular y optimizada
- ✅ Manejo inteligente de memoria
- ✅ Monitor de salud del sistema
- ✅ Optimizado para Render

## Estructura del Proyecto

```
finance-bot/
├── main.py                     # Punto de entrada principal
├── requirements.txt            # Dependencias
├── README.md                  # Este archivo
├── config/
│   └── settings.py            # Configuración centralizada
├── core/
│   ├── bot_manager.py         # Gestor principal del bot
│   ├── scheduler.py           # Tareas programadas
│   └── flask_server.py        # Servidor para Render
├── db/
│   └── database_manager.py    # Gestor de base de datos optimizado
├── handlers/
│   ├── command_handlers.py    # Comandos del bot
│   ├── callback_handlers.py   # Botones inline
│   └── message_handlers.py    # Mensajes de texto
└── utils/
    ├── message_formatter.py   # Formateador de mensajes
    ├── markup_builder.py      # Constructor de botones
    ├── validator.py           # Validador de entradas
    ├── error_handler.py       # Manejo de errores
    ├── memory_manager.py      # Gestor de memoria
    └── health_check.py        # Monitor de salud
```

## Instalación y Configuración

### 1. Clonar y configurar dependencias

```bash
git clone <tu-repositorio>
cd finance-bot
pip install -r requirements.txt
```

### 2. Crear bot de Telegram

1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot con `/newbot`
3. Guarda el token que te proporcione

### 3. Obtener tu User ID

1. Envía un mensaje a [@userinfobot](https://t.me/userinfobot)
2. Copia tu User ID numérico

### 4. Configurar variables de entorno

En Render o tu servidor, configura estas variables:

```bash
BOT_TOKEN=tu_token_del_bot
AUTHORIZED_USER_ID=tu_user_id_numerico
DATABASE_PATH=finanzas.db
LOG_LEVEL=INFO
PORT=5000
```

Variables opcionales:
```bash
DATABASE_TIMEOUT=30
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=5
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=7
```

## Despliegue en Render

### 1. Conectar repositorio

1. Ve a [Render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Crea un nuevo Web Service

### 2. Configuración del servicio

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`
- **Environment:** `Python 3`

### 3. Variables de entorno

Agrega las variables mencionadas en la sección anterior.

### 4. Desplegar

Render desplegará automáticamente tu bot. El proceso incluye:
- Servidor Flask en el puerto especificado
- Bot de Telegram ejecutándose en paralelo
- Tareas programadas activas
- Monitor de salud funcionando

## Uso del Bot

### Comandos principales

- `/start` - Iniciar bot y configuración
- `/balance` - Ver balance actual
- `/gasto 5000 descripción` - Registrar gasto rápido
- `/ingreso 50000 descripción` - Registrar ingreso rápido
- `/resumen` - Ver resumen del mes
- `/config` - Acceder a configuración
- `/ayuda` - Ver guía completa

### Funcionalidades

#### 1. Configuración inicial
- Balance inicial personalizable
- Configuración de categorías de ingresos y gastos
- Wizard guiado paso a paso

#### 2. Registro de movimientos
- Ingresos con categorías personalizables
- Gastos organizados por categorías
- Ahorros separados de gastos
- Registro rápido por comandos
- Registro detallado por menús interactivos

#### 3. Suscripciones automáticas
- Configuración de pagos recurrentes
- Cobro automático según día configurado
- Notificaciones automáticas
- Gestión completa desde el bot

#### 4. Recordatorios
- Alertas para pagos importantes
- Fechas personalizables
- Activación automática

#### 5. Análisis y reportes
- Resúmenes mensuales detallados
- Comparación entre meses
- Histórico de movimientos
- Balance en tiempo real

## Características Técnicas

### Optimizaciones implementadas

#### 1. Arquitectura modular
- Separación clara de responsabilidades
- Código organizado y mantenible
- Fácil escalabilidad

#### 2. Manejo de memoria
- Pool de conexiones de base de datos
- Limpieza automática de objetos
- Monitor de uso de memoria
- Prevención de memory leaks

#### 3. Base de datos optimizada
- Índices optimizados para consultas frecuentes
- Cache de resúmenes mensuales
- Conexiones reutilizables
- Limpieza automática de datos antiguos

#### 4. Manejo de errores
- Sistema centralizado de errores
- Logs detallados
- Recuperación automática de errores
- Notificaciones de estado

#### 5. Tareas programadas
- Verificación de suscripciones
- Envío de recordatorios
- Backups automáticos
- Limpieza de sistema
- Resúmenes mensuales

### Monitoreo y salud

El bot incluye un sistema de monitoreo que verifica:
- Uso de memoria y CPU
- Tiempo de actividad
- Estado de conexiones
- Alertas automáticas

## Mantenimiento

### Logs

Los logs se guardan automáticamente con rotación:
- Archivo: `finance_bot.log`
- Rotación: 10MB por archivo
- Retención: 5 archivos
- Niveles: ERROR, WARNING, INFO, DEBUG

### Backups

Backups automáticos diarios:
- Formato CSV con todos los movimientos
- Enviado por Telegram al usuario
- Retención configurable

### Limpieza automática

El sistema limpia automáticamente:
- Estados de usuario antiguos (2 horas)
- Recordatorios procesados (semanal)
- Cache de resúmenes (semanal)
- Memoria del sistema (4 horas)

## Solución de Problemas

### Bot no responde

1. Verifica que el token sea correcto
2. Confirma que el USER_ID esté bien configurado
3. Revisa los logs para errores
4. Reinicia el servicio en Render

### Errores de base de datos

1. Verifica permisos de escritura
2. Confirma que el archivo DB no esté corrupto
3. Revisa el espacio en disco
4. Consulta logs para detalles específicos

### Alto uso de memoria

1. El sistema se auto-optimiza automáticamente
2. Reinicia el servicio si persiste
3. Revisa logs del monitor de salud
4. Considera ajustar thresholds en configuración

### Suscripciones no se procesan

1. Verifica que el scheduler esté activo
2. Confirma fechas correctas en DB
3. Revisa logs de tareas programadas
4. Verifica conectividad de Telegram API

## Desarrollo

### Agregar nuevas características

1. Crea handlers en la carpeta correspondiente
2. Registra handlers en `bot_manager.py`
3. Agrega validaciones en `validator.py`
4. Formatea mensajes en `message_formatter.py`
5. Crea botones en `markup_builder.py`

### Testing

Para probar localmente:

```bash
# Configura variables de entorno
export BOT_TOKEN="tu_token"
export AUTHORIZED_USER_ID="tu_id"

# Ejecuta el bot
python main.py
```

### Debugging

Para debug detallado:

```bash
export LOG_LEVEL="DEBUG"
python main.py
```

---

**Bot desarrollado con arquitectura optimizada para alta disponibilidad y bajo consumo de recursos.**