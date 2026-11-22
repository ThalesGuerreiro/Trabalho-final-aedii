import csv
import os
import solver_malha

def carregar_dados(caminho_vertices="vertices.csv", caminho_arestas="arestas.csv"):
    if not os.path.exists(caminho_vertices) and os.path.exists("dados/vertices.csv"):
        caminho_vertices = "dados/vertices.csv"
        caminho_arestas = "dados/arestas.csv"

    vertices = {}
    with open(caminho_vertices, "r", encoding="utf-8", newline="") as arq_v:
        for linha in csv.DictReader(arq_v):
            id_v = int(linha["id"])
            vertices[id_v] = {
                "nome": linha["nome"],
                "uf": linha["uf"],
                "lat": float(linha["lat"]),
                "lon": float(linha["lon"]),
                "tipo_no": linha.get("tipo_no", "estacao")
            }

    arestas = []
    with open(caminho_arestas, "r", encoding="utf-8", newline="") as arq_a:
        for linha in csv.DictReader(arq_a):
            arestas.append({
                "origem": int(linha["origem"]),
                "destino": int(linha["destino"]),
                "distancia_km": float(linha["distancia_km"]),
                "custo_milhoes": float(linha["custo_milhoes"]),
                "lucro_agro_milhoes": float(linha.get("lucro_agro_milhoes", 0.0)),
                "lucro_minerio_milhoes": float(linha.get("lucro_minerio_milhoes", 0.0)),
                "lucro_total_milhoes": float(linha.get("lucro_total_milhoes", 0.0)),
                "tipo": linha["tipo"]
            })

    return vertices, arestas

