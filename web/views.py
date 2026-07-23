from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta, date
from cadastros.models import Cadastro
from financeiro.models import Lancamento, Conta
from locacao.models import Veiculo, ContratoLocacao, ContratoVenda, Vendedor, ManutencaoVeiculo, ProgramaManutencao

# ==========================================
# LANDING PAGE (Tela Inicial)
# ==========================================
def home(request):
    """Tela de entrada (antes do login ou home do sistema)"""
    return render(request, 'web/home.html')


# ==========================================
# DASHBOARD (Painel Principal)
# ==========================================
@login_required
def dashboard(request):
    empresa = request.user.empresa
    hoje = timezone.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # 1. DADOS DE CADASTROS
    # Filtra apenas quem é Cliente (CLI) ou Ambos (AMB)
    qs_clientes = Cadastro.objects.filter(
        empresa=empresa
    ).filter(Q(papel='CLI') | Q(papel='AMB'))

    total_clientes = qs_clientes.count()
    ativos = qs_clientes.filter(situacao='ATIVO').count()
    
    # 2. DADOS FINANCEIROS (REALIZADO / FLUXO)
    # Soma apenas o que foi BAIXADO/PAGO neste mês
    
    # Receitas (Créditos)
    receita_mensal = Lancamento.objects.filter(
        empresa=empresa,
        tipo='C', 
        data_lancamento__month=mes_atual,
        data_lancamento__year=ano_atual
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # Despesas (Débitos) - Vem negativo do banco
    despesa_mensal_raw = Lancamento.objects.filter(
        empresa=empresa,
        tipo='D', 
        data_lancamento__month=mes_atual,
        data_lancamento__year=ano_atual
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # Saldo Real (Soma direta pois despesa é negativa)
    saldo_mes = receita_mensal + despesa_mensal_raw

    # 3. LISTAS DE ALERTA
    ultimos_pagamentos = Lancamento.objects.filter(
        empresa=empresa, 
        tipo='C'
    ).order_by('-data_lancamento')[:5]

    contas_atrasadas = Conta.objects.filter(
        empresa=empresa,
        plano_de_contas__tipo='R', # Só queremos saber de receber
        status='PENDENTE',
        data_vencimento__lt=hoje
    ).order_by('data_vencimento')[:5]

    # 4. DADOS PARA O GRÁFICO (Últimos 6 meses)
    labels_grafico = []
    dados_receita = []
    dados_despesa = []
    
    for i in range(5, -1, -1):
        data_ref = hoje.replace(day=1) - timedelta(days=i*30)
        mes_ref = data_ref.month
        ano_ref = data_ref.year
        
        labels_grafico.append(f"{mes_ref:02d}/{ano_ref}")
        
        r = Lancamento.objects.filter(
            empresa=empresa, tipo='C', 
            data_lancamento__month=mes_ref, data_lancamento__year=ano_ref
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        d = Lancamento.objects.filter(
            empresa=empresa, tipo='D', 
            data_lancamento__month=mes_ref, data_lancamento__year=ano_ref
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        dados_receita.append(float(r))
        dados_despesa.append(abs(float(d)))

    # 5. DADOS DE LOCAÇÃO
    locacoes_ativas = ContratoLocacao.objects.filter(
        empresa=empresa, status='ATIVO'
    ).count()

    locacoes_mes = ContratoLocacao.objects.filter(
        empresa=empresa,
        data_reserva__month=mes_atual,
        data_reserva__year=ano_atual
    ).count()

    receita_locacoes_mes = ContratoLocacao.objects.filter(
        empresa=empresa,
        status='FINALIZADO',
        data_devolucao_real__month=mes_atual,
        data_devolucao_real__year=ano_atual
    ).aggregate(Sum('valor_total_locacao'))['valor_total_locacao__sum'] or 0

    ultimas_locacoes = ContratoLocacao.objects.filter(
        empresa=empresa
    ).select_related('cliente', 'veiculo').order_by('-data_reserva')[:5]

    # 6. DADOS DE VENDA
    vendas_mes = ContratoVenda.objects.filter(
        empresa=empresa,
        data_venda__month=mes_atual,
        data_venda__year=ano_atual
    ).count()

    receita_vendas_mes = ContratoVenda.objects.filter(
        empresa=empresa,
        status='PAGO',
        data_venda__month=mes_atual,
        data_venda__year=ano_atual
    ).aggregate(Sum('valor_venda'))['valor_venda__sum'] or 0

    ultimas_vendas = ContratoVenda.objects.filter(
        empresa=empresa
    ).select_related('cliente', 'veiculo', 'vendedor').order_by('-data_venda')[:5]

    # 7. ESTOQUE DE VEÍCULOS
    veiculos_total = Veiculo.objects.filter(empresa=empresa).count()
    veiculos_disponiveis = Veiculo.objects.filter(empresa=empresa, status='DISPONIVEL').count()
    veiculos_alugados = Veiculo.objects.filter(empresa=empresa, status='ALUGADO').count()
    veiculos_vendidos = Veiculo.objects.filter(empresa=empresa, status='VENDIDO').count()
    veiculos_manutencao = Veiculo.objects.filter(empresa=empresa, status='MANUTENCAO').count()

    # 8. TOP VENDEDORES
    top_vendedores = Vendedor.objects.filter(
        empresa=empresa, situacao='ATIVO'
    ).order_by('-valor_total_vendas')[:5]

    # 9. MANUTENCOES PENDENTES
    manutencoes_pendentes = ManutencaoVeiculo.objects.filter(
        empresa=empresa, status__in=['PENDENTE', 'EM_ANDAMENTO']
    ).select_related('veiculo')[:5]

    # 10. ALERTAS DE MANUTENCAO PREVENTIVA
    veiculos_empresa = Veiculo.objects.filter(empresa=empresa)
    alertas_manutencao = []

    for veiculo in veiculos_empresa:
        programas = ProgramaManutencao.objects.filter(
            empresa=empresa, tipo_veiculo=veiculo.grupo, ativo=True
        )
        for programa in programas:
            ultima = ManutencaoVeiculo.objects.filter(
                empresa=empresa, veiculo=veiculo,
                tipo_servico__icontains=programa.tipo_servico
            ).order_by('-data_entrada').first()

            if not ultima:
                continue

            km_atual = veiculo.km_atual
            km_restante = 999999
            dias_restante = 999999
            proximo_km = 0
            proxima_data = None

            if programa.km_intervalo > 0:
                proximo_km = ultima.km_na_manutencao + programa.km_intervalo
                km_restante = proximo_km - km_atual

            if programa.dias_intervalo > 0:
                proxima_data = ultima.data_entrada + timedelta(days=programa.dias_intervalo)
                dias_restante = (proxima_data - hoje).days

            eh_vencido = km_restante < 0 or (proxima_data and dias_restante < 0)
            eh_proximo = (0 <= km_restante <= 500) or (proxima_data and 0 <= dias_restante <= 30)

            if eh_vencido or eh_proximo:
                alertas_manutencao.append({
                    'veiculo': veiculo,
                    'servico': programa.tipo_servico,
                    'km_restante': km_restante,
                    'dias_restante': dias_restante,
                    'proxima_data': proxima_data,
                    'status': 'VENCIDO' if eh_vencido else 'PROXIMO',
                })

    alertas_manutencao.sort(key=lambda x: (0 if x['status'] == 'VENCIDO' else 1, x['km_restante']))
    total_alertas_vencidos = len([a for a in alertas_manutencao if a['status'] == 'VENCIDO'])
    total_alertas_proximos = len([a for a in alertas_manutencao if a['status'] == 'PROXIMO'])

    # 11. CUSTO MANUTENCAO MES
    custo_manutencao_mes = ManutencaoVeiculo.objects.filter(
        empresa=empresa,
        data_entrada__month=mes_atual,
        data_entrada__year=ano_atual
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0

    context = {
        'total_clientes': total_clientes,
        'ativos': ativos,
        'receita_mensal': receita_mensal,
        'despesa_mensal': abs(despesa_mensal_raw),
        'saldo': saldo_mes,
        'ultimos_pagamentos': ultimos_pagamentos,
        'contas_atrasadas': contas_atrasadas,
        'grafico_labels': labels_grafico,
        'grafico_receita': dados_receita,
        'grafico_despesa': dados_despesa,
        # Locação
        'locacoes_ativas': locacoes_ativas,
        'locacoes_mes': locacoes_mes,
        'receita_locacoes_mes': receita_locacoes_mes,
        'ultimas_locacoes': ultimas_locacoes,
        # Vendas
        'vendas_mes': vendas_mes,
        'receita_vendas_mes': receita_vendas_mes,
        'ultimas_vendas': ultimas_vendas,
        # Veículos
        'veiculos_total': veiculos_total,
        'veiculos_disponiveis': veiculos_disponiveis,
        'veiculos_alugados': veiculos_alugados,
        'veiculos_vendidos': veiculos_vendidos,
        'veiculos_manutencao': veiculos_manutencao,
        # Vendedores
        'top_vendedores': top_vendedores,
        # Manutenção
        'manutencoes_pendentes': manutencoes_pendentes,
        'alertas_manutencao': alertas_manutencao[:10],
        'total_alertas_vencidos': total_alertas_vencidos,
        'total_alertas_proximos': total_alertas_proximos,
        'custo_manutencao_mes': custo_manutencao_mes,
    }
    
    return render(request, 'web/dashboard.html', context)