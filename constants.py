# Constantes para cálculo de custos de caixas
from supabase_client import get_supabase_manager

# Cache para evitar múltiplas consultas ao Supabase
_constants_cache = None
_custos_fixos_cache = None

# Função para obter custos fixos do Supabase
def get_custos_fixos():
    """Busca custos fixos do Supabase"""
    global _custos_fixos_cache
    
    # Se já temos cache, retornar
    if _custos_fixos_cache is not None:
        return _custos_fixos_cache
    
    supabase_manager = get_supabase_manager()
    _custos_fixos_cache = supabase_manager.get_custos_fixos()
    return _custos_fixos_cache

# Função para obter custos fixos dinamicamente
def get_custos_fixos_dinamicos():
    """Retorna os custos fixos sempre atualizados do Supabase"""
    return get_custos_fixos()

# Constantes que não mudam (materiais, preços, etc.)
# Custos fixos mensais (agora vindos do Supabase dinamicamente)
def get_custos_fixos_constantes():
    """Retorna as constantes de custos fixos sempre atualizadas"""
    custos = get_custos_fixos_dinamicos()
    constants = get_constants()
    
    # Se existe campo 'total', usar ele. Senão, somar todos
    if isinstance(custos, dict):
        if 'total' in custos:
            total_custos = custos['total']
        else:
            total_custos = sum(value for key, value in custos.items())
    else:
        raise Exception("Formato inválido de custos fixos")
    
    # Buscar 'caixas_por_mes' na tabela constants
    if 'caixas_por_mes' not in constants:
        raise Exception("Campo 'caixas_por_mes' não encontrado na tabela constants do Supabase")
    
    return {
        'TOTAL_CUSTOS_FIXOS': total_custos,
        'CAIXAS_POR_MES': constants['caixas_por_mes']
    }

# Função para obter constantes do Supabase
def get_constants():
    """Busca constantes do Supabase"""
    global _constants_cache
    
    # Se já temos cache, retornar
    if _constants_cache is not None:
        return _constants_cache
    
    supabase_manager = get_supabase_manager()
    _constants_cache = supabase_manager.get_constants()
    return _constants_cache

# Função para obter uma constante específica
def get_constant(name: str):
    """Busca uma constante específica do Supabase"""
    constants = get_constants()
    if name not in constants:
        raise Exception(f"Constante '{name}' não encontrada no Supabase")
    return constants[name]

# Função para limpar cache (útil para testes ou quando dados mudam)
def clear_cache():
    """Limpa o cache de constantes e custos fixos"""
    global _constants_cache, _custos_fixos_cache
    _constants_cache = None
    _custos_fixos_cache = None