def gerar_graficos(vertices, arestas, resultados_orcamentos, res_10bi_roi):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[Aviso] matplotlib não instalado. Pulando geração de imagens.")
        return

    # --- GRÁFICO 1: Evolução por Orçamento ---
    orcamentos = [f"R$ {r['orcamento_bi']:.0f} bi" for r in resultados_orcamentos]
    km_reat = [r["km_reativados"] for r in resultados_orcamentos]
    km_nov = [r["km_novos"] for r in resultados_orcamentos]
    lucros = [r["lucro_total_bi"] for r in resultados_orcamentos]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    x = range(len(orcamentos))
    ax1.bar(x, km_reat, label="Trechos Reativados (km)", color="#1f77b4")
    ax1.bar(x, km_nov, bottom=km_reat, label="Trechos Novos (km)", color="#2ca02c")
    ax1.set_ylabel("Extensão Expandida (km)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(orcamentos)
    ax1.set_ylim(0, max(r["km_totais_expandidos"] for r in resultados_orcamentos) * 1.15)
    ax1.legend(loc="upper left", frameon=True)

    ax2 = ax1.twinx()
    ax2.plot(x, lucros, color="#d62728", marker="o", linewidth=2, label="Lucro 10 anos (R$ bi)")
    ax2.set_ylabel("Lucro Estimado em 10 anos (R$ Bilhões)", color="#d62728")
    ax2.set_ylim(0, max(lucros) * 1.15)
    ax2.legend(loc="upper left", bbox_to_anchor=(0.0, 0.83), frameon=True)

    plt.title("Expansão Ferroviária e Retorno Financeiro por Orçamento (ROI Agro + Minério)")
    plt.tight_layout()
    plt.savefig("grafico_orcamentos_3.png", dpi=300)
    plt.close()

    # --- GRÁFICO 2: Mapa Topológico da Expansão (R$ 10 Bilhões) ---
    plt.figure(figsize=(7, 7))

    try:
        import geopandas as gpd
        ufs = gpd.read_file("ShapeFileMar-2026/UF2026.shp")
        ufs.plot(ax=plt.gca(), color="#f7f7f7", edgecolor="#bbbbbb", linewidth=0.6, zorder=0)
    except Exception:
        pass

    # Plotar malha ativa atual filtrando anomalias de coordenadas (> 4 graus de salto)
    for a in arestas:
        if a["tipo"] == "ativa":
            u, v = vertices[a["origem"]], vertices[a["destino"]]
            if abs(u["lon"] - v["lon"]) < 4.0 and abs(u["lat"] - v["lat"]) < 4.0:
                plt.plot([u["lon"], v["lon"]], [u["lat"], v["lat"]], color="#bbbbbb", linewidth=0.7, zorder=1)

    # Plotar trechos selecionados no orçamento de R$ 10 bi
    for a in res_10bi_roi["selecionadas"]:
        u, v = vertices[a["origem"]], vertices[a["destino"]]
        if a["tipo"] == "desativada":
            plt.plot([u["lon"], v["lon"]], [u["lat"], v["lat"]], color="#0055ff",
                     linewidth=2.2, marker="o", markersize=2.5, zorder=3)
        else:
            plt.plot([u["lon"], v["lon"]], [u["lat"], v["lat"]], color="#00aa44",
                     linewidth=2.0, zorder=4)

    plt.plot([], [], color="#bbbbbb", linewidth=1, label="Malha Ativa Atual")
    plt.plot([], [], color="#0055ff", linewidth=2, marker="o", markersize=3, label="Trechos Reativados (R$ 10 bi)")
    plt.plot([], [], color="#00aa44", linewidth=2, label="Trechos Novos Construídos (R$ 10 bi)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Expansão Ótima da Malha Ferroviária Brasileira (Orçamento: R$ 10 Bilhões)")
    plt.legend(loc="lower left", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig("mapa_expansao_10bi_3.png", dpi=300)
    plt.close()
    print("\n[OK] Gráficos salvos: 'grafico_orcamentos_3.png' e 'mapa_expansao_10bi_3.png'")

if __name__ == "__main__":
    vertices, arestas = carregar_dados()
    arestas_ativas = [a for a in arestas if a["tipo"] == "ativa"]

    grafo_inicial = solver_malha.construir_grafo(vertices, arestas_ativas)
    comps_iniciais = solver_malha.encontrar_componentes(grafo_inicial)

    print("==========================================================================")
    print(" ANÁLISE DE EXPANSÃO DA MALHA FERROVIÁRIA BRASILEIRA (AGRO + MINÉRIO)")
    print("==========================================================================")
    print(f"Vértices totais: {len(vertices)} | Arestas totais: {len(arestas)}")
    print(f"Componentes conexas iniciais: {len(comps_iniciais)} (Maior componente: {len(comps_iniciais[0])} nós)\n")

    print("--- TABELA 1: ANÁLISE DE SENSIBILIDADE POR ORÇAMENTO (CRITÉRIO: ROI TOTAL) ---")
    cabecalho = f"{'Orçamento':<11} | {'Gasto':<9} | {'Reativ(km)':<10} | {'Novos(km)':<10} | {'Lucro 10a':<10} | {'MaiorComp':<9} | {'Tempo(ms)':<9}"
    print(cabecalho)
    print("-" * len(cabecalho))

    resultados_orc = []
    res_10bi_roi = None

    for orc in [2.0, 5.0, 10.0, 20.0, 50.0]:
        res = solver_malha.kruskal_expansao(vertices, arestas, orc, criterio="roi_total")
        resultados_orc.append(res)
        if orc == 10.0:
            res_10bi_roi = res
        print(f"R$ {res['orcamento_bi']:<7.1f} | R$ {res['custo_gasto_bi']:<5.2f} | "
              f"{res['km_reativados']:<10.1f} | {res['km_novos']:<10.1f} | "
              f"R$ {res['lucro_total_bi']:<6.2f} | {res['maior_componente']:<9} | {res['tempo_ms']:<9.3f}")

    print("\n--- TABELA 2: COMPARATIVO DE ESTRATÉGIAS NO ORÇAMENTO DE R$ 10 BILHÕES ---")
    cab2 = f"{'Estratégia':<15} | {'Km Total':<10} | {'Lucro Agro':<11} | {'Lucro Min.':<11} | {'Lucro Total':<11} | {'ROI':<6}"
    print(cab2)
    print("-" * len(cab2))

    for crit in ["custo_minimo", "roi_agro", "roi_minerio", "roi_total"]:
        r = solver_malha.kruskal_expansao(vertices, arestas, 10.0, criterio=crit)
        print(f"{crit:<15} | {r['km_totais_expandidos']:<10.1f} | R$ {r['lucro_agro_bi']:<7.2f} | "
              f"R$ {r['lucro_minerio_bi']:<7.2f} | R$ {r['lucro_total_bi']:<7.2f} | {r['roi_geral']:<6.2f}x")

    gerar_graficos(vertices, arestas, resultados_orc, res_10bi_roi)