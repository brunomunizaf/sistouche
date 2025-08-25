import math
from itertools import permutations
from constants import get_constant
from enum import Enum

def calcular_area_papelao(largura, altura, profundidade, tipo_tampa):
    """Calcula a área total de papelão necessária baseada no tipo de tampa"""
    area_base = largura * altura
    
    # Converter enum para string se necessário
    if hasattr(tipo_tampa, 'value'):
        tipo_tampa = tipo_tampa.value
    
    if tipo_tampa == "Tampa Solta":
        # Base + 4 laterais + tampa
        area_laterais = 2 * (largura * profundidade) + 2 * (altura * profundidade)
        area_tampa = largura * altura
        return area_base + area_laterais + area_tampa
    
    elif tipo_tampa == "Tampa Livro":
        # Base + 4 laterais + tampa (tampa conectada)
        area_laterais = 2 * (largura * profundidade) + 2 * (altura * profundidade)
        area_tampa = largura * altura
        return area_base + area_laterais + area_tampa
    
    elif tipo_tampa == "Tampa Luva":
        # Base + 4 laterais + tampa + aba lateral
        area_laterais = 2 * (largura * profundidade) + 2 * (altura * profundidade)
        area_tampa = largura * altura
        area_aba = largura * profundidade  # Aba lateral
        return area_base + area_laterais + area_tampa + area_aba
    
    elif tipo_tampa == "Tampa Imã":
        # Base + 4 laterais + tampa + área para imã
        area_laterais = 2 * (largura * profundidade) + 2 * (altura * profundidade)
        area_tampa = largura * altura
        area_ima = largura * 2  # Área para imã (2cm de altura)
        return area_base + area_laterais + area_tampa + area_ima
    
    else:
        return area_base

def calcular_custo_papelao(largura, altura):
    """Calcula o custo do papelão baseado na área"""
    area_m2 = (largura * altura) / 10000  # Converter cm² para m²
    return area_m2 * get_constant("custo_papelao_m2")

def calcular_custo_vinil_uv(largura_vinil, altura_vinil):
    """Calcula o custo do vinil UV baseado na área"""
    area_m2 = (largura_vinil * altura_vinil) / 10000
    return area_m2 * get_constant("custo_vinil_uv_por_m2")

def calcular_custo_acrilico(largura_acrilico, altura_acrilico):
    """Calcula o custo do acrílico baseado na área"""
    area_m2 = (largura_acrilico * altura_acrilico) / 10000
    return area_m2 * get_constant("custo_acrilico_m2")

def calcular_custo_ima_chapa_automatico(tipo_tampa, largura):
    """Calcula automaticamente o custo de imã + chapa baseado no tipo de tampa"""
    # Converter enum para string se necessário
    if hasattr(tipo_tampa, 'value'):
        tipo_tampa = tipo_tampa.value
    
    if tipo_tampa == "Tampa Imã":
        # Regra: 1 par se largura ≤ 10cm, 2 pares se > 10cm
        num_pares = 1 if largura <= 10 else 2
        return num_pares * get_constant("custo_ima_chapa_par")
    return 0

def calcular_max_caixas_por_embalagem(largura, altura, profundidade):
    """Calcula o número máximo de caixas que cabem na embalagem 50x35x35"""
    # Dimensões da caixa de papelão ondulado
    embalagem_largura = 50
    embalagem_altura = 35
    embalagem_profundidade = 35
    
    # Verificar se alguma dimensão da caixa é maior que a dimensão correspondente da embalagem
    # (considerando todas as rotações possíveis)
    caixa_dims = [largura, altura, profundidade]
    embalagem_dims = [embalagem_largura, embalagem_altura, embalagem_profundidade]
    
    # Verificar se a caixa cabe em alguma rotação
    cabe_em_alguma_rotacao = False
    for dims in permutations(caixa_dims):
        l, a, p = dims
        if l <= embalagem_largura and a <= embalagem_altura and p <= embalagem_profundidade:
            cabe_em_alguma_rotacao = True
            break
    
    # Se não cabe em nenhuma rotação, retorna 0
    if not cabe_em_alguma_rotacao:
        return 0
    
    max_caixas = 0
    
    # Testar todas as 6 rotações possíveis (3! = 6)
    for dims in permutations(caixa_dims):
        l, a, p = dims
        
        # Calcular quantas caixas cabem em cada direção
        num_largura = embalagem_largura // l
        num_altura = embalagem_altura // a
        num_profundidade = embalagem_profundidade // p
        
        # Total de caixas para esta rotação
        total_esta_rotacao = num_largura * num_altura * num_profundidade
        
        if total_esta_rotacao > max_caixas:
            max_caixas = total_esta_rotacao
    
    return max_caixas

def calcular_custo_caixa_papelao(num_caixas_por_embalagem):
    """Calcula o custo da caixa de papelão ondulado por unidade"""
    if num_caixas_por_embalagem > 0:
        return get_constant("custo_caixa_despache_unidade") / num_caixas_por_embalagem
    return 0

def aplicar_multiplicador_complexidade(custo_variavel, tem_berco, tem_nicho):
    """Aplica multiplicador de complexidade"""
    if tem_berco and tem_nicho:
        return custo_variavel * get_constant("multiplicador_ambos")
    elif tem_berco:
        return custo_variavel * get_constant("multiplicador_berco")
    else:
        return custo_variavel

def determinar_colas_automaticas(estrutura, usar_acrilico):
    """Determina automaticamente quais colas usar baseado na estrutura"""
    if estrutura == "Papelão":
        return {
            "cola_pva": True,
            "cola_adesiva": True,
            "cola_quente": False,
            "cola_isopor": False,
            "cola_acrilico": False
        }
    elif estrutura == "Acrílico":
        return {
            "cola_pva": False,
            "cola_adesiva": False,
            "cola_quente": False,
            "cola_isopor": False,
            "cola_acrilico": True
        }
    else:
        return {
            "cola_pva": False,
            "cola_adesiva": False,
            "cola_quente": False,
            "cola_isopor": False,
            "cola_acrilico": False
        }

def determinar_revestimentos_disponiveis(estrutura):
    """Determina quais revestimentos estão disponíveis para cada estrutura"""
    if estrutura == "Papelão":
        return ["Vinil UV", "Papel"]
    elif estrutura == "Acrílico":
        return ["Nenhum"]
    else:
        return []

