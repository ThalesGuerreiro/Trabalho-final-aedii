import csv
import os
import solver_malha
import visualizacao


PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_PROJETO, "dados")

def carregar_dados():
    caminho_vertices = os.path.join(PASTA_DADOS, "vertices.csv")
    caminho_arestas = os.path.join(PASTA_DADOS, "arestas.csv")

    vertices = {}

    with open(caminho_vertices, "r", encoding="utf-8", newline="") as arq_v:
        for linha in csv.DictReader(arq_v):
            id_v = int(linha["id"])

            vertices[id_v] = {
                "codigo_original": linha["codigo_original"],
                "codigo_muni": linha["codigo_muni"],
                "nome": linha["nome"],
                "uf": linha["uf"],
                "lat": float(linha["lat"]),
                "lon": float(linha["lon"]),
                "eh_porto": bool(int(linha["eh_porto"])),
                "demanda_ferr_agro_ton": float(linha["demanda_ferr_agro_ton"]),
                "demanda_ferr_min_ton": float(linha["demanda_ferr_min_ton"]),
                "demanda_rodo_agro_ciots": float(linha["demanda_rodo_agro_ciots"]),
                "demanda_rodo_min_ciots": float(linha["demanda_rodo_min_ciots"]),
                "tipo_no": linha["tipo_no"]
            }

    arestas = []

    with open(caminho_arestas, "r", encoding="utf-8", newline="") as arq_a:
        for linha in csv.DictReader(arq_a):
            arestas.append({
                "origem": int(linha["origem"]),
                "destino": int(linha["destino"]),
                "distancia_km": float(linha["distancia_km"]),
                "custo_milhoes": float(linha["custo_milhoes"]),
                "lucro_agro_milhoes": float(linha["lucro_agro_milhoes"]),
                "lucro_minerio_milhoes": float(linha["lucro_minerio_milhoes"]),
                "lucro_total_milhoes": float(linha["lucro_total_milhoes"]),
                "tipo": linha["tipo"]
            })

    return vertices, arestas


def main():
    vertices, arestas = carregar_dados()

    # ============================================================
    # 1. CONECTIVIDADE INICIAL DA MALHA
    # ============================================================

    arestas_ativas = [a for a in arestas if a["tipo"] == "ativa"]

    grafo = solver_malha.construir_grafo(vertices, arestas_ativas)
    componentes = solver_malha.encontrar_componentes(grafo)

    print("=" * 75)
    print(" ANÁLISE DE EXPANSÃO DA MALHA FERROVIÁRIA BRASILEIRA")
    print("=" * 75)

    print(f"Vértices: {len(vertices)}")
    print(f"Arestas: {len(arestas)}")
    print(f"Componentes conexas: {len(componentes)}")
    print(f"Maior componente: {len(componentes[0])} vértices")

    # ============================================================
    # 2. SENSIBILIDADE POR ORÇAMENTO
    # ============================================================

    print("\n--- SENSIBILIDADE POR ORÇAMENTO (ROI TOTAL) ---")

    cabecalho = (
        f"{'Orçamento':<12} | {'Gasto':<9} | {'Reativados':<11} | "
        f"{'Novos':<10} | {'Lucro 10a':<10} | {'MaiorComp':<10}"
    )

    print(cabecalho)
    print("-" * len(cabecalho))

    resultados_orcamentos = []
    res_10bi_roi = None

    for orcamento in [2.0, 5.0, 10.0, 20.0, 50.0]:
        resultado = solver_malha.kruskal_expansao(
            vertices,
            arestas,
            orcamento,
            criterio="roi_total"
        )

        resultados_orcamentos.append(resultado)

        if orcamento == 10.0:
            res_10bi_roi = resultado

        print(
            f"R$ {resultado['orcamento_bi']:<8.1f} | "
            f"R$ {resultado['custo_gasto_bi']:<5.2f} | "
            f"{resultado['km_reativados']:<11.1f} | "
            f"{resultado['km_novos']:<10.1f} | "
            f"R$ {resultado['lucro_total_bi']:<6.2f} | "
            f"{resultado['maior_componente']:<10}"
        )

    # ============================================================
    # 3. COMPARAÇÃO ENTRE ESTRATÉGIAS
    # ============================================================

    print("\n--- COMPARAÇÃO DE ESTRATÉGIAS (R$ 10 BILHÕES) ---")

    comparacao_estrategias = {}

    cabecalho = (
        f"{'Estratégia':<15} | {'Km Total':<10} | "
        f"{'Lucro Agro':<11} | {'Lucro Min.':<11} | "
        f"{'Lucro Total':<11} | {'ROI':<7}"
    )

    print(cabecalho)
    print("-" * len(cabecalho))

    for criterio in ["custo_minimo", "roi_agro", "roi_minerio", "roi_total"]:
        resultado = solver_malha.kruskal_expansao(
            vertices,
            arestas,
            10.0,
            criterio=criterio
        )

        comparacao_estrategias[criterio] = resultado

        print(
            f"{criterio:<15} | "
            f"{resultado['km_totais_expandidos']:<10.1f} | "
            f"R$ {resultado['lucro_agro_bi']:<7.2f} | "
            f"R$ {resultado['lucro_minerio_bi']:<7.2f} | "
            f"R$ {resultado['lucro_total_bi']:<7.2f} | "
            f"{resultado['roi_geral']:<6.2f}x"
        )

    # ============================================================
    # 4. ANÁLISE DE CAMINHOS ATÉ A MALHA PRINCIPAL
    # ============================================================

    estacoes_principais = solver_malha.obter_estacoes_maior_componente(
        vertices,
        arestas
    )

    caminhos = solver_malha.analisar_caminhos_dijkstra(
        vertices,
        arestas,
        estacoes_principais
    )

    alcançaveis = [c for c in caminhos if c["alcançavel"]]
    nao_alcancaveis = len(caminhos) - len(alcançaveis)

    print("\n--- INTEGRAÇÃO COM A MALHA PRINCIPAL ---")
    print(f"Estações na maior componente: {len(estacoes_principais)}")
    print(f"Municípios analisados: {len(caminhos)}")
    print(f"Municípios alcançáveis: {len(alcançaveis)}")
    print(f"Municípios sem caminho: {nao_alcancaveis}")

    # ============================================================
    # 5. CRUZAMENTO ENTRE DEMANDA E CUSTO
    # ============================================================

    municipios = solver_malha.analisar_municipios(vertices)

    cruzamento = solver_malha.cruzar_demanda_custo(
        municipios,
        caminhos
    )

    print("\n--- MUNICÍPIOS COM MAIOR RELAÇÃO DEMANDA/CUSTO ---")

    for municipio in cruzamento[:10]:
        print(
            f"{municipio['nome_municipio']} - "
            f"{municipio['uf']} | "
            f"Demanda: {municipio['demanda_rodo_total_ciots']:.0f} CIOTs | "
            f"Custo: R$ {municipio['custo_integracao_milhoes']:.2f} mi"
        )

    # ============================================================
    # 6. CLASSIFICAÇÃO DOS MUNICÍPIOS
    # ============================================================

    classificacao = solver_malha.classificar_municipios(cruzamento)

    print("\n--- CLASSIFICAÇÃO DOS MUNICÍPIOS ---")

    print(
        f"Mediana da demanda: "
        f"{classificacao['mediana_demanda']:.0f} CIOTs"
    )

    print(
        f"Mediana do custo: "
        f"R$ {classificacao['mediana_custo']:.2f} milhões"
    )

    nomes_grupos = {
        "alta_demanda_baixo_custo": "Alta demanda / Baixo custo",
        "alta_demanda_alto_custo": "Alta demanda / Alto custo",
        "baixa_demanda_baixo_custo": "Baixa demanda / Baixo custo",
        "baixa_demanda_alto_custo": "Baixa demanda / Alto custo"
    }

    for chave, grupo in classificacao["grupos"].items():
        print(f"{nomes_grupos[chave]}: {len(grupo)} municípios")

    # ============================================================
    # 7. VISUALIZAÇÕES
    # ============================================================

    print("\nGerando visualizações...")

    visualizacao.gerar_grafico_orcamentos(resultados_orcamentos)

    visualizacao.gerar_mapa_expansao(
        vertices,
        arestas,
        res_10bi_roi
    )

    visualizacao.gerar_grafico_estrategias(comparacao_estrategias)

    visualizacao.gerar_grafico_demanda_custo(classificacao)

    visualizacao.gerar_grafico_classificacao(classificacao)

    print("Visualizações geradas com sucesso!")


if __name__ == "__main__":
    main()
