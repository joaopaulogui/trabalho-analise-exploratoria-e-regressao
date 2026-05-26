from dash import Dash, html, dcc, Output, Input, callback
import plotly.express as px
import pandas as pd

app = Dash()

df = pd.read_csv("data_cts_intentional_homicide.csv")
df_clean = df[
    (df['Sex'] == 'Total') &
    (df['Age'] == 'Total') &
    (df['Dimension'] == 'Total') &
    (df['Category'] == 'Total') &
    (df['Unit of measurement'] == 'Counts') &
    (df['Indicator'].str.startswith("Victims"))

].copy()

# colunas necessarias
colunas_manter = ['Iso3_code', 'Country', 'Year', 'VALUE']
df_clean = df_clean[colunas_manter]

df_clean['Year'] = df_clean['Year'].astype(int)

df_clean['VALUE'] = pd.to_numeric(df_clean['VALUE'], errors='coerce')

df_clean.head()

# Descobre o ano mínimo e máximo geral do dataset
ano_min = df_clean['Year'].min()
ano_max = df_clean['Year'].max()

# extrai a lista única de países e seus nomes
paises_unicos = df_clean[['Iso3_code', 'Country']].drop_duplicates()

print(f"Ano mínimo: {ano_min}")
print(f"Ano máximo: {ano_max}")

paises_unicos.head()

# Cria um produto cartesiano (Cross Join): Todos os países x Todos os anos
grid_indices = pd.MultiIndex.from_product(
    [paises_unicos['Iso3_code'], range(ano_min, ano_max + 1)],
    names=['Iso3_code', 'Year']
)
df_grid = pd.DataFrame(index=grid_indices).reset_index()


# bota nome do país de volta para o grid
df_grid = pd.merge(df_grid, paises_unicos, on='Iso3_code', how='left')

# Left Join com os dados reais de homicídios
df_completo = pd.merge(df_grid, df_clean, on=['Iso3_code', 'Country', 'Year'], how='left')

# Aplica a interpolação linear agrupando ESTRITAMENTE por país
df_completo['VALUE'] = df_completo.groupby('Iso3_code')['VALUE'].transform(
    lambda x: x.interpolate(method='linear', limit_direction='both')
)

print(df_completo.head(10))

from sklearn.linear_model import LinearRegression

# gerando os Lags
df_completo = df_completo.sort_values(by=['Iso3_code', 'Year']).reset_index(drop=True)
df_completo['VALUE_Lag1'] = df_completo.groupby('Iso3_code')['VALUE'].shift(1)
df_completo['VALUE_Lag2'] = df_completo.groupby('Iso3_code')['VALUE'].shift(2)

lista_resultados_finais = []

paises_unicos_lista = df_completo['Iso3_code'].unique()

for pais in paises_unicos_lista:
    # 1. Filtra os dados apenas do país atual
    df_pais = df_completo[df_completo['Iso3_code'] == pais].copy()
    nome_pais = df_pais['Country'].iloc[0]

    # 2. Separa os dados históricos válidos (sem NaNs nos Lags) para o treino
    df_treino = df_pais.dropna(subset=['VALUE_Lag1', 'VALUE_Lag2']).copy()

    # Se o país tiver pouquíssimos dados históricos, pulamos para evitar quebra matemática
    if len(df_treino) < 3:
        continue

    # Variáveis preditoras (X) e Alvo (y)
    X_treino = df_treino[['VALUE_Lag1', 'VALUE_Lag2']]
    y_treino = df_treino['VALUE']

    # 3. Treina o modelo de regressão linear para ESTE país
    modelo = LinearRegression()
    modelo.fit(X_treino, y_treino)

    # 4. Loop de Previsão Recursiva (Escadinha) para 2023 a 2026
    # Vamos criar as linhas futuras iterativamente
    anos_futuros = [2023, 2024, 2025, 2026]

    for ano in anos_futuros:
        # Pega a última linha disponível no dataframe do país para descobrir os Lags
        ultima_linha = df_pais.iloc[-1]

        # O Lag 1 para o novo ano é o 'VALUE' da última linha cadastrada
        lag1_atual = ultima_linha['VALUE']
        # O Lag 2 para o novo ano é o 'VALUE_Lag1' da última linha cadastrada
        lag2_atual = ultima_linha['VALUE_Lag1']

        # Monta o vetor de características para o modelo prever
        X_novo = pd.DataFrame([[lag1_atual, lag2_atual]], columns=['VALUE_Lag1', 'VALUE_Lag2'])

        # O modelo faz a previsão do número de homicídios
        predicao = modelo.predict(X_novo)[0]

        # Garante que a previsão não seja um número negativo (homicídios não podem ser menores que zero)
        predicao = max(0.0, predicao)

        # Cria uma nova linha para anexar ao dataframe do país
        nova_linha = pd.DataFrame([{
            'Iso3_code': pais,
            'Year': ano,
            'Country': nome_pais,
            'VALUE': round(predicao, 1), # Salva a previsão na coluna principal
            'VALUE_Lag1': lag1_atual,
            'VALUE_Lag2': lag2_atual
        }])

        # Adiciona a linha de previsão ao histórico do país para servir de base para o próximo ano
        df_pais = pd.concat([df_pais, nova_linha], ignore_index=True)

    # Guarda o dataframe completo do país (histórico + previsões de 23 a 26) na nossa lista
    lista_resultados_finais.append(df_pais)

# 5. Consolidação: Junta os dataframes de todos os países de volta em um só
df_previsoes_finais = pd.concat(lista_resultados_finais, ignore_index=True)

print("Previsões concluídas com sucesso!")

# Visualizando o resultado final das projeções de um país específico como exemplo (ex: Aruba)
print("\nResultado final com as projeções (2023-2026) anexadas:")
print(df_previsoes_finais[df_previsoes_finais['Iso3_code'] == 'ABW'].head(20))

df_previsoes_finais.tail()


# Criando gráfico de linha
tabela_linha = df_previsoes_finais[["Country", "VALUE", "Year"]]
grafico_linha = px.line(
    tabela_linha,
    x="Year",
    y="VALUE",
    title="Taxa de homicídio"
)

app.layout = html.Div(children=[
    dcc.Dropdown(
        options=[{'label': pais, 'value': pais} for pais in paises_unicos["Country"]],
        value='Brazil',
        id='dropdown',
    ),

    dcc.Graph(
        id="grafico_de_linha",
        figure=grafico_linha,
    ),
])

@callback(
    Output('grafico_de_linha','figure'),
    Input('dropdown', 'value')
)
def update_output(valor_atualizado):
    tabela_linha_atualizada = df_previsoes_finais[["Country", "VALUE", "Year"]]
    tabela_linha_atualizada = tabela_linha[tabela_linha["Country"] == valor_atualizado]
    grafico_linha_atualizado = px.line(
        tabela_linha_atualizada,
        x="Year",
        y="VALUE",
        title=f"Taxa de homicídio - {valor_atualizado}"
    )


    return grafico_linha_atualizado

if __name__ == '__main__':
    app.run(debug=True)