def calcular_planificacao_tampa_solta(largura, altura, profundidade):
    """
    Calcula a planificação para caixas com tampa solta
    Retorna: (area_base, area_tampa, caixas_por_chapa, chapas_necessarias)
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Cálculo da base planificada
    largura_base_planificada = largura_mm + 2 * profundidade_mm
    altura_base_planificada = altura_mm + 2 * profundidade_mm
    area_base_planificada = largura_base_planificada * altura_base_planificada
    
    # Cálculo da tampa solta
    # Profundidade da tampa é fixa em 25mm
    profundidade_tampa_mm = 25
    
    # Largura e altura da face central da tampa (maior que a base em 3×espessura)
    largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
    altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
    
    # Planificação da tampa
    largura_tampa_planificada = largura_tampa + 2 * profundidade_tampa_mm
    altura_tampa_planificada = altura_tampa + 2 * profundidade_tampa_mm
    area_tampa_planificada = largura_tampa_planificada * altura_tampa_planificada
    
    # Calcular quantas caixas completas cabem em uma chapa
    # Área disponível na chapa (descontando margens)
    area_disponivel = (get_constant("largura_placa_papelao_mm") - get_constant("margem_mm")) * (get_constant("altura_placa_papelao_mm") - get_constant("margem_mm"))
    
    # Área necessária para uma caixa completa (base + tampa)
    area_caixa_completa = area_base_planificada + area_tampa_planificada
    
    # Número de caixas que cabem em uma chapa
    caixas_por_chapa = int(area_disponivel / area_caixa_completa)
    
    return {
        'area_base_mm2': area_base_planificada,
        'area_tampa_mm2': area_tampa_planificada,
        'area_caixa_completa_mm2': area_caixa_completa,
        'caixas_por_chapa': caixas_por_chapa,
        'dimensoes_base': (largura_base_planificada, altura_base_planificada),
        'dimensoes_tampa': (largura_tampa_planificada, altura_tampa_planificada)
    }

def calcular_planificacao_tampa_livro(largura, altura, profundidade):
    """
    Calcula a planificação para caixas com tampa-livro
    Retorna: (area_planificada, caixas_por_chapa, chapas_necessarias)
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Cálculo da planificação da tampa-livro
    # Largura planificada = largura da base + 2 × profundidade
    largura_planificada = largura_mm + 2 * profundidade_mm
    
    # Altura planificada = 2 × altura + profundidade
    altura_planificada = 2 * altura_mm + profundidade_mm
    
    # Área planificada
    area_planificada = largura_planificada * altura_planificada
    
    # Calcular quantas caixas cabem por chapa
    # Colunas por chapa = parte inteira de: 1040 ÷ (largura planificada + margem)
    colunas_por_chapa = int(get_constant("largura_placa_papelao_mm") / (largura_planificada + get_constant("margem_mm")))
    
    # Linhas por chapa = parte inteira de: 860 ÷ (altura planificada + margem)
    linhas_por_chapa = int(get_constant("altura_placa_papelao_mm") / (altura_planificada + get_constant("margem_mm")))
    
    # Caixas por chapa = colunas × linhas
    caixas_por_chapa = colunas_por_chapa * linhas_por_chapa
    
    return {
        'area_planificada_mm2': area_planificada,
        'caixas_por_chapa': caixas_por_chapa,
        'dimensoes_planificacao': (largura_planificada, altura_planificada),
        'colunas_por_chapa': colunas_por_chapa,
        'linhas_por_chapa': linhas_por_chapa
    }

def calcular_planificacao_tampa_ima(largura, altura, profundidade):
    """
    Calcula a planificação para caixas com tampa-imã
    Retorna: (area_base, area_tampa, area_ima, caixas_por_chapa)
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Cálculo da base planificada
    largura_base_planificada = largura_mm + 2 * profundidade_mm
    altura_base_planificada = altura_mm + 2 * profundidade_mm
    area_base_planificada = largura_base_planificada * altura_base_planificada
    
    # Cálculo da tampa com imã
    # Profundidade da tampa é fixa em 25mm
    profundidade_tampa_mm = 25
    
    # Largura e altura da face central da tampa (maior que a base em 3×espessura)
    largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
    altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
    
    # Planificação da tampa
    largura_tampa_planificada = largura_tampa + 2 * profundidade_tampa_mm
    altura_tampa_planificada = altura_tampa + 2 * profundidade_tampa_mm
    area_tampa_planificada = largura_tampa_planificada * altura_tampa_planificada
    
    # Cálculo da área para imã (2cm de altura)
    altura_ima_mm = 20  # 2cm
    area_ima_planificada = largura_mm * altura_ima_mm
    
    # Calcular quantas caixas completas cabem em uma chapa
    # Área disponível na chapa (descontando margens)
    area_disponivel = (get_constant("largura_placa_papelao_mm") - get_constant("margem_mm")) * (get_constant("altura_placa_papelao_mm") - get_constant("margem_mm"))
    
    # Área necessária para uma caixa completa (base + tampa + imã)
    area_caixa_completa = area_base_planificada + area_tampa_planificada + area_ima_planificada
    
    # Número de caixas que cabem em uma chapa
    caixas_por_chapa = int(area_disponivel / area_caixa_completa)
    
    return {
        'area_base_mm2': area_base_planificada,
        'area_tampa_mm2': area_tampa_planificada,
        'area_ima_mm2': area_ima_planificada,
        'area_caixa_completa_mm2': area_caixa_completa,
        'caixas_por_chapa': caixas_por_chapa,
        'dimensoes_base': (largura_base_planificada, altura_base_planificada),
        'dimensoes_tampa': (largura_tampa_planificada, altura_tampa_planificada),
        'dimensoes_ima': (largura_mm, altura_ima_mm)
    }

def calcular_planificacao_tampa_luva(largura, altura, profundidade):
    """
    Calcula a planificação para caixas com tampa-luva
    Retorna: (area_base, area_tampa, area_aba, caixas_por_chapa)
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Cálculo da base planificada
    largura_base_planificada = largura_mm + 2 * profundidade_mm
    altura_base_planificada = altura_mm + 2 * profundidade_mm
    area_base_planificada = largura_base_planificada * altura_base_planificada
    
    # Cálculo da tampa-luva
    # Profundidade da tampa é fixa em 25mm
    profundidade_tampa_mm = 25
    
    # Largura e altura da face central da tampa (maior que a base em 3×espessura)
    largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
    altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
    
    # Planificação da tampa
    largura_tampa_planificada = largura_tampa + 2 * profundidade_tampa_mm
    altura_tampa_planificada = altura_tampa + 2 * profundidade_tampa_mm
    area_tampa_planificada = largura_tampa_planificada * altura_tampa_planificada
    
    # Cálculo da aba (para tampa-luva)
    # A aba tem a largura da caixa e profundidade de 15mm
    largura_aba = largura_mm
    profundidade_aba = 15
    area_aba_planificada = largura_aba * profundidade_aba
    
    # Calcular quantas caixas completas cabem em uma chapa
    # Área disponível na chapa (descontando margens)
    area_disponivel = (get_constant("largura_placa_papelao_mm") - get_constant("margem_mm")) * (get_constant("altura_placa_papelao_mm") - get_constant("margem_mm"))
    
    # Área necessária para uma caixa completa (base + tampa + aba)
    area_caixa_completa = area_base_planificada + area_tampa_planificada + area_aba_planificada
    
    # Número de caixas que cabem em uma chapa
    caixas_por_chapa = int(area_disponivel / area_caixa_completa)
    
    return {
        'area_base_mm2': area_base_planificada,
        'area_tampa_mm2': area_tampa_planificada,
        'area_aba_mm2': area_aba_planificada,
        'area_caixa_completa_mm2': area_caixa_completa,
        'caixas_por_chapa': caixas_por_chapa,
        'dimensoes_base': (largura_base_planificada, altura_base_planificada),
        'dimensoes_tampa': (largura_tampa_planificada, altura_tampa_planificada),
        'dimensoes_aba': (largura_mm, profundidade_aba)
    } 

def calcular_area_colagem_pva_tampa_solta(largura, altura, profundidade):
    """
    Calcula a área de colagem PVA para tampa solta
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Para tampa solta, a cola PVA é aplicada em toda a área do papelão
    # Usar a mesma lógica da planificação para obter a área total
    
    # Cálculo da base planificada
    largura_base_planificada = largura_mm + 2 * profundidade_mm
    altura_base_planificada = altura_mm + 2 * profundidade_mm
    area_base_planificada = largura_base_planificada * altura_base_planificada
    
    # Cálculo da tampa planificada
    profundidade_tampa_mm = 25
    largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
    altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
    largura_tampa_planificada = largura_tampa + 2 * profundidade_tampa_mm
    altura_tampa_planificada = altura_tampa + 2 * profundidade_tampa_mm
    area_tampa_planificada = largura_tampa_planificada * altura_tampa_planificada
    
    # Área total de colagem (base + tampa)
    area_colagem_total = area_base_planificada + area_tampa_planificada
    
    return {
        'area_colagem_total_mm2': area_colagem_total,
        'area_base_mm2': area_base_planificada,
        'area_tampa_mm2': area_tampa_planificada
    } 

def calcular_area_colagem_pva_tampa_livro(largura, altura, profundidade):
    """
    Calcula a área de colagem PVA para tampa-livro
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Para tampa-livro, a colagem é nas laterais
    area_laterais_largura = 2 * (profundidade_mm * largura_mm)
    area_laterais_altura = 2 * (profundidade_mm * altura_mm)
    
    # Área total de colagem
    area_colagem_total = area_laterais_largura + area_laterais_altura
    
    return {
        'area_colagem_total_mm2': area_colagem_total,
        'area_laterais_largura_mm2': area_laterais_largura,
        'area_laterais_altura_mm2': area_laterais_altura
    } 

