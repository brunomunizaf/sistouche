#!/usr/bin/env python3
"""
Módulo CPQ para cálculo de custos de caixas customizadas
Versão síncrona para integração com Streamlit
"""

from calculations import *
from constants import get_custos_fixos_constantes, get_constant
import math

def calcular_custo_caixa_completo(
    largura_mm: float,
    altura_mm: float,
    profundidade_mm: float,
    modelo: str,
    material: str,
    quantidade: int = 1,
    berco: bool = False,
    nicho: bool = False,
    serigrafia: bool = False,
    num_cores_serigrafia: int = 1,
    num_impressoes_serigrafia: int = 1,
    usar_impressao_digital: bool = False,
    tipo_impressao: str = "A4",
    tipo_revestimento: str = "Nenhum",
    usar_cola_quente: bool = False,
    usar_cola_isopor: bool = False,
    metros_fita: float = 0,
    num_rebites: int = 0,
    markup: float = 0.0
):
    """
    Calcula o custo de produção de caixas customizadas.
    Versão síncrona para integração com Streamlit.
    """
    try:
        # Validar parâmetros
        if largura_mm <= 0 or altura_mm <= 0 or profundidade_mm <= 0:
            raise ValueError("Dimensões devem ser maiores que zero")
        
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        
        if nicho and not berco:
            raise ValueError("Nicho só pode ser selecionado junto com berço")
        
        # Aplicar revestimento padrão se material for Papelão e revestimento não foi especificado
        if material == "Papelão" and tipo_revestimento == "Nenhum":
            tipo_revestimento = "Papel"
        
        # Calcular custos fixos unitários
        custos_constantes = get_custos_fixos_constantes()
        caixas_por_mes = custos_constantes['CAIXAS_POR_MES']
        custo_fixo_unitario = custos_constantes['TOTAL_CUSTOS_FIXOS'] / caixas_por_mes
        
        # Inicializar variáveis
        area_acrilico_m2 = 0
        custo_acrilico = 0
        
        # Calcular área do papelão/acrílico
        if material == "Papelão":
            # Calcular área baseada no modelo
            if modelo == "Tampa Solta":
                area_planificada = calcular_planificacao_tampa_solta(largura_mm, altura_mm, profundidade_mm)
                area_papelao_mm2 = area_planificada['area_base_mm2'] + area_planificada['area_tampa_mm2']
            elif modelo == "Tampa Livro":
                area_planificada = calcular_planificacao_tampa_livro(largura_mm, altura_mm, profundidade_mm)
                area_papelao_mm2 = area_planificada['area_planificada_mm2']
            elif modelo == "Tampa Imã":
                area_planificada = calcular_planificacao_tampa_ima(largura_mm, altura_mm, profundidade_mm)
                area_papelao_mm2 = area_planificada['area_base_mm2'] + area_planificada['area_tampa_mm2'] + area_planificada['area_ima_mm2']
            elif modelo == "Tampa Luva":
                area_planificada = calcular_planificacao_tampa_luva(largura_mm, altura_mm, profundidade_mm)
                area_papelao_mm2 = area_planificada['area_planificada_mm2']
            elif modelo == "Tampa Redonda":
                area_planificada = calcular_planificacao_tampa_redonda(largura_mm, altura_mm, profundidade_mm)
                area_papelao_mm2 = area_planificada['area_planificada_mm2']
            else:
                raise ValueError(f"Modelo '{modelo}' não suportado")
            
            # Converter para m²
            area_papelao_m2 = area_papelao_mm2 / 1000000
            
            # Calcular custo do papelão
            custo_papelao = area_papelao_m2 * get_constant("custo_papelao_m2")
            
            # Calcular área de colagem PVA
            if modelo == "Tampa Solta":
                area_colagem_pva = calcular_area_colagem_pva_tampa_solta(largura_mm, altura_mm, profundidade_mm)
            elif modelo == "Tampa Livro":
                area_colagem_pva = calcular_area_colagem_pva_tampa_livro(largura_mm, altura_mm, profundidade_mm)
            elif modelo == "Tampa Imã":
                area_colagem_pva = calcular_area_colagem_pva_tampa_ima(largura_mm, altura_mm, profundidade_mm)
            elif modelo == "Tampa Luva":
                area_colagem_pva = calcular_area_colagem_pva_tampa_luva(largura_mm, altura_mm, profundidade_mm)
            elif modelo == "Tampa Redonda":
                area_colagem_pva = calcular_area_colagem_pva_tampa_redonda(largura_mm, altura_mm, profundidade_mm)
            
            # Converter para m²
            area_colagem_pva_mm2 = area_colagem_pva['area_colagem_total_mm2']
            area_colagem_pva_m2 = area_colagem_pva_mm2 / 1000000
            
            # A cola PVA é aplicada interno e externo (2x a área)
            area_colagem_pva_m2 = area_colagem_pva_m2 * 2
            ml_cola_pva = area_colagem_pva_m2 * get_constant("consumo_cola_pva_ml_m2")
            custo_cola_pva = ml_cola_pva * get_constant("custo_cola_pva_ml")
            
            # Calcular perímetro para cola adesiva
            perimetro_papelao = calcular_perimetro_papelao(largura_mm, altura_mm, profundidade_mm, modelo)
            perimetro_papelao_m = perimetro_papelao['perimetro_total_m']
            ml_cola_adesiva = perimetro_papelao_m * get_constant("consumo_cola_adesiva_ml_m")
            custo_cola_adesiva = ml_cola_adesiva * get_constant("custo_cola_adesiva_ml")
            
            # Inicializar custos de acrílico como zero
            custo_acrilico = 0
            custo_cola_acrilico = 0
            
        else:  # Acrílico
            # Calcular área do acrílico
            if modelo == "Tampa Solta":
                area_planificada = calcular_planificacao_tampa_solta(largura_mm, altura_mm, profundidade_mm)
                area_acrilico_mm2 = area_planificada['area_base_mm2'] + area_planificada['area_tampa_mm2']
            elif modelo == "Tampa Livro":
                area_planificada = calcular_planificacao_tampa_livro(largura_mm, altura_mm, profundidade_mm)
                area_acrilico_mm2 = area_planificada['area_planificada_mm2']
            elif modelo == "Tampa Imã":
                area_planificada = calcular_planificacao_tampa_ima(largura_mm, altura_mm, profundidade_mm)
                area_acrilico_mm2 = area_planificada['area_base_mm2'] + area_planificada['area_tampa_mm2'] + area_planificada['area_ima_mm2']
            elif modelo == "Tampa Luva":
                area_planificada = calcular_planificacao_tampa_luva(largura_mm, altura_mm, profundidade_mm)
                area_acrilico_mm2 = area_planificada['area_planificada_mm2']
            elif modelo == "Tampa Redonda":
                area_planificada = calcular_planificacao_tampa_redonda(largura_mm, altura_mm, profundidade_mm)
                area_acrilico_mm2 = area_planificada['area_planificada_mm2']
            
            # Converter para m²
            area_acrilico_m2 = area_acrilico_mm2 / 1000000
            
            # Calcular custo do acrílico
            custo_acrilico = area_acrilico_m2 * get_constant("custo_acrilico_m2")
            
            # Para acrílico, não há cola PVA
            custo_cola_pva = 0
            custo_cola_adesiva = 0
            ml_cola_pva = 0
            ml_cola_adesiva = 0
            area_papelao_m2 = 0
            custo_papelao = 0
        
        # Calcular custos de revestimento
        if tipo_revestimento != "Nenhum" and material == "Papelão":
            if tipo_revestimento == "Papel":
                area_revestimento_m2 = area_papelao_m2
                custo_revestimento = area_revestimento_m2 * get_constant("custo_papel_m2")
            elif tipo_revestimento == "Vinil UV":
                area_revestimento_m2 = area_papelao_m2
                custo_revestimento = area_revestimento_m2 * get_constant("custo_vinil_uv_m2")
        else:
            area_revestimento_m2 = 0
            custo_revestimento = 0
        
        # Calcular custos de serigrafia
        if serigrafia:
            custo_serigrafia = num_cores_serigrafia * num_impressoes_serigrafia * get_constant("custo_serigrafia_cor")
        else:
            custo_serigrafia = 0
        
        # Calcular custos de impressão digital
        if usar_impressao_digital:
            if tipo_impressao == "A4":
                custo_impressao = get_constant("custo_impressao_a4")
            elif tipo_impressao == "A3":
                custo_impressao = get_constant("custo_impressao_a3")
        else:
            custo_impressao = 0
        
        # Calcular custos de cola
        custo_cola_quente = get_constant("custo_cola_quente_fixo") if usar_cola_quente else 0
        custo_cola_isopor = get_constant("custo_cola_isopor_fixo") if usar_cola_isopor else 0
        
        # Calcular custos de fita e rebites
        custo_fita = metros_fita * get_constant("custo_fita_m")
        custo_rebites = num_rebites * get_constant("custo_rebite_unidade")
        
        # Calcular custo de imã e chapa
        custo_ima_chapa = calcular_custo_ima_chapa_automatico(modelo, largura_mm)
        
        # Calcular custo total unitário
        custo_total_unitario = (
            custo_fixo_unitario +
            custo_papelao +
            custo_acrilico +
            custo_revestimento +
            custo_cola_pva +
            custo_cola_adesiva +
            custo_serigrafia +
            custo_impressao +
            custo_cola_quente +
            custo_cola_isopor +
            custo_fita +
            custo_rebites +
            custo_ima_chapa
        )
        
        # Aplicar markup
        if markup > 0:
            preco_unitario = custo_total_unitario * (1 + markup)
        else:
            preco_unitario = custo_total_unitario
        
        # Calcular preço total do projeto
        preco_total = preco_unitario * quantidade
        
        # Calcular custo de embalagem
        custo_caixa_papelao_total = calcular_custo_caixa_papelao(quantidade)
        
        # Montar resposta
        response = {
            "preco_total": preco_total,
            "preco_unitario": preco_unitario,
            "custo_fixo_unitario": custo_fixo_unitario,
            "caixas_por_mes": caixas_por_mes,
            "custo_papelao": custo_papelao,
            "custo_acrilico": custo_acrilico,
            "custo_revestimento": custo_revestimento,
            "custo_cola_pva": custo_cola_pva,
            "custo_cola_adesiva": custo_cola_adesiva,
            "custo_serigrafia": custo_serigrafia,
            "custo_impressao": custo_impressao,
            "custo_cola_quente": custo_cola_quente,
            "custo_cola_isopor": custo_cola_isopor,
            "custo_fita": custo_fita,
            "custo_rebites": custo_rebites,
            "custo_ima_chapa": custo_ima_chapa,
            "area_papelao_m2": area_papelao_m2,
            "area_acrilico_m2": area_acrilico_m2,
            "area_revestimento_m2": area_revestimento_m2,
            "ml_cola_pva": ml_cola_pva,
            "ml_cola_adesiva": ml_cola_adesiva
        }
        
        return response
        
    except Exception as e:
        print(f"Erro no cálculo CPQ: {str(e)}")
        return None
