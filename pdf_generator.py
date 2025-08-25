import os
from datetime import datetime
import pytz
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class TouchePDFGenerator:
    def __init__(self):
        # Registrar fontes personalizadas
        self._register_fonts()
        
        # Dimensões da página
        self.page_width, self.page_height = A4
        self.header_height = 1.15*inch  # Altura do header
        self.footer_height = 0.70*inch  # Altura do footer
        self.content_height = self.page_height - self.header_height - self.footer_height
        
        # Margens para o conteúdo
        self.content_margin = 0.5*inch
        self.content_width = self.page_width - 2*self.content_margin
        
        # Estilos personalizados
        self.styles = self._create_styles()
    
    def _register_fonts(self):
        """Registra as fontes personalizadas (TTF)"""
        try:
            # Lista de fontes para tentar registrar (apenas TTF)
            font_files = [
                ('HoeflerBlack', 'fonts/Hoefler black.ttf'),
                ('HoeflerBlackItalic', 'fonts/Hoefler black italic.ttf'),
                ('HoeflerTextOrnaments', 'fonts/Hoefler Text Ornaments.ttf'),
                ('HoeflerTextRegular', 'fonts/Hoefler Text Regular.ttf'),
            ]

            # Registrar cada fonte
            for font_name, font_path in font_files:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        print(f"✅ Fonte {font_name} registrada ({font_path})")
                    except Exception as e:
                        print(f"⚠️ Erro ao registrar {font_name}: {e}")
                else:
                    print(f"⚠️ Arquivo '{font_path}' não encontrado")
                    
        except Exception as e:
            print(f"❌ Erro ao registrar fontes: {e}")
    
    def _get_available_font(self):
        """Retorna a primeira fonte disponível ou Helvetica como fallback"""
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        
        # Prioridade: HoeflerTextRegular > Helvetica
        if 'HoeflerTextRegular' in registered_fonts:
            return 'HoeflerTextRegular'
        else:
            return 'Helvetica'
    
    def _create_styles(self):
        """Cria os estilos personalizados da TOUCHÉ"""
        styles = getSampleStyleSheet()

        # Obter fonte disponível
        font_name = self._get_available_font()

        title_style = ParagraphStyle(
            'ToucheTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName=font_name,
            leftIndent=12,  # Alinhar com padding das tabelas
            rightIndent=12
        )

        subtitle_style = ParagraphStyle(
            'ToucheSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.black,
            fontName=font_name,
            leftIndent=12,  # Alinhar com padding das tabelas
            rightIndent=12
        )

        normal_style = ParagraphStyle(
            'ToucheNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName=font_name,
            leftIndent=12,  # Alinhar com padding das tabelas
            rightIndent=12
        )

        detail_style = ParagraphStyle(
            'ToucheDetail',
            parent=styles['Normal'],  # Usar Normal como parent
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica',  # Usar fonte diferente para detalhes
            leftIndent=12,
            rightIndent=12
        )

        observation_style = ParagraphStyle(
            'ToucheObservation',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_LEFT,
            textColor=colors.black,
            fontName='Helvetica',
            leftIndent=20,
            rightIndent=12,
            spaceAfter=0
        )

        observation_centered_style = ParagraphStyle(
            'ToucheObservationCentered',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica',
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0
        )

        return {
            'title': title_style,
            'subtitle': subtitle_style,
            'normal': normal_style,
            'detail': detail_style,
            'observation': observation_style,
            'observation_centered': observation_centered_style
        }
    
    def _create_content_frame(self):
        """Cria o frame para o conteúdo principal"""
        return Frame(
            self.content_margin,  # Margem esquerda
            self.footer_height + 0.1*inch,  # Posicionar acima do footer
            self.content_width,  # Largura do conteúdo
            self.content_height - 0.2*inch,  # Altura do conteúdo
            topPadding=0.2*inch,
            bottomPadding=0.2*inch,
            leftPadding=0,
            rightPadding=0
        )

    def _create_header_footer_template(self):
        """Cria o template com header e footer fixos"""
        def header_footer(canvas, doc):
            # Header no topo
            header_path = 'header.png'
            if os.path.exists(header_path):
                try:
                    canvas.drawImage(header_path, 0, self.page_height - self.header_height, 
                                   width=8.27*inch, height=1.15*inch)
                except Exception as e:
                    print(f"Erro ao carregar header: {e}")
            
            # Footer no bottom
            footer_path = 'footer.png'
            if os.path.exists(footer_path):
                try:
                    canvas.drawImage(footer_path, 0, 0, width=8.27*inch, height=0.70*inch)
                except Exception as e:
                    print(f"Erro ao carregar footer: {e}")
        
        return PageTemplate(
            id='touche_template',
            frames=[self._create_content_frame()],
            onPage=header_footer
        )
    
    def _create_contact_table(self, request_data):
        """Cria a tabela de contato"""
        font_name = self._get_available_font() # Get font for tables
        
        # Dados dinâmicos do request_data ou valores padrão
        cliente_empresa = request_data.get('cliente_empresa', '')
        representante = request_data.get('representante', '')
        projeto = request_data.get('projeto', '')
        cnpj_cpf = request_data.get('cnpj_cpf', '')
        endereco = request_data.get('endereco', '')
        contato = request_data.get('contato', '')
        email = request_data.get('email', '')
        
        # Novos campos
        cliente = request_data.get('cliente', '')
        email_cliente = request_data.get('email_cliente', '')
        telefone_cliente = request_data.get('telefone_cliente', '')
        
        # Usar novos campos se disponíveis, senão usar os antigos
        cliente_final = cliente if cliente else cliente_empresa
        representante_final = representante if representante else cliente
        email_final = email_cliente if email_cliente else email
        contato_final = telefone_cliente if telefone_cliente else contato
        
        dados_contato = [
            ["Cliente/Empresa", cliente_final],
            ["Representante", representante_final],
            ["Projeto", projeto],
            ["CNPJ/CPF", cnpj_cpf],
            ["Endereço", endereco],
            ["Contato", contato_final],
            ["Email", email_final]
        ]

        t = Table(dados_contato, colWidths=[1.5*inch, 2.5*inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        return t

    def _create_box_specifications_table(self, request_data):
        """Cria a tabela de especificações da caixa"""
        font_name = self._get_available_font() # Get font for tables
        
        # Dados dinâmicos do request_data ou valores padrão
        revestimento_interno = request_data.get('revestimento_interno', '')
        revestimento_externo = request_data.get('revestimento_externo', '')
        tipo_impressao = request_data.get('tipo_impressao', '')
        cores_impressao = request_data.get('cores_impressao', '')
        local_impressao = request_data.get('local_impressao', '')
        detalhes_berco = request_data.get('detalhes_berco', '')
        
        dados_caixa = [
            ["Dimensões (cm)", f"{request_data['largura_cm']} x {request_data['altura_cm']} x {request_data['profundidade_cm']} cm"],
            ["Modelo", request_data['modelo']],
            ["Material", request_data['material']],
            ["Quantidade", str(request_data['quantidade'])],
            ["Berço", "Sim" if request_data['berco'] else "Não"],
            ["Nicho", "Sim" if request_data['nicho'] else "Não"],
            ["Revestimento Interno", revestimento_interno], 
            ["Revestimento Externo", revestimento_externo],
            ["Tipo de impressão", tipo_impressao],
            ["Cores da impressão", cores_impressao],
            ["Local da impressão", local_impressao],
            ["Berço", detalhes_berco]
        ]

        t = Table(dados_caixa, colWidths=[2*inch, 5*inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        return t
    
    def _create_schedule_table(self, request_data, resultado):
        """Cria a tabela de cronograma"""
        font_name = self._get_available_font()
        
        # Dados dinâmicos do resultado ou valores padrão
        valor_unitario = resultado.get('custo_unitario', 0)
        prazo = request_data.get('prazo', '')
        pagamento = request_data.get('pagamento', '')
        manuseio = request_data.get('manuseio', '')
        prazo_brindes = request_data.get('prazo_brindes', '')
        frete = request_data.get('frete', 0)
        investimento_total = resultado.get('custo_total_projeto', 0)
        
        # Novos campos
        prazo_entrega = request_data.get('prazo_entrega', '')
        forma_pagamento = request_data.get('forma_pagamento', '')
        
        # Usar novos campos se disponíveis, senão usar os antigos
        prazo_final = prazo_entrega if prazo_entrega else prazo
        pagamento_final = forma_pagamento if forma_pagamento else pagamento
        
        dados_cronograma = [
            ["Valor unitário por caixa", f"R${valor_unitario:.2f}"],
            ["Prazo", prazo_final],
            ["Pagamento", pagamento_final],
            ["Manuseio/Montagem", manuseio],
            ["Prazo de brindes", prazo_brindes],
            ["Frete", f"R${frete:.2f}"],
            ["Investimento Total", f"R${investimento_total:.2f}"]
        ]

        t = Table(dados_cronograma, colWidths=[2*inch, 1*inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # Destacar o cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            # Destacar a linha do prazo total
            ('BACKGROUND', (0, 6), (-1, 6), colors.lightblue),
            ('FONTNAME', (0, 6), (-1, 6), font_name),
            ('FONTSIZE', (0, 6), (-1, 6), 10),
        ]))
        return t
    
    def _create_contact_schedule_tables(self, request_data, resultado):
        """Cria as tabelas de contato e cronograma lado a lado"""
        # Criar as duas tabelas
        contact_table = self._create_contact_table(request_data)
        schedule_table = self._create_schedule_table(request_data, resultado)
        
        # Criar tabela de duas colunas
        two_column_table = Table([[contact_table, schedule_table]], colWidths=[3.5*inch, 3.5*inch])
        two_column_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),  # Tabela da esquerda
            ('RIGHTPADDING', (0, 0), (0, 0), 40), # Muito mais espaço entre tabelas
            ('LEFTPADDING', (1, 0), (1, 0), 40),  # Tabela da direita bem mais à direita
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ]))
        
        return two_column_table
    
    def generate_pdf(self, request_data, resultado):
        """
        Gera um PDF com os detalhes do cálculo usando template da TOUCHÉ
        
        Args:
            request_data (dict): Dados da requisição
            resultado (dict): Resultados do cálculo
            
        Returns:
            bytes: Conteúdo do PDF em bytes
        """
        # Criar buffer em memória
        buffer = BytesIO()
        
        # Criar documento PDF no buffer com margens zero para controle total
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
        
        # Conteúdo principal
        content_story = []
        
        # Título principal
        content_story.append(Paragraph("Orçamento de Caixas", self.styles['title']))

        # Tabelas de contato e cronograma lado a lado
        content_story.append(self._create_contact_schedule_tables(request_data, resultado))
        content_story.append(Spacer(1, 10))

        # Dados da caixa
        content_story.append(self._create_box_specifications_table(request_data))
        content_story.append(Spacer(1, 20))  # Mais espaço antes do texto da empresa
        
        # Adicionar observações personalizadas se fornecidas
        observacoes = request_data.get('observacoes', '')
        if observacoes:
            content_story.append(Paragraph("Observações:", self.styles['observation']))
            content_story.append(Paragraph(observacoes, self.styles['observation']))
            content_story.append(Spacer(1, 10))
        
        # Adicionar observação de validade
        content_story.append(Paragraph("1. A confirmação formal deve ser feita via email.", self.styles['observation']))
        content_story.append(Paragraph("2. Qualquer alteração após a aprovação do projeto fica a custo do cliente.", self.styles['observation']))
        content_story.append(Paragraph("3. O atraso do pagamento ou das etapas acima citadas pode alterar o prazo final de entrega.", self.styles['observation']))
        content_story.append(Paragraph("4. Esse orçamento tem validade de 10 dias corridos após a data de envio do mesmo.", self.styles['observation']))
        content_story.append(Spacer(1, 30))

        content_story.append(Paragraph("MUNIZ E FERNANDES LTDA", self.styles['observation_centered']))
        content_story.append(Paragraph("40.874.080/0001-29", self.styles['observation_centered']))
        # Obter data atual formatada em GMT-3 (horário de Brasília)
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        data_atual = datetime.now(tz_brasil).strftime("%d de %B de %Y")
        
        # Mapear meses para português (capitalizados)
        meses_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        
        # Substituir o mês em inglês pelo português
        for mes_en, mes_pt in meses_pt.items():
            data_atual = data_atual.replace(mes_en, mes_pt)
        content_story.append(Paragraph(f"Recife, {data_atual}", self.styles['observation_centered']))

        # Aplicar template e construir documento
        template = self._create_header_footer_template()
        doc.addPageTemplates([template])
        doc.build(content_story)

        # Retornar o conteúdo do buffer
        buffer.seek(0)
        return buffer.getvalue()


# Função de conveniência para uso direto
def gerar_pdf_calculo(request_data, resultado):
    """
    Função de conveniência para gerar PDF
    
    Args:
        request_data (dict): Dados da requisição
        resultado (dict): Resultados do cálculo
        
    Returns:
        bytes: Conteúdo do PDF em bytes
    """
    generator = TouchePDFGenerator()
    return generator.generate_pdf(request_data, resultado) 