def calcular_area_colagem_pva_tampa_ima(largura, altura, profundidade):
    """
    Calcula a área de colagem PVA para tampa-imã
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Área de colagem = área das laterais da base
    area_laterais_largura = 2 * (largura_mm * profundidade_mm)
    area_laterais_altura = 2 * (altura_mm * profundidade_mm)
    
    # Área total de colagem
    area_colagem_total = area_laterais_largura + area_laterais_altura
    
    return {
        'area_colagem_total_mm2': area_colagem_total,
        'area_laterais_largura_mm2': area_laterais_largura,
        'area_laterais_altura_mm2': area_laterais_altura
    } 

def calcular_planificacao_tampa_redonda(largura, altura, profundidade):
    """
    Calcula a planificação para caixas com tampa redonda
    Retorna: (area_base, area_tampa, caixas_por_chapa)
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Para caixas redondas, usar o diâmetro maior
    diametro = max(largura_mm, altura_mm)
    
    # Cálculo da base planificada (circular)
    area_base = (diametro / 2) ** 2 * math.pi  # π * r²
    
    # Cálculo da tampa redonda
    # A tampa é um pouco maior que a base
    diametro_tampa = diametro + 6  # 3mm de cada lado
    area_tampa = (diametro_tampa / 2) ** 2 * math.pi
    
    # Calcular quantas caixas completas cabem em uma chapa
    # Área disponível na chapa (descontando margens)
    area_disponivel = (get_constant("largura_placa_papelao_mm") - get_constant("margem_mm")) * (get_constant("altura_placa_papelao_mm") - get_constant("margem_mm"))
    
    # Área necessária para uma caixa completa (base + tampa)
    area_caixa_completa = area_base + area_tampa
    
    # Número de caixas que cabem em uma chapa
    caixas_por_chapa = int(area_disponivel / area_caixa_completa)
    
    return {
        'area_base_mm2': area_base,
        'area_tampa_mm2': area_tampa,
        'area_caixa_completa_mm2': area_caixa_completa,
        'caixas_por_chapa': caixas_por_chapa,
        'diametro_base': diametro,
        'diametro_tampa': diametro_tampa
    }

