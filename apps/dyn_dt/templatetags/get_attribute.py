from django import template
from datetime import datetime

register = template.Library()

@register.filter(name="getattribute")
def getattribute(value, arg):
    """
    Mengambil atribut dari objek secara dinamis.
    Contoh di HTML: {{ item|getattribute:field_name }}
    """
    try:
        if hasattr(value, str(arg)):
            attr_value = getattr(value, arg)
            
            # Jika datanya berupa Tanggal/Waktu, format jadi rapi
            if isinstance(attr_value, datetime):
                return attr_value.strftime("%Y-%m-%d %H:%M:%S")
            
            return attr_value
        elif isinstance(value, dict) and arg in value:
            return value[arg]
        return ''
    except Exception:
        return ''

@register.filter
def get(dict_data, key):
    """
    Mengambil value dari dictionary.
    """
    if isinstance(dict_data, dict):
        return dict_data.get(key, [])
    return []