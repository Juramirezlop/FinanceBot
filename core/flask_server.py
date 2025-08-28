"""
Servidor Flask minimalista para mantener el bot activo en Render
"""

from flask import Flask, jsonify
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_flask_app() -> Flask:
    """Crea la aplicación Flask"""
    app = Flask(__name__)
    
    # Configurar logging para Flask
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.WARNING)
    
    @app.route("/")
    def home():
        """Endpoint principal"""
        return jsonify({
            "status": "running",
            "service": "Finance Telegram Bot",
            "timestamp": datetime.now().isoformat(),
            "message": "Bot de finanzas ejecutándose correctamente"
        })
    
    @app.route("/health")
    def health():
        """Endpoint de salud"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running"
        })
    
    @app.route("/status")
    def status():
        """Endpoint de estado detallado"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return jsonify({
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
                "pid": os.getpid()
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    # Manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint no encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Error interno del servidor"}), 500
    
    return app