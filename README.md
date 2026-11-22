# Trabalho final AED II

Mapeamento e análise da malha ferroviária brasileira com o intuito de desenvolver um algoritmo de otimização da expansão das vias.

Link do dataset Zenodo: [https://zenodo.org/records/24450092](https://zenodo.org/records/24450092)

O dataset foi gerado com o código gerador.py, que utiliza 3 milhões como valor de restauração de via e 15 milhões como valor para a construção de uma linha nova.

As novas linhas foram propostas com base nos fluxos Origem-Destino (OD) agroindustriais e minerais (soja, milho e minério de ferro), priorizando as conexões com maior Índice de Retorno sobre Investimento (ROI) ancoradas à malha ferroviária existente.

## Como Executar (Linux / Ubuntu 24.04)

# 1. Clonar o repositório
git clone https://github.com/ThalesGuerreiro/Trabalho-final-aedii.git
cd Trabalho-final-aedii

# 2. Baixar o dataset tratado (vertices.csv e arestas.csv) do Zenodo (https://zenodo.org/records/24450092)
# e colocar os arquivos na raiz do projeto (ou dentro da pasta dados/)

# 3. Executar a otimização e gerar os resultados
python3 main.py

Saídas geradas

Terminal: Tabelas de análise de sensibilidade por orçamento (R$ 2 bi a R$ 50 bi) e comparativo de estratégias (custo_minimo, roi_agro, roi_minerio e roi_total) no cenário de R$ 10 bilhões.

Gráficos: grafico_orcamentos_3.png e mapa_expansao_10bi_3.png.
