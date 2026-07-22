from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import ModeloSaaS
from cadastros.models import Cadastro
from decimal import Decimal
import random


class TipoVeiculo(ModeloSaaS):
    """Categorias de veículos: SUV, Sedã, Hatch, etc."""
    nome = models.CharField(max_length=100, verbose_name="Nome do Grupo")
    valor_diaria_padrao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Valor Diária Padrão (R$)"
    )
    valor_mensal_padrao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Valor Mensal Padrão (R$)"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de Veículo"
        verbose_name_plural = "Tipos de Veículos"
        ordering = ['nome']
        unique_together = [['empresa', 'nome']]


class Veiculo(ModeloSaaS):
    """Estoque de veículos da empresa."""
    STATUS_CHOICES = [
        ('DISPONIVEL', 'Disponível'),
        ('ALUGADO', 'Alugado'),
        ('VENDIDO', 'Vendido'),
        ('MANUTENCAO', 'Em Manutenção'),
    ]

    MARCAS_CHOICES = [
        ('CHEVROLET', 'Chevrolet'),
        ('FIAT', 'Fiat'),
        ('FORD', 'Ford'),
        ('HONDA', 'Honda'),
        ('HYUNDAI', 'Hyundai'),
        ('JEEP', 'Jeep'),
        ('KIA', 'Kia'),
        ('NISSAN', 'Nissan'),
        ('PEUGEOT', 'Peugeot'),
        ('RENAULT', 'Renault'),
        ('TOYOTA', 'Toyota'),
        ('VOLKSWAGEN', 'Volkswagen'),
        ('OUTRA', 'Outra'),
    ]

    # Identificação
    placa = models.CharField(max_length=10, verbose_name="Placa")
    renavam = models.CharField(max_length=20, blank=True, verbose_name="Renavam")
    chassi = models.CharField(max_length=20, blank=True, verbose_name="Chassi")

    # Dados do Veículo
    marca = models.CharField(max_length=20, choices=MARCAS_CHOICES, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    ano_fabricacao = models.IntegerField(verbose_name="Ano Fabricação")
    ano_modelo = models.IntegerField(verbose_name="Ano Modelo", null=True, blank=True)
    cor = models.CharField(max_length=50, verbose_name="Cor")
    grupo = models.ForeignKey(
        TipoVeiculo, on_delete=models.PROTECT, verbose_name="Grupo/Tipo"
    )

    # Controle
    km_atual = models.IntegerField(default=0, verbose_name="KM Atual")
    nivel_tanque = models.IntegerField(
        default=8,
        validators=[MinValueValidator(0), MaxValueValidator(8)],
        verbose_name="Nível do Tanque (0-8)"
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default='DISPONIVEL'
    )

    # Valores
    valor_compra = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor de Compra (R$)"
    )
    valor_venda = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor de Venda (R$)"
    )

    # Controle
    foto = models.ImageField(upload_to='veiculos/', null=True, blank=True)
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['marca', 'modelo']
        unique_together = [['empresa', 'placa']]


class ContratoLocacao(ModeloSaaS):
    """Contrato de locação de veículo."""
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto (Reservado)'),
        ('ATIVO', 'Ativo (Veículo Retirado)'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('AVISTA', 'À Vista'),
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('CREDIARIO', 'Crediário'),
        ('BOLETO', 'Boleto'),
    ]

    # Número do Contrato (auto-gerado)
    numero_contrato = models.CharField(
        max_length=20, unique=True, verbose_name="Nº Contrato"
    )

    # Clientes e Veículos
    cliente = models.ForeignKey(
        Cadastro, on_delete=models.PROTECT, verbose_name="Cliente"
    )
    veiculo = models.ForeignKey(
        Veiculo, on_delete=models.PROTECT, verbose_name="Veículo"
    )

    # Datas
    data_reserva = models.DateTimeField(auto_now_add=True, verbose_name="Data da Reserva")
    data_saida = models.DateTimeField(
        null=True, blank=True, verbose_name="Data/Hora Saída"
    )
    data_retorno_prevista = models.DateTimeField(
        verbose_name="Data/Hora Retorno Previsto"
    )
    data_devolucao_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Data/Hora Devolução Real"
    )

    # Locais
    local_retirada = models.CharField(
        max_length=255, default="Matriz", verbose_name="Local de Retirada"
    )
    local_devolucao = models.CharField(
        max_length=255, default="Matriz", verbose_name="Local de Devolução"
    )

    # KM e Combustível
    km_saida = models.IntegerField(default=0, null=True, blank=True, verbose_name="KM Saída")
    km_chegada = models.IntegerField(
        null=True, blank=True, verbose_name="KM Chegada"
    )
    tanque_saida = models.IntegerField(
        default=8, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(8)],
        verbose_name="Tanque Saída (0-8)"
    )
    tanque_chegada = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(8)],
        verbose_name="Tanque Chegada (0-8)"
    )

    # Valores
    valor_diaria = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Diária (R$)"
    )
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Desconto (%)"
    )
    desconto_valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Desconto (R$)"
    )

    # Taxas e Seguros
    protecao_casco = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Proteção Carro Casco (R$)"
    )
    premio_rcf = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Prêmio Diário RCF (R$)"
    )
    limpeza_garantia = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Limpeza Garantia (R$)"
    )
    taxa_aluguel = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Taxa de Aluguel (R$)"
    )

    # Valor Total Calculado
    valor_total_dia = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Valor Total Dia (R$)", editable=False
    )

    # Pagamento
    deposito_garantia = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Depósito em Garantia (R$)"
    )
    forma_pagamento = models.CharField(
        max_length=20, choices=FORMA_PAGAMENTO_CHOICES,
        default='AVISTA', verbose_name="Forma de Pagamento"
    )
    reserva_codigo = models.CharField(
        max_length=20, blank=True, verbose_name="Código da Reserva"
    )

    # Status
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default='ABERTO'
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    # ============================================================
    # DADOS FINANCEIROS DA DEVOLUÇÃO (preenchidos na entrega)
    # ============================================================
    forma_pagamento_devolucao = models.CharField(
        max_length=20, choices=FORMA_PAGAMENTO_CHOICES,
        blank=True, null=True, verbose_name="Forma Pgto na Devolução"
    )
    valor_desconto_devolucao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Desconto na Devolução (R$)"
    )
    valor_total_locacao = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor Total da Locação (R$)", editable=False
    )
    valor_pago = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor Pago (R$)"
    )
    observacoes_financeiras = models.TextField(
        blank=True, verbose_name="Observações Financeiras"
    )

    def save(self, *args, **kwargs):
        # Gera número do contrato se não existir
        if not self.numero_contrato:
            self.numero_contrato = self._gerar_numero_contrato()

        # Calcula valor total do dia
        self.valor_total_dia = (
            self.valor_diaria
            - self.desconto_valor
            + self.protecao_casco
            + self.premio_rcf
            + self.limpeza_garantia
            + self.taxa_aluguel
        )

        # Calcula valor total da locação se estiver finalizado
        if self.status == 'FINALIZADO' and self.data_saida and self.data_devolucao_real:
            dias = self.dias_locacao
            self.valor_total_locacao = (self.valor_total_dia * dias) - self.valor_desconto_devolucao

        super().save(*args, **kwargs)

    def _gerar_numero_contrato(self):
        """Gera número único de contrato tipo GYNA000000"""
        while True:
            codigo = f"LOC{random.randint(100000, 999999)}"
            if not ContratoLocacao.objects.filter(
                numero_contrato=codigo
            ).exists():
                return codigo

    @property
    def dias_locacao(self):
        """Calcula a quantidade de dias de locação."""
        if self.data_saida and self.data_devolucao_real:
            delta = self.data_devolucao_real - self.data_saida
            return max(delta.days, 1)
        elif self.data_saida and self.data_retorno_prevista:
            delta = self.data_retorno_prevista - self.data_saida
            return max(delta.days, 1)
        return 0

    def __str__(self):
        return f"{self.numero_contrato} - {self.cliente.nome} ({self.veiculo})"

    class Meta:
        verbose_name = "Contrato de Locação"
        verbose_name_plural = "Contratos de Locação"
        ordering = ['-data_reserva']


class ContratoVenda(ModeloSaaS):
    """Contrato de venda de veículo."""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('CANCELADO', 'Cancelado'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('AVISTA', 'À Vista'),
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('FINANCIADO', 'Financiado'),
        ('CREDIARIO', 'Crediário'),
        ('PERMUTA', 'Permuta'),
    ]

    numero_contrato = models.CharField(
        max_length=20, unique=True, verbose_name="Nº Contrato"
    )

    cliente = models.ForeignKey(
        Cadastro, on_delete=models.PROTECT, verbose_name="Cliente"
    )
    veiculo = models.ForeignKey(
        Veiculo, on_delete=models.PROTECT, verbose_name="Veículo"
    )

    data_venda = models.DateField(verbose_name="Data da Venda")
    valor_venda = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Valor da Venda (R$)"
    )
    forma_pagamento = models.CharField(
        max_length=20, choices=FORMA_PAGAMENTO_CHOICES,
        default='AVISTA', verbose_name="Forma de Pagamento"
    )

    # Dados do Veículo no Momento da Venda
    km_venda = models.IntegerField(default=0, verbose_name="KM na Venda")

    # Dados do Vendedor
    vendedor = models.ForeignKey(
        'Vendedor', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Vendedor"
    )

    # Dados de Pagamento
    valor_entrada = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor da Entrada (R$)"
    )
    parcelas = models.PositiveIntegerField(
        default=1, verbose_name="Nº de Parcelas"
    )
    valor_parcela = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor da Parcela (R$)"
    )
    data_vencimento_primeira = models.DateField(
        null=True, blank=True, verbose_name="Vencimento 1ª Parcela"
    )

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='PENDENTE'
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def save(self, *args, **kwargs):
        if not self.numero_contrato:
            self.numero_contrato = self._gerar_numero_contrato()

        # Calcula valor da parcela automaticamente
        if self.parcelas and self.parcelas > 0:
            valor_financiado = self.valor_venda - self.valor_entrada
            if valor_financiado < 0:
                valor_financiado = 0
            self.valor_parcela = valor_financiado / self.parcelas
        else:
            self.valor_parcela = 0

        super().save(*args, **kwargs)

    def _gerar_numero_contrato(self):
        while True:
            codigo = f"VND{random.randint(100000, 999999)}"
            if not ContratoVenda.objects.filter(
                numero_contrato=codigo
            ).exists():
                return codigo

    def __str__(self):
        return f"{self.numero_contrato} - {self.cliente.nome} ({self.veiculo})"

    @property
    def valor_financeado(self):
        """Valor financiado = valor total - entrada."""
        return max(self.valor_venda - self.valor_entrada, 0)

    @property
    def is_a_vista(self):
        """Verifica se a forma de pagamento é à vista."""
        return self.forma_pagamento in ['AVISTA', 'PIX', 'CARTAO_DEBITO']

    class Meta:
        verbose_name = "Contrato de Venda"
        verbose_name_plural = "Contratos de Venda"
        ordering = ['-data_venda']


class ManutencaoVeiculo(ModeloSaaS):
    """Histórico de manutenções dos veículos."""
    veiculo = models.ForeignKey(
        Veiculo, on_delete=models.CASCADE, verbose_name="Veículo"
    )
    data_entrada = models.DateField(verbose_name="Data Entrada")
    data_saida = models.DateField(
        null=True, blank=True, verbose_name="Data Saída"
    )
    tipo_servico = models.CharField(max_length=100, verbose_name="Tipo de Serviço")
    descricao = models.TextField(verbose_name="Descrição do Serviço")
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor (R$)"
    )
    oficina = models.CharField(max_length=200, blank=True, verbose_name="Oficina/Mecânico")

    def __str__(self):
        return f"{self.veiculo} - {self.tipo_servico} ({self.data_entrada})"

    class Meta:
        verbose_name = "Manutenção de Veículo"
        verbose_name_plural = "Manutenções de Veículos"
        ordering = ['-data_entrada']


class Vendedor(ModeloSaaS):
    """Cadastro de vendedores para controle de vendas e comissões."""
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo'),
    ]

    # Dados Pessoais
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    data_nascimento = models.DateField(
        null=True, blank=True, verbose_name="Data de Nascimento"
    )
    
    # Contato
    email = models.EmailField(max_length=254, blank=True, verbose_name="E-mail")
    celular = models.CharField(max_length=20, blank=True, verbose_name="Celular")
    telefone_fixo = models.CharField(max_length=20, blank=True, verbose_name="Telefone Fixo")
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")
    endereco = models.CharField(max_length=255, blank=True, verbose_name="Endereço")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    uf = models.CharField(max_length=2, blank=True, verbose_name="UF")
    
    # Dados Profissionais
    matricula = models.CharField(max_length=20, blank=True, verbose_name="Matrícula")
    comissao_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Comissão Padrão (%)",
        help_text="Percentual de comissão sobre vendas"
    )
    comissao_valor_fixo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Comissão Valor Fixo (R$)",
        help_text="Valor fixo por venda (se aplicável)"
    )
    
    # Controle
    situacao = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ATIVO'
    )
    foto = models.ImageField(upload_to='vendedores/', null=True, blank=True)
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Estatísticas (atualizadas automaticamente)
    total_vendas = models.IntegerField(default=0, verbose_name="Total de Vendas")
    valor_total_vendas = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Valor Total em Vendas (R$)"
    )
    total_comissoes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Total de Comissões (R$)"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        ordering = ['nome']
        unique_together = [['empresa', 'cpf']]


class ComissaoVendedor(ModeloSaaS):
    """Registro de comissões geradas por venda."""
    vendedor = models.ForeignKey(
        Vendedor, on_delete=models.PROTECT, verbose_name="Vendedor"
    )
    contrato_venda = models.ForeignKey(
        'ContratoVenda', on_delete=models.PROTECT, verbose_name="Contrato de Venda"
    )
    
    data_venda = models.DateField(verbose_name="Data da Venda")
    valor_venda = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Valor da Venda (R$)"
    )
    percentual_comissao = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentual (%)"
    )
    valor_comissao = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Comissão (R$)"
    )
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGA', 'Paga'),
        ('CANCELADA', 'Cancelada'),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='PENDENTE'
    )
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def __str__(self):
        return f"{self.vendedor.nome} - R$ {self.valor_comissao:.2f} ({self.status})"

    class Meta:
        verbose_name = "Comissão de Vendedor"
        verbose_name_plural = "Comissões de Vendedores"
        ordering = ['-data_venda']
