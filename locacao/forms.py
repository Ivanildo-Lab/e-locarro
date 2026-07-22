from django import forms
from .models import TipoVeiculo, Veiculo, ContratoLocacao, ContratoVenda, ManutencaoVeiculo, Vendedor, ProgramaManutencao
from cadastros.models import Cadastro


class TipoVeiculoForm(forms.ModelForm):
    class Meta:
        model = TipoVeiculo
        fields = '__all__'
        exclude = ['empresa']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'


class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = '__all__'
        exclude = ['empresa', 'status']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

        if self.user:
            self.fields['grupo'].queryset = TipoVeiculo.objects.filter(empresa=self.user.empresa)

    def clean_placa(self):
        placa = self.cleaned_data.get('placa', '').upper()
        if self.user and placa:
            existe = Veiculo.objects.filter(
                empresa=self.user.empresa, placa=placa
            ).exclude(id=self.instance.id).exists()
            if existe:
                raise forms.ValidationError("Já existe um veículo com esta placa.")
        return placa


class ContratoLocacaoForm(forms.ModelForm):
    class Meta:
        model = ContratoLocacao
        fields = '__all__'
        exclude = ['empresa', 'numero_contrato', 'data_reserva', 'data_devolucao_real', 'km_saida', 'tanque_saida', 'km_chegada', 'tanque_chegada', 'valor_total_dia', 'status']
        widgets = {
            'data_saida': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'data_retorno_prevista': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Estilização
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

        if self.user:
            self.fields['cliente'].queryset = Cadastro.objects.filter(
                empresa=self.user.empresa
            ).filter(papel='CLI')
            self.fields['veiculo'].queryset = Veiculo.objects.filter(
                empresa=self.user.empresa, status='DISPONIVEL'
            )


class DevolucaoForm(forms.Form):
    """Formulário para devolução de veículo com dados financeiros."""
    
    # DADOS DO VEÍCULO
    data_devolucao = forms.DateTimeField(
        label="Data/Hora Devolução",
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'})
    )
    km_chegada = forms.IntegerField(label="KM Chegada")
    tanque_chegada = forms.IntegerField(
        label="Tanque Chegada (0-8)",
        min_value=0, max_value=8
    )
    
    # DADOS FINANCEIROS
    forma_pagamento = forms.ChoiceField(
        label="Forma de Pagamento",
        choices=[
            ('AVISTA', 'À Vista'),
            ('PIX', 'PIX'),
            ('CARTAO_CREDITO', 'Cartão de Crédito'),
            ('CARTAO_DEBITO', 'Cartão de Débito'),
            ('CREDIARIO', 'Crediário'),
            ('BOLETO', 'Boleto'),
        ],
        initial='AVISTA'
    )
    valor_desconto = forms.DecimalField(
        label="Desconto (R$)",
        max_digits=10, decimal_places=2, initial=0,
        required=False
    )
    valor_pago = forms.DecimalField(
        label="Valor Pago (R$)",
        max_digits=12, decimal_places=2, initial=0,
        required=False
    )
    observacoes_financeiras = forms.CharField(
        label="Observações Financeiras",
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )
    
    # OBSERVAÇÕES GERAIS
    observacoes_devolucao = forms.CharField(
        label="Observações da Devolução",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'


class ContratoVendaForm(forms.ModelForm):
    class Meta:
        model = ContratoVenda
        fields = '__all__'
        exclude = ['empresa', 'numero_contrato', 'status', 'valor_parcela']
        widgets = {
            'data_venda': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_vencimento_primeira': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'valor_venda': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_entrada': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

        if self.user:
            self.fields['cliente'].queryset = Cadastro.objects.filter(
                empresa=self.user.empresa
            ).filter(papel='CLI')
            self.fields['veiculo'].queryset = Veiculo.objects.filter(
                empresa=self.user.empresa, status='DISPONIVEL'
            )
            self.fields['vendedor'].queryset = Vendedor.objects.filter(
                empresa=self.user.empresa, situacao='ATIVO'
            )


class ManutencaoVeiculoForm(forms.ModelForm):
    class Meta:
        model = ManutencaoVeiculo
        fields = '__all__'
        exclude = ['empresa']
        widgets = {
            'data_entrada': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_saida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'pecas_utilizadas': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'garantia_ate': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

        if self.user:
            self.fields['veiculo'].queryset = Veiculo.objects.filter(
                empresa=self.user.empresa
            )
            if 'programa' in self.fields:
                self.fields['programa'].queryset = ProgramaManutencao.objects.filter(
                    empresa=self.user.empresa, ativo=True
                )


class ProgramaManutencaoForm(forms.ModelForm):
    class Meta:
        model = ProgramaManutencao
        fields = '__all__'
        exclude = ['empresa', 'ativo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

        if self.user:
            self.fields['tipo_veiculo'].queryset = TipoVeiculo.objects.filter(
                empresa=self.user.empresa
            )


class VendedorForm(forms.ModelForm):
    class Meta:
        model = Vendedor
        fields = '__all__'
        exclude = ['empresa', 'situacao', 'total_vendas', 'valor_total_vendas', 'total_comissoes']
        widgets = {
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors'

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        if self.user and cpf:
            existe = Vendedor.objects.filter(
                empresa=self.user.empresa, cpf=cpf
            ).exclude(id=self.instance.id).exists()
            if existe:
                raise forms.ValidationError("Já existe um vendedor com este CPF.")
        return cpf
