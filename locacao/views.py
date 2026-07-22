from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal

from .models import TipoVeiculo, Veiculo, ContratoLocacao, ContratoVenda, ManutencaoVeiculo, Vendedor, ComissaoVendedor, ProgramaManutencao
from .forms import (
    TipoVeiculoForm, VeiculoForm, ContratoLocacaoForm,
    DevolucaoForm, ContratoVendaForm, ManutencaoVeiculoForm, VendedorForm,
    ProgramaManutencaoForm
)
from financeiro.models import Conta, PlanoDeContas, Lancamento, Caixa


# ==========================================================
# 1. TIPOS DE VEÍCULO (GRUPOS)
# ==========================================================
@login_required
def lista_tipos_veiculo(request):
    tipos = TipoVeiculo.objects.filter(empresa=request.user.empresa)
    return render(request, 'locacao/tipo_veiculo_lista.html', {'tipos': tipos})


@login_required
def novo_tipo_veiculo(request):
    if request.method == 'POST':
        form = TipoVeiculoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Tipo de veículo criado com sucesso!")
            return redirect('locacao:lista_tipos_veiculo')
    else:
        form = TipoVeiculoForm(user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': 'Novo Tipo de Veículo',
        'url_cancelar': 'locacao:lista_tipos_veiculo'
    })


@login_required
def editar_tipo_veiculo(request, id):
    obj = get_object_or_404(TipoVeiculo, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = TipoVeiculoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de veículo atualizado!")
            return redirect('locacao:lista_tipos_veiculo')
    else:
        form = TipoVeiculoForm(instance=obj, user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': f'Editar {obj.nome}',
        'url_cancelar': 'locacao:lista_tipos_veiculo'
    })


@login_required
def excluir_tipo_veiculo(request, id):
    obj = get_object_or_404(TipoVeiculo, id=id, empresa=request.user.empresa)
    if obj.veiculo_set.exists():
        messages.error(request, "Não é possível excluir: existem veículos neste grupo.")
    else:
        obj.delete()
        messages.success(request, "Tipo excluído com sucesso.")
    return redirect('locacao:lista_tipos_veiculo')


# ==========================================================
# 2. VEÍCULOS (ESTOQUE)
# ==========================================================
@login_required
def lista_veiculos(request):
    qs = Veiculo.objects.filter(empresa=request.user.empresa)

    q = request.GET.get('q')
    status = request.GET.get('status')
    grupo_id = request.GET.get('grupo')

    if q:
        qs = qs.filter(
            Q(placa__icontains=q) |
            Q(modelo__icontains=q) |
            Q(marca__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)

    grupos = TipoVeiculo.objects.filter(empresa=request.user.empresa)

    return render(request, 'locacao/veiculo_lista.html', {
        'veiculos': qs,
        'grupos': grupos,
        'filtro_q': q,
        'filtro_status': status,
        'filtro_grupo': grupo_id,
    })


@login_required
def novo_veiculo(request):
    if request.method == 'POST':
        form = VeiculoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Veículo cadastrado com sucesso!")
            return redirect('locacao:lista_veiculos')
    else:
        form = VeiculoForm(user=request.user)
    return render(request, 'locacao/veiculo_formulario.html', {
        'form': form, 'titulo': 'Novo Veículo',
        'url_cancelar': 'locacao:lista_veiculos'
    })


@login_required
def editar_veiculo(request, id):
    obj = get_object_or_404(Veiculo, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = VeiculoForm(request.POST, request.FILES, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Veículo atualizado!")
            return redirect('locacao:lista_veiculos')
    else:
        form = VeiculoForm(instance=obj, user=request.user)
    return render(request, 'locacao/veiculo_formulario.html', {
        'form': form, 'titulo': f'Editar {obj}',
        'url_cancelar': 'locacao:lista_veiculos'
    })


@login_required
def excluir_veiculo(request, id):
    obj = get_object_or_404(Veiculo, id=id, empresa=request.user.empresa)
    if obj.contratolocacao_set.filter(status__in=['ABERTO', 'ATIVO']).exists():
        messages.error(request, "Não é possível excluir: veículo possui contrato ativo.")
    else:
        obj.delete()
        messages.success(request, "Veículo excluído com sucesso.")
    return redirect('locacao:lista_veiculos')


# ==========================================================
# 3. CONTRATOS DE LOCAÇÃO
# ==========================================================
@login_required
def lista_contratos(request):
    qs = ContratoLocacao.objects.filter(empresa=request.user.empresa)

    q = request.GET.get('q')
    status = request.GET.get('status')

    if q:
        qs = qs.filter(
            Q(numero_contrato__icontains=q) |
            Q(cliente__nome__icontains=q) |
            Q(veiculo__placa__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    return render(request, 'locacao/contrato_lista.html', {
        'contratos': qs,
        'filtro_q': q,
        'filtro_status': status,
    })


@login_required
def novo_contrato(request):
    if request.method == 'POST':
        form = ContratoLocacaoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()

            # Atualiza status do veículo
            veiculo = obj.veiculo
            veiculo.status = 'ALUGADO'
            veiculo.save()

            messages.success(request, f"Contrato {obj.numero_contrato} criado com sucesso!")
            return redirect('locacao:lista_contratos')
    else:
        form = ContratoLocacaoForm(user=request.user)
    return render(request, 'locacao/contrato_formulario.html', {
        'form': form, 'titulo': 'Novo Contrato de Locação',
        'url_cancelar': 'locacao:lista_contratos'
    })


@login_required
def editar_contrato(request, id):
    obj = get_object_or_404(ContratoLocacao, id=id, empresa=request.user.empresa)
    if obj.status not in ['ABERTO']:
        messages.error(request, "Só é possível editar contratos em aberto.")
        return redirect('locacao:lista_contratos')

    if request.method == 'POST':
        form = ContratoLocacaoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Contrato atualizado!")
            return redirect('locacao:lista_contratos')
    else:
        form = ContratoLocacaoForm(instance=obj, user=request.user)
    return render(request, 'locacao/contrato_formulario.html', {
        'form': form, 'titulo': f'Editar Contrato {obj.numero_contrato}',
        'url_cancelar': 'locacao:lista_contratos'
    })


@login_required
def iniciar_contrato(request, id):
    """Muda status para ATIVO e registra dados de saída."""
    obj = get_object_or_404(ContratoLocacao, id=id, empresa=request.user.empresa)
    if obj.status != 'ABERTO':
        messages.error(request, "Somente contratos em aberto podem ser iniciados.")
        return redirect('locacao:lista_contratos')

    obj.status = 'ATIVO'
    obj.data_saida = timezone.now()
    obj.km_saida = obj.veiculo.km_atual
    obj.tanque_saida = obj.veiculo.nivel_tanque
    obj.save()

    messages.success(request, f"Contrato {obj.numero_contrato} iniciado! Veículo retirado.")
    return redirect('locacao:lista_contratos')


@login_required
def devolucao_veiculo(request, id):
    """Tela de devolução do veículo com dados financeiros."""
    obj = get_object_or_404(ContratoLocacao, id=id, empresa=request.user.empresa)
    if obj.status != 'ATIVO':
        messages.error(request, "Somente contratos ativos podem ter devolução.")
        return redirect('locacao:lista_contratos')

    if request.method == 'POST':
        form = DevolucaoForm(request.POST)
        if form.is_valid():
            # DADOS DO VEÍCULO
            obj.data_devolucao_real = form.cleaned_data['data_devolucao']
            obj.km_chegada = form.cleaned_data['km_chegada']
            obj.tanque_chegada = form.cleaned_data['tanque_chegada']
            
            # DADOS FINANCEIROS
            obj.forma_pagamento_devolucao = form.cleaned_data['forma_pagamento']
            obj.valor_desconto_devolucao = form.cleaned_data.get('valor_desconto', 0) or 0
            obj.valor_pago = form.cleaned_data.get('valor_pago', 0) or 0
            obj.observacoes_financeiras = form.cleaned_data.get('observacoes_financeiras', '')
            
            # ============================================================
            # CÁLCULO DO VALOR TOTAL DA LOCAÇÃO
            # ============================================================
            dias = obj.dias_locacao
            
            # 1. Valor base (diária × dias)
            valor_base = obj.valor_total_dia * dias
            
            # 2. Cálculo de KM extra (se aplicável)
            km_percorridos = (obj.km_chegada or 0) - (obj.km_saida or 0)
            # Exemplo: acima de 300km/dia, cobra R$ 0,50 por km extra
            km_limite = dias * 300  # Limite: 300km por dia
            km_extra = max(0, km_percorridos - km_limite)
            valor_km_extra = Decimal(km_extra) * Decimal('0.50')
            
            # 3. Total = Base + KM Extra - Desconto
            obj.valor_total_locacao = valor_base + valor_km_extra - obj.valor_desconto_devolucao
            
            obj.status = 'FINALIZADO'

            # Atualiza KM e tanque do veículo
            veiculo = obj.veiculo
            veiculo.km_atual = obj.km_chegada
            veiculo.nivel_tanque = obj.tanque_chegada
            veiculo.status = 'DISPONIVEL'
            veiculo.save()

            # Adiciona observação se houver
            obs_dev = form.cleaned_data.get('observacoes_devolucao', '')
            if obs_dev:
                obj.observacoes = f"{obj.observacoes}\n[Devolução] {obs_dev}".strip()

            obj.save()

            # ============================================================
            # GERAÇÃO DO FINANCEIRO
            # ============================================================
            if obj.valor_total_locacao > 0:
                # Busca ou cria Plano de Contas para Locação
                plano_locacao, _ = PlanoDeContas.objects.get_or_create(
                    empresa=request.user.empresa,
                    codigo='LOC001',
                    defaults={'nome': 'Receita de Locação', 'tipo': 'R'}
                )

                # Monta descrição detalhada
                desc_completa = (
                    f"Locação {obj.numero_contrato} - {obj.cliente.nome}\n"
                    f"Veículo: {obj.veiculo.marca} {obj.veiculo.modelo} ({obj.veiculo.placa})\n"
                    f"Período: {obj.data_saida.strftime('%d/%m/%Y')} a {obj.data_devolucao_real.strftime('%d/%m/%Y')} ({dias} dia(s))\n"
                    f"KM Percorridos: {km_percorridos} km"
                )
                if km_extra > 0:
                    desc_completa += f"\nKM Extra: {km_extra} km (R$ {valor_km_extra:.2f})"
                if obj.observacoes_financeiras:
                    desc_completa += f"\n{obj.observacoes_financeiras}"

                # Formas de Pagamento que são À VISTA (geram Lançamento direto)
                FORMAS_A_VISTA = ['AVISTA', 'PIX', 'CARTAO_DEBITO']
                
                if obj.forma_pagamento_devolucao in FORMAS_A_VISTA:
                    # ============================================================
                    # À VISTA → LANÇAMENTO DIRETO NO FLUXO DE CAIXA
                    # ============================================================
                    caixa_padrao = Caixa.objects.filter(empresa=request.user.empresa).first()
                    
                    if caixa_padrao:
                        Lancamento.objects.create(
                            empresa=request.user.empresa,
                            caixa=caixa_padrao,
                            plano_de_contas=plano_locacao,
                            data_lancamento=obj.data_devolucao_real.date(),
                            descricao=desc_completa,
                            valor=obj.valor_total_locacao,
                            tipo='C'  # Crédito (Receita)
                        )
                        msg_financeiro = "Lançamento registrado no Fluxo de Caixa."
                    else:
                        msg_financeiro = "Atenção: Nenhum Caixa configurado. Lançamento não gerado."
                else:
                    # ============================================================
                    # PRAZO → CONTA A RECEBER
                    # ============================================================
                    Conta.objects.create(
                        empresa=request.user.empresa,
                        descricao=f"Locação {obj.numero_contrato} - {obj.cliente.nome} ({dias} dia(s))",
                        plano_de_contas=plano_locacao,
                        cadastro=obj.cliente,
                        valor=obj.valor_total_locacao,
                        data_vencimento=obj.data_devolucao_real.date(),
                        status='PENDENTE',
                        documento=obj.numero_contrato,
                        observacoes=desc_completa
                    )
                    msg_financeiro = "Conta a Receber gerada no Financeiro."
            else:
                msg_financeiro = "Valor zero - nenhum lançamento gerado."

            # Monta mensagem de sucesso
            msg_km = f" | KM Extra: {km_extra}km" if km_extra > 0 else ""
            messages.success(
                request, 
                f"Devolução realizada! Contrato {obj.numero_contrato} finalizado. "
                f"Total: R$ {obj.valor_total_locacao:.2f} ({dias} dia(s){msg_km}). {msg_financeiro}"
            )
            return redirect('locacao:lista_contratos')
    else:
        form = DevolucaoForm()

    return render(request, 'locacao/devolucao.html', {
        'form': form, 'contrato': obj
    })


@login_required
def cancelar_contrato(request, id):
    """Cancela um contrato e libera o veículo."""
    obj = get_object_or_404(ContratoLocacao, id=id, empresa=request.user.empresa)
    if obj.status in ['FINALIZADO', 'CANCELADO']:
        messages.error(request, "Não é possível cancelar este contrato.")
        return redirect('locacao:lista_contratos')

    # Libera o veículo
    obj.veiculo.status = 'DISPONIVEL'
    obj.veiculo.save()

    obj.status = 'CANCELADO'
    obj.save()

    messages.success(request, f"Contrato {obj.numero_contrato} cancelado.")
    return redirect('locacao:lista_contratos')


# ==========================================================
# 4. CONTRATOS DE VENDA
# ==========================================================
@login_required
def lista_vendas(request):
    qs = ContratoVenda.objects.filter(empresa=request.user.empresa).select_related('vendedor')

    q = request.GET.get('q')
    status = request.GET.get('status')
    pagamento = request.GET.get('pagamento')

    if q:
        qs = qs.filter(
            Q(numero_contrato__icontains=q) |
            Q(cliente__nome__icontains=q) |
            Q(veiculo__placa__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if pagamento:
        qs = qs.filter(forma_pagamento=pagamento)

    return render(request, 'locacao/venda_lista.html', {
        'vendas': qs,
        'filtro_q': q,
        'filtro_status': status,
        'filtro_pagamento': pagamento,
    })


@login_required
def nova_venda(request):
    if request.method == 'POST':
        form = ContratoVendaForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa

            # Registra KM na venda
            obj.km_venda = obj.veiculo.km_atual
            obj.save()

            # Atualiza status do veículo
            veiculo = obj.veiculo
            veiculo.status = 'VENDIDO'
            veiculo.save()

            # ============================================================
            # GERAÇÃO DO FINANCEIRO
            # ============================================================
            msg_financeiro = ""
            if obj.valor_venda > 0:
                # Busca ou cria Plano de Contas para Vendas
                plano_venda, _ = PlanoDeContas.objects.get_or_create(
                    empresa=request.user.empresa,
                    codigo='VEN001',
                    defaults={'nome': 'Receita de Venda de Veículos', 'tipo': 'R'}
                )

                desc_completa = (
                    f"Venda {obj.numero_contrato} - {obj.cliente.nome}\n"
                    f"Veículo: {obj.veiculo.marca} {obj.veiculo.modelo} ({obj.veiculo.placa})\n"
                    f"KM: {obj.km_venda} km"
                )

                FORMAS_A_VISTA = ['AVISTA', 'PIX', 'CARTAO_DEBITO']

                if obj.forma_pagamento in FORMAS_A_VISTA:
                    # À VISTA → LANÇAMENTO DIRETO NO FLUXO DE CAIXA
                    caixa_padrao = Caixa.objects.filter(empresa=request.user.empresa).first()
                    if caixa_padrao:
                        Lancamento.objects.create(
                            empresa=request.user.empresa,
                            caixa=caixa_padrao,
                            plano_de_contas=plano_venda,
                            data_lancamento=obj.data_venda,
                            descricao=desc_completa,
                            valor=obj.valor_venda,
                            tipo='C'
                        )
                        msg_financeiro = "Lançamento registrado no Fluxo de Caixa."
                    else:
                        msg_financeiro = "Atenção: Nenhum Caixa configurado. Lançamento não gerado."
                else:
                    # PRAZO → CONTA A RECEBER (gera parcelas)
                    from datetime import timedelta
                    import calendar

                    total_parcelas = obj.parcelas if obj.parcelas > 0 else 1
                    valor_financiado = obj.valor_financeado

                    for i in range(total_parcelas):
                        # Calcula vencimento de cada parcela
                        if obj.data_vencimento_primeira:
                            data_venc = obj.data_vencimento_primeira + timedelta(days=30 * i)
                        else:
                            data_venc = obj.data_venda + timedelta(days=30 * (i + 1))

                        Conta.objects.create(
                            empresa=request.user.empresa,
                            descricao=f"Venda {obj.numero_contrato} - Parcela {i+1}/{total_parcelas} - {obj.cliente.nome}",
                            plano_de_contas=plano_venda,
                            cadastro=obj.cliente,
                            valor=obj.valor_parcela,
                            data_vencimento=data_venc,
                            status='PENDENTE',
                            documento=f"{obj.numero_contrato} ({i+1}/{total_parcelas})",
                            observacoes=desc_completa
                        )

                    msg_financeiro = f"{total_parcelas} parcela(s) gerada(s) no Financeiro."

            # Registra comissão do vendedor se houver
            if obj.vendedor and obj.valor_venda > 0:
                comissao_valor = Decimal('0')
                if obj.vendedor.comissao_percentual > 0:
                    comissao_valor = (obj.valor_venda * obj.vendedor.comissao_percentual) / Decimal('100')
                elif obj.vendedor.comissao_valor_fixo > 0:
                    comissao_valor = obj.vendedor.comissao_valor_fixo

                if comissao_valor > 0:
                    ComissaoVendedor.objects.create(
                        empresa=request.user.empresa,
                        vendedor=obj.vendedor,
                        contrato_venda=obj,
                        data_venda=obj.data_venda,
                        valor_venda=obj.valor_venda,
                        percentual_comissao=obj.vendedor.comissao_percentual,
                        valor_comissao=comissao_valor,
                        observacoes=f"Comissão pela venda {obj.numero_contrato}"
                    )
                    obj.vendedor.total_vendas += 1
                    obj.vendedor.valor_total_vendas += obj.valor_venda
                    obj.vendedor.total_comissoes += comissao_valor
                    obj.vendedor.save()

            messages.success(
                request,
                f"Venda {obj.numero_contrato} registrada com sucesso! {msg_financeiro}"
            )
            return redirect('locacao:lista_vendas')
    else:
        form = ContratoVendaForm(user=request.user)

    # Dados dos veículos para preenchimento automático no JS
    veiculos_data = {}
    for v in Veiculo.objects.filter(empresa=request.user.empresa, status='DISPONIVEL'):
        veiculos_data[v.id] = {
            'valor_venda': float(v.valor_venda),
            'km_atual': v.km_atual,
        }

    import json
    return render(request, 'locacao/venda_formulario.html', {
        'form': form, 'titulo': 'Nova Venda de Veículo',
        'url_cancelar': 'locacao:lista_vendas',
        'veiculos_data': json.dumps(veiculos_data),
    })


@login_required
def cancelar_venda(request, id):
    """Cancela uma venda e devolve o veículo ao estoque."""
    obj = get_object_or_404(ContratoVenda, id=id, empresa=request.user.empresa)
    if obj.status == 'CANCELADO':
        messages.error(request, "Esta venda já está cancelada.")
        return redirect('locacao:lista_vendas')

    obj.veiculo.status = 'DISPONIVEL'
    obj.veiculo.save()

    # Cancela Contas a Receber vinculadas
    contas = Conta.objects.filter(
        empresa=request.user.empresa,
        documento__icontains=obj.numero_contrato
    )
    qtd_contas = contas.count()
    contas.update(status='CANCELADA')

    # Cancela comissões
    comissoes = ComissaoVendedor.objects.filter(
        empresa=request.user.empresa,
        contrato_venda=obj
    )
    for com in comissoes:
        com.vendedor.total_vendas -= 1
        com.vendedor.valor_total_vendas -= com.valor_venda
        com.vendedor.total_comissoes -= com.valor_comissao
        com.vendedor.save()
    comissoes.delete()

    obj.status = 'CANCELADO'
    obj.save()

    msg_fin = ""
    if qtd_contas > 0:
        msg_fin = f" {qtd_contas} parcela(s) no financeiro foram cancelada(s)."

    messages.success(request, f"Venda {obj.numero_contrato} cancelada.{msg_fin}")
    return redirect('locacao:lista_vendas')


# ==========================================================
# 5. MANUTENÇÕES
# ==========================================================
@login_required
def lista_manutencoes(request):
    qs = ManutencaoVeiculo.objects.filter(empresa=request.user.empresa)

    veiculo_id = request.GET.get('veiculo')
    status = request.GET.get('status')

    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if status:
        qs = qs.filter(status=status)

    veiculos = Veiculo.objects.filter(empresa=request.user.empresa)

    return render(request, 'locacao/manutencao_lista.html', {
        'manutencoes': qs,
        'veiculos': veiculos,
        'filtro_veiculo': veiculo_id,
        'filtro_status': status,
    })


@login_required
def nova_manutencao(request):
    if request.method == 'POST':
        form = ManutencaoVeiculoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Manutencao registrada com sucesso!")
            return redirect('locacao:lista_manutencoes')
    else:
        form = ManutencaoVeiculoForm(user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': 'Nova Manutencao',
        'url_cancelar': 'locacao:lista_manutencoes'
    })


@login_required
def editar_manutencao(request, id):
    obj = get_object_or_404(ManutencaoVeiculo, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = ManutencaoVeiculoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Manutencao atualizada!")
            return redirect('locacao:lista_manutencoes')
    else:
        form = ManutencaoVeiculoForm(instance=obj, user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': 'Editar Manutencao',
        'url_cancelar': 'locacao:lista_manutencoes'
    })


@login_required
def excluir_manutencao(request, id):
    obj = get_object_or_404(ManutencaoVeiculo, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Manutencao excluida!")
        return redirect('locacao:lista_manutencoes')
    return render(request, 'locacao/confirmar_exclusao.html', {
        'obj': obj, 'url_cancelar': 'locacao:lista_manutencoes'
    })


# ==========================================================
# 5.1 PROGRAMAS DE MANUTENCAO PREVENTIVA
# ==========================================================
@login_required
def lista_programas(request):
    qs = ProgramaManutencao.objects.filter(empresa=request.user.empresa)
    tipo_veiculo_id = request.GET.get('tipo_veiculo')
    if tipo_veiculo_id:
        qs = qs.filter(tipo_veiculo_id=tipo_veiculo_id)
    tipos_veiculo = TipoVeiculo.objects.filter(empresa=request.user.empresa)
    return render(request, 'locacao/programa_lista.html', {
        'programas': qs,
        'tipos_veiculo': tipos_veiculo,
        'filtro_tipo_veiculo': tipo_veiculo_id,
    })


@login_required
def novo_programa(request):
    if request.method == 'POST':
        form = ProgramaManutencaoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Programa de manutencao criado com sucesso!")
            return redirect('locacao:lista_programas')
    else:
        form = ProgramaManutencaoForm(user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': 'Novo Programa de Manutencao',
        'url_cancelar': 'locacao:lista_programas'
    })


@login_required
def editar_programa(request, id):
    obj = get_object_or_404(ProgramaManutencao, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = ProgramaManutencaoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Programa atualizado!")
            return redirect('locacao:lista_programas')
    else:
        form = ProgramaManutencaoForm(instance=obj, user=request.user)
    return render(request, 'locacao/formulario_simples.html', {
        'form': form, 'titulo': 'Editar Programa de Manutencao',
        'url_cancelar': 'locacao:lista_programas'
    })


@login_required
def excluir_programa(request, id):
    obj = get_object_or_404(ProgramaManutencao, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Programa excluido!")
        return redirect('locacao:lista_programas')
    return render(request, 'locacao/confirmar_exclusao.html', {
        'obj': obj, 'url_cancelar': 'locacao:lista_programas'
    })


# ==========================================================
# 5.2 PROXIMAS MANUTENCOES (ALERTAS)
# ==========================================================
@login_required
def proximas_manutencoes(request):
    empresa = request.user.empresa
    from datetime import timedelta
    hoje = timezone.now().date()

    veiculos = Veiculo.objects.filter(empresa=empresa)
    alertas = []

    for veiculo in veiculos:
        programas = ProgramaManutencao.objects.filter(
            empresa=empresa, tipo_veiculo=veiculo.grupo, ativo=True
        )
        for programa in programas:
            ultima = ManutencaoVeiculo.objects.filter(
                empresa=empresa, veiculo=veiculo,
                tipo_servico__icontains=programa.tipo_servico
            ).order_by('-data_entrada').first()

            km_atual = veiculo.km_atual
            if not ultima:
                continue

            proximo_km = 0
            km_restante = 999999
            proxima_data = None
            dias_restante = 999999

            if programa.km_intervalo > 0:
                proximo_km = ultima.km_na_manutencao + programa.km_intervalo
                km_restante = proximo_km - km_atual

            if programa.dias_intervalo > 0:
                proxima_data = ultima.data_entrada + timedelta(days=programa.dias_intervalo)
                dias_restante = (proxima_data - hoje).days

            eh_proximo_km = 0 <= km_restante <= 500
            eh_proximo_tempo = proxima_data and 0 <= dias_restante <= 30
            eh_vencido = km_restante < 0 or (proxima_data and dias_restante < 0)

            if eh_proximo_km or eh_proximo_tempo or eh_vencido:
                alertas.append({
                    'veiculo': veiculo,
                    'programa': programa,
                    'ultima_manutencao': ultima,
                    'km_atual': km_atual,
                    'proximo_km': proximo_km,
                    'km_restante': km_restante,
                    'proxima_data': proxima_data,
                    'dias_restante': dias_restante,
                    'status': 'VENCIDO' if eh_vencido else 'PROXIMO',
                    'tipo_alerta': 'KM' if eh_vencido or eh_proximo_km else 'DATA',
                })

    alertas.sort(key=lambda x: (0 if x['status'] == 'VENCIDO' else 1, x['km_restante']))
    return render(request, 'locacao/proximas_manutencoes.html', {'alertas': alertas})


# ==========================================================
# 5.3 RELATORIO DE MANUTENCOES
# ==========================================================
@login_required
def relatorio_manutencoes(request):
    empresa = request.user.empresa
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    veiculo_id = request.GET.get('veiculo')
    tipo_servico = request.GET.get('tipo_servico')

    qs = ManutencaoVeiculo.objects.filter(empresa=empresa)

    if data_inicio:
        qs = qs.filter(data_entrada__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_entrada__lte=data_fim)
    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if tipo_servico:
        qs = qs.filter(tipo_servico__icontains=tipo_servico)

    from django.db.models import Sum, Count

    total_manutencoes = qs.count()
    valor_total = qs.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    valor_medio = valor_total / total_manutencoes if total_manutencoes > 0 else 0

    por_tipo = qs.values('tipo_servico').annotate(
        total=Count('id'), valor=Sum('valor_total')
    ).order_by('-valor')

    por_oficina = qs.exclude(oficina='').values('oficina').annotate(
        total=Count('id'), valor=Sum('valor_total')
    ).order_by('-valor')

    veiculos = Veiculo.objects.filter(empresa=empresa)

    return render(request, 'locacao/relatorio_manutencoes.html', {
        'manutencoes': qs,
        'total_manutencoes': total_manutencoes,
        'valor_total': valor_total,
        'valor_medio': valor_medio,
        'por_tipo': por_tipo,
        'por_oficina': por_oficina,
        'veiculos': veiculos,
    })


# ==========================================================
# 6. VENDEDORES
# ==========================================================
@login_required
def lista_vendedores(request):
    qs = Vendedor.objects.filter(empresa=request.user.empresa)

    q = request.GET.get('q')
    status = request.GET.get('status')

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cpf__icontains=q) |
            Q(email__icontains=q)
        )
    if status:
        qs = qs.filter(situacao=status)

    return render(request, 'locacao/vendedor_lista.html', {
        'vendedores': qs,
        'filtro_q': q,
        'filtro_status': status,
    })


@login_required
def novo_vendedor(request):
    if request.method == 'POST':
        form = VendedorForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Vendedor cadastrado com sucesso!")
            return redirect('locacao:lista_vendedores')
    else:
        form = VendedorForm(user=request.user)
    return render(request, 'locacao/vendedor_formulario.html', {
        'form': form, 'titulo': 'Novo Vendedor',
        'url_cancelar': 'locacao:lista_vendedores'
    })


@login_required
def editar_vendedor(request, id):
    obj = get_object_or_404(Vendedor, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = VendedorForm(request.POST, request.FILES, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendedor atualizado com sucesso!")
            return redirect('locacao:lista_vendedores')
    else:
        form = VendedorForm(instance=obj, user=request.user)
    return render(request, 'locacao/vendedor_formulario.html', {
        'form': form, 'titulo': f'Editar {obj.nome}',
        'url_cancelar': 'locacao:lista_vendedores'
    })


@login_required
def excluir_vendedor(request, id):
    obj = get_object_or_404(Vendedor, id=id, empresa=request.user.empresa)
    
    # Verifica se há comissões vinculadas
    if obj.comissaovendedor_set.exists():
        messages.error(request, "Não é possível excluir: existem comissões vinculadas a este vendedor.")
    else:
        obj.delete()
        messages.success(request, "Vendedor excluído com sucesso.")
    return redirect('locacao:lista_vendedores')


@login_required
def toggle_vendedor(request, id):
    """Ativa/Inativa um vendedor."""
    obj = get_object_or_404(Vendedor, id=id, empresa=request.user.empresa)
    obj.situacao = 'INATIVO' if obj.situacao == 'ATIVO' else 'ATIVO'
    obj.save()
    status_msg = "ativado" if obj.situacao == 'ATIVO' else "inativado"
    messages.success(request, f"Vendedor {obj.nome} {status_msg} com sucesso!")
    return redirect('locacao:lista_vendedores')


# ==========================================================
# 6. RELATÓRIOS
# ==========================================================
@login_required
def relatorio_vendas(request):
    """Relatório de vendas com filtros por período, status e forma de pagamento."""
    from datetime import date

    qs = ContratoVenda.objects.filter(empresa=request.user.empresa).select_related('cliente', 'veiculo', 'vendedor')

    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')
    pagamento = request.GET.get('pagamento', '')

    if data_inicio:
        qs = qs.filter(data_venda__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_venda__lte=data_fim)
    if status:
        qs = qs.filter(status=status)
    if pagamento:
        qs = qs.filter(forma_pagamento=pagamento)

    # Totais
    total_vendas = qs.count()
    total_valor = sum(v.valor_venda for v in qs)
    total_entrada = sum(v.valor_entrada for v in qs)
    total_financeado = sum(v.valor_financeado for v in qs)

    # Quebra por status
    qtd_pendente = qs.filter(status='PENDENTE').count()
    qtd_pago = qs.filter(status='PAGO').count()
    qtd_cancelado = qs.filter(status='CANCELADO').count()

    # Quebra por forma de pagamento
    por_pagamento = {}
    for v in qs:
        fp = v.get_forma_pagamento_display()
        if fp not in por_pagamento:
            por_pagamento[fp] = {'qtd': 0, 'valor': 0}
        por_pagamento[fp]['qtd'] += 1
        por_pagamento[fp]['valor'] += v.valor_venda

    return render(request, 'locacao/relatorio_vendas.html', {
        'empresa': request.user.empresa,
        'vendas': qs,
        'total_vendas': total_vendas,
        'total_valor': total_valor,
        'total_entrada': total_entrada,
        'total_financeado': total_financeado,
        'qtd_pendente': qtd_pendente,
        'qtd_pago': qtd_pago,
        'qtd_cancelado': qtd_cancelado,
        'por_pagamento': por_pagamento,
        'filtro_data_inicio': data_inicio,
        'filtro_data_fim': data_fim,
        'filtro_status': status,
        'filtro_pagamento': pagamento,
    })


@login_required
def relatorio_vendedores(request):
    """Relatório de vendas por vendedor com comissões."""
    from datetime import date

    qs = Vendedor.objects.filter(empresa=request.user.empresa)

    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    vendedores = []
    for v in qs:
        vendas_qs = ContratoVenda.objects.filter(
            empresa=request.user.empresa, vendedor=v, status__in=['PENDENTE', 'PAGO']
        )
        if data_inicio:
            vendas_qs = vendas_qs.filter(data_venda__gte=data_inicio)
        if data_fim:
            vendas_qs = vendas_qs.filter(data_venda__lte=data_fim)

        qtd = vendas_qs.count()
        valor_total = sum(x.valor_venda for x in vendas_qs)
        comissoes_qs = ComissaoVendedor.objects.filter(
            empresa=request.user.empresa, vendedor=v
        )
        if data_inicio:
            comissoes_qs = comissoes_qs.filter(data_venda__gte=data_inicio)
        if data_fim:
            comissoes_qs = comissoes_qs.filter(data_venda__lte=data_fim)

        total_comissao = sum(c.valor_comissao for c in comissoes_qs)

        vendedores.append({
            'vendedor': v,
            'qtd_vendas': qtd,
            'valor_total': valor_total,
            'total_comissao': total_comissao,
        })

    # Totais gerais
    total_vendas_geral = sum(x['qtd_vendas'] for x in vendedores)
    total_valor_geral = sum(x['valor_total'] for x in vendedores)
    total_comissao_geral = sum(x['total_comissao'] for x in vendedores)

    return render(request, 'locacao/relatorio_vendedores.html', {
        'empresa': request.user.empresa,
        'vendedores': vendedores,
        'total_vendas_geral': total_vendas_geral,
        'total_valor_geral': total_valor_geral,
        'total_comissao_geral': total_comissao_geral,
        'filtro_data_inicio': data_inicio,
        'filtro_data_fim': data_fim,
    })


@login_required
def relatorio_locacoes(request):
    """Relatório de locações com filtros por período e status."""
    qs = ContratoLocacao.objects.filter(empresa=request.user.empresa).select_related('cliente', 'veiculo')

    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')

    if data_inicio:
        qs = qs.filter(data_reserva__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_reserva__lte=data_fim)
    if status:
        qs = qs.filter(status=status)

    total_contratos = qs.count()
    total_valor_dia = sum(c.valor_total_dia for c in qs)
    total_locacao = sum(c.valor_total_locacao for c in qs)

    # Quebra por status
    qtd_aberto = qs.filter(status='ABERTO').count()
    qtd_ativo = qs.filter(status='ATIVO').count()
    qtd_finalizado = qs.filter(status='FINALIZADO').count()
    qtd_cancelado = qs.filter(status='CANCELADO').count()

    # Quebra por pagamento
    por_pagamento = {}
    for c in qs:
        fp = c.get_forma_pagamento_devolucao_display() if c.forma_pagamento_devolucao else 'Não informado'
        if fp not in por_pagamento:
            por_pagamento[fp] = {'qtd': 0, 'valor': 0}
        por_pagamento[fp]['qtd'] += 1
        por_pagamento[fp]['valor'] += c.valor_total_locacao

    return render(request, 'locacao/relatorio_locacoes.html', {
        'empresa': request.user.empresa,
        'contratos': qs,
        'total_contratos': total_contratos,
        'total_valor_dia': total_valor_dia,
        'total_locacao': total_locacao,
        'qtd_aberto': qtd_aberto,
        'qtd_ativo': qtd_ativo,
        'qtd_finalizado': qtd_finalizado,
        'qtd_cancelado': qtd_cancelado,
        'por_pagamento': por_pagamento,
        'filtro_data_inicio': data_inicio,
        'filtro_data_fim': data_fim,
        'filtro_status': status,
    })
