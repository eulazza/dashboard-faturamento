import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from datetime import datetime

# Carregar dados
df = pd.read_csv('Vendas.csv', delimiter=',')

# Converter valores monetários para float
def converter_valor(valor):
    if pd.isnull(valor) or str(valor).strip() == '' or str(valor) == 'R$ 0,00':
        return 0.0
    try:
        valor_str = str(valor).replace('R$', '').replace('.', '').replace(',', '.')
        return float(valor_str)
    except:
        return 0.0

colunas_valores = df.columns[1:-1]  # Excluir a coluna 'Total geral'
df[colunas_valores] = df[colunas_valores].applymap(converter_valor)

# Derreter dataframe
df_melted = df.melt(id_vars=['Nome do Produto'], value_vars=colunas_valores, 
                    var_name='Periodo', value_name='Faturamento')

# Converter 'Periodo' para datetime (ajuste para meses em português)
meses_pt = {
    'janeiro': 'January', 'fevereiro': 'February', 'março': 'March', 'abril': 'April',
    'maio': 'May', 'junho': 'June', 'julho': 'July', 'agosto': 'August',
    'setembro': 'September', 'outubro': 'October', 'novembro': 'November', 'dezembro': 'December'
}

def converter_periodo(periodo):
    if pd.isnull(periodo):
        return None
    try:
        mes, ano = periodo.lower().split(' / ')
        mes_en = meses_pt[mes]
        return pd.to_datetime(f'{mes_en} {ano}', format='%B %Y')
    except:
        return None

df_melted['Periodo'] = df_melted['Periodo'].apply(converter_periodo)

# Ordenar por data
df_melted = df_melted.dropna(subset=['Periodo']).sort_values('Periodo')

# Criar uma sequência completa de meses
data_min = df_melted['Periodo'].min()
data_max = df_melted['Periodo'].max()
todos_meses = pd.date_range(start=data_min, end=data_max, freq='MS')

# Função para criar dataframe com todos os meses
def completar_meses(dados_produto):
    if dados_produto.empty:
        return dados_produto
    df_completo = pd.DataFrame({'Periodo': todos_meses})
    df_completo = df_completo.merge(dados_produto, on='Periodo', how='left').fillna(0)
    return df_completo

# Iniciar app Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Dashboard de Faturamento'),

    html.Div([
        html.Label('Selecione o Produto:'),
        dcc.Dropdown(
            options=[{'label': prod, 'value': prod} for prod in df['Nome do Produto'].unique()],
            value=df['Nome do Produto'].iloc[0],
            id='produto-dropdown'
        ),
    ], style={'width': '48%', 'display': 'inline-block'}),

    html.Div([
        html.Label('Tipo de Gráfico:'),
        dcc.Dropdown(
            options=[
                {'label': 'Linha', 'value': 'line'},
                {'label': 'Barras', 'value': 'bar'}
            ],
            value='line',
            id='tipo-grafico-dropdown'
        ),
    ], style={'width': '48%', 'display': 'inline-block', 'paddingLeft': '20px'}),

    dcc.Graph(id='grafico-faturamento'),
    html.Div(id='total-faturado', style={'fontSize': 20, 'fontWeight': 'bold', 'marginTop': 20})
])

@app.callback(
    [Output('grafico-faturamento', 'figure'), Output('total-faturado', 'children')],
    [Input('produto-dropdown', 'value'), Input('tipo-grafico-dropdown', 'value')]
)
def atualizar_grafico(produto_selecionado, tipo_grafico):
    # Filtrar dados do produto
    dados_produto = df_melted[df_melted['Nome do Produto'] == produto_selecionado].copy()
    
    # Completar com todos os meses
    dados_produto = completar_meses(dados_produto)
    
    # Calcular total
    total_faturamento = dados_produto['Faturamento'].sum()
    
    # Criar gráfico
    if tipo_grafico == 'line':
        fig = px.line(dados_produto, x='Periodo', y='Faturamento', markers=True,
                     title=f'Faturamento de {produto_selecionado}')
    else:
        fig = px.bar(dados_produto, x='Periodo', y='Faturamento',
                    title=f'Faturamento de {produto_selecionado}')
    
    # Configurar layout
    fig.update_layout(
        xaxis_title='Mês',
        yaxis_title='Faturamento (R$)',
        xaxis={'tickformat': '%b/%Y', 'dtick': 'M1'},  # Mostra todos os meses
        yaxis={'tickformat': ',.2f'},
        showlegend=True
    )
    
    # Garantir que todos os meses apareçam
    fig.update_xaxes(
        range=[todos_meses.min(), todos_meses.max()],
        tickmode='array',
        tickvals=todos_meses,
        ticktext=[d.strftime('%b/%Y') for d in todos_meses]
    )

    return fig, f'Total Faturado: R$ {total_faturamento:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)