def calcular_perimetro_papelao(largura, altura, profundidade, tipo_tampa):
    """
    Calcula o perímetro total do papelão necessário para a caixa
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    if tipo_tampa == "Tampa Solta":
        # Perímetro da base planificada
        largura_base_planificada = largura_mm + 2 * profundidade_mm
        altura_base_planificada = altura_mm + 2 * profundidade_mm
        perimetro_base = 2 * (largura_base_planificada + altura_base_planificada)
        
        # Perímetro da tampa planificada
        largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
        altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
        largura_tampa_planificada = largura_tampa + 2 * 25  # 25mm de profundidade da tampa
        altura_tampa_planificada = altura_tampa + 2 * 25
        perimetro_tampa = 2 * (largura_tampa_planificada + altura_tampa_planificada)
        
        perimetro_total = perimetro_base + perimetro_tampa
        
    elif tipo_tampa == "Tampa Livro":
        # Perímetro da planificação única
        largura_planificada = largura_mm + 2 * profundidade_mm
        altura_planificada = 2 * altura_mm + profundidade_mm
        perimetro_total = 2 * (largura_planificada + altura_planificada)
        
    elif tipo_tampa == "Tampa Imã":
        # Perímetro da base planificada
        largura_base_planificada = largura_mm + 2 * profundidade_mm
        altura_base_planificada = altura_mm + 2 * profundidade_mm
        perimetro_base = 2 * (largura_base_planificada + altura_base_planificada)
        
        # Perímetro da tampa planificada
        largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
        altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
        largura_tampa_planificada = largura_tampa + 2 * 25
        altura_tampa_planificada = altura_tampa + 2 * 25
        perimetro_tampa = 2 * (largura_tampa_planificada + altura_tampa_planificada)
        
        # Perímetro do imã (largura × altura)
        perimetro_ima = 2 * (largura_mm + 20)  # 20mm de altura do imã
        
        perimetro_total = perimetro_base + perimetro_tampa + perimetro_ima
        
    elif tipo_tampa == "Tampa Luva":
        # Perímetro da base planificada
        largura_base_planificada = largura_mm + 2 * profundidade_mm
        altura_base_planificada = altura_mm + 2 * profundidade_mm
        perimetro_base = 2 * (largura_base_planificada + altura_base_planificada)
        
        # Perímetro da tampa planificada
        largura_tampa = largura_mm + 3 * get_constant("espessura_papelao_mm")
        altura_tampa = altura_mm + 3 * get_constant("espessura_papelao_mm")
        largura_tampa_planificada = largura_tampa + 2 * 25
        altura_tampa_planificada = altura_tampa + 2 * 25
        perimetro_tampa = 2 * (largura_tampa_planificada + altura_tampa_planificada)
        
        # Perímetro da aba lateral
        perimetro_aba = 2 * (largura_mm + profundidade_mm)
        
        perimetro_total = perimetro_base + perimetro_tampa + perimetro_aba
    elif tipo_tampa == "Tampa Redonda":
        # Perímetro da base circular
        diametro_mm = largura_mm
        raio_mm = diametro_mm / 2
        perimetro_base = 2 * math.pi * raio_mm
        
        # Perímetro da tampa circular
        raio_tampa_mm = raio_mm + 3 * get_constant("espessura_papelao_mm")
        perimetro_tampa = 2 * math.pi * raio_tampa_mm
        
        perimetro_total = perimetro_base + perimetro_tampa

    
    return {
        'perimetro_total_mm': perimetro_total,
        'perimetro_total_m': perimetro_total / 1000  # Converter para metros
    }

def calcular_area_colagem_pva_tampa_luva(largura, altura, profundidade):
    """
    Calcula a área de colagem PVA para tampa-luva
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Área de colagem = área das laterais da base
    area_laterais_largura = 2 * (largura_mm * profundidade_mm)
    area_laterais_altura = 2 * (altura_mm * profundidade_mm)
    
    # Área total de colagem
    area_colagem_total = area_laterais_largura + area_laterais_altura
    
    return {
        'area_colagem_total_mm2': area_colagem_total,
        'area_laterais_largura_mm2': area_laterais_largura,
        'area_laterais_altura_mm2': area_laterais_altura
    }

def calcular_area_colagem_pva_tampa_redonda(largura, altura, profundidade):
    """
    Calcula a área de colagem PVA para tampa redonda
    """
    # As dimensões já estão em mm
    largura_mm = largura
    altura_mm = altura
    profundidade_mm = profundidade
    
    # Para caixas redondas, usar o diâmetro maior
    diametro = max(largura_mm, altura_mm)
    
    # Área de colagem = perímetro da base × profundidade
    perimetro = diametro * math.pi  # π * d
    area_colagem_total = perimetro * profundidade_mm
    
    return {
        'area_colagem_total_mm2': area_colagem_total,
        'perimetro_base_mm': perimetro
    } 