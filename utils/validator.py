"""
Validador de entradas del usuario
"""

import re
from datetime import date, datetime
from typing import Optional
from config.settings import BotConstants

class InputValidator:
    """Clase para validar todas las entradas del usuario"""
    
    @staticmethod
    def is_valid_amount(amount_str: str, allow_zero: bool = False) -> bool:
        """Valida si una cadena representa un monto válido"""
        try:
            # Limpiar la cadena
            cleaned = amount_str.strip().replace(',', '').replace('$', '')
            
            # Verificar que solo contenga números y punto decimal
            if not re.match(r'^\d+\.?\d*$', cleaned):
                return False
            
            amount = float(cleaned)
            
            # Verificar rangos
            if allow_zero:
                return 0 <= amount <= BotConstants.MAX_AMOUNT
            else:
                return BotConstants.MIN_AMOUNT <= amount <= BotConstants.MAX_AMOUNT
                
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_category_name(name: str) -> bool:
        """Valida el nombre de una categoría"""
        if not name or not isinstance(name, str):
            return False
            
        name = name.strip()
        return 2 <= len(name) <= BotConstants.MAX_CATEGORY_NAME_LENGTH
    
    @staticmethod
    def is_valid_subscription_name(name: str) -> bool:
        """Valida el nombre de una suscripción"""
        if not name or not isinstance(name, str):
            return False
            
        name = name.strip()
        return 2 <= len(name) <= BotConstants.MAX_SUBSCRIPTION_NAME_LENGTH
    
    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Valida una descripción"""
        if not description or not isinstance(description, str):
            return False
            
        description = description.strip()
        return 2 <= len(description) <= BotConstants.MAX_DESCRIPTION_LENGTH
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parsea una fecha en formato DD/MM/YYYY o DD/MM"""
        if not date_str or not isinstance(date_str, str):
            return None
            
        date_str = date_str.strip()
        
        try:
            # Intentar formato DD/MM/YYYY
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            
            # Intentar formato DD/MM (año actual)
            if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
                current_year = date.today().year
                full_date_str = f"{date_str}/{current_year}"
                return datetime.strptime(full_date_str, '%d/%m/%Y').date()
                
        except ValueError:
            pass
            
        return None
    
    @staticmethod
    def is_valid_day(day_str: str) -> bool:
        """Valida un día del mes (1-31)"""
        try:
            day = int(day_str.strip())
            return 1 <= day <= 31
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """Sanitiza un texto eliminando caracteres peligrosos"""
        if not text:
            return ""
            
        # Eliminar caracteres de control y emojis problemáticos
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Limitar longitud si se especifica
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()
            
        return sanitized.strip()