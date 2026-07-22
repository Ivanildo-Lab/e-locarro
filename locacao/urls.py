from django.urls import path
from . import views

app_name = 'locacao'

urlpatterns = [
    # TIPOS DE VEÍCULO
    path('tipos/', views.lista_tipos_veiculo, name='lista_tipos_veiculo'),
    path('tipos/novo/', views.novo_tipo_veiculo, name='novo_tipo_veiculo'),
    path('tipos/editar/<int:id>/', views.editar_tipo_veiculo, name='editar_tipo_veiculo'),
    path('tipos/excluir/<int:id>/', views.excluir_tipo_veiculo, name='excluir_tipo_veiculo'),

    # VEÍCULOS
    path('veiculos/', views.lista_veiculos, name='lista_veiculos'),
    path('veiculos/novo/', views.novo_veiculo, name='novo_veiculo'),
    path('veiculos/editar/<int:id>/', views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/excluir/<int:id>/', views.excluir_veiculo, name='excluir_veiculo'),

    # CONTRATOS DE LOCAÇÃO
    path('contratos/', views.lista_contratos, name='lista_contratos'),
    path('contratos/novo/', views.novo_contrato, name='novo_contrato'),
    path('contratos/editar/<int:id>/', views.editar_contrato, name='editar_contrato'),
    path('contratos/iniciar/<int:id>/', views.iniciar_contrato, name='iniciar_contrato'),
    path('contratos/devolver/<int:id>/', views.devolucao_veiculo, name='devolucao_veiculo'),
    path('contratos/cancelar/<int:id>/', views.cancelar_contrato, name='cancelar_contrato'),

    # VENDAS
    path('vendas/', views.lista_vendas, name='lista_vendas'),
    path('vendas/nova/', views.nova_venda, name='nova_venda'),
    path('vendas/cancelar/<int:id>/', views.cancelar_venda, name='cancelar_venda'),

    # MANUTENÇÕES
    path('manutencoes/', views.lista_manutencoes, name='lista_manutencoes'),
    path('manutencoes/nova/', views.nova_manutencao, name='nova_manutencao'),
    path('manutencoes/editar/<int:id>/', views.editar_manutencao, name='editar_manutencao'),
    path('manutencoes/excluir/<int:id>/', views.excluir_manutencao, name='excluir_manutencao'),

    # PROGRAMAS DE MANUTENÇÃO
    path('programas/', views.lista_programas, name='lista_programas'),
    path('programas/novo/', views.novo_programa, name='novo_programa'),
    path('programas/editar/<int:id>/', views.editar_programa, name='editar_programa'),
    path('programas/excluir/<int:id>/', views.excluir_programa, name='excluir_programa'),

    # ALERTAS
    path('proximas-manutencoes/', views.proximas_manutencoes, name='proximas_manutencoes'),

    # VENDEDORES
    path('vendedores/', views.lista_vendedores, name='lista_vendedores'),
    path('vendedores/novo/', views.novo_vendedor, name='novo_vendedor'),
    path('vendedores/editar/<int:id>/', views.editar_vendedor, name='editar_vendedor'),
    path('vendedores/excluir/<int:id>/', views.excluir_vendedor, name='excluir_vendedor'),
    path('vendedores/toggle/<int:id>/', views.toggle_vendedor, name='toggle_vendedor'),

    # RELATÓRIOS
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('relatorios/vendedores/', views.relatorio_vendedores, name='relatorio_vendedores'),
    path('relatorios/locacoes/', views.relatorio_locacoes, name='relatorio_locacoes'),
    path('relatorios/manutencoes/', views.relatorio_manutencoes, name='relatorio_manutencoes'),
]
