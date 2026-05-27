# Projeto Analítico: Taxas de Homicídio

Este repositório contém o trabalho da faculdade focado na análise, tratamento e projeção de dados sobre homicídios intencionais. O projeto está dividido em duas entregas principais.

##  Entregas

**1. Notebook de Análise**
* **Arquivo:** `questoes.ipynb`
* Contém a resolução de 10 questões analíticas, documentando o raciocínio e a exploração inicial do dataset.

**2. Data App (Dashboard Interativo)**
* **Arquivo:** `data_app.py`
* Uma aplicação web construída em Dash. O script realiza a limpeza dos dados, resolve lacunas históricas via interpolação, projeta cenários futuros (2023-2026) usando Regressão Linear e disponibiliza um gráfico interativo filtrável por país.

---

##  Como executar o Data App

Para garantir flexibilidade, você pode iniciar a aplicação de duas maneiras. Escolha a que melhor se adequa ao seu fluxo de trabalho atual.

### Opção 1: Execução Local 
Ideal para testar modificações no código rapidamente. Você precisará instalar as bibliotecas base utilizadas no processamento e na interface.

Execute o seguinte comando no seu terminal:
```bash
pip install dash plotly pandas scikit-learn
```

Em seguida, inicie a aplicação:
```bash
python data_app.py
```
O dashboard ficará disponível no seu navegador no endereço: `http://127.0.0.1:8050/`
