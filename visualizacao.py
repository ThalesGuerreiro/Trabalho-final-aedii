import os
import matplotlib.pyplot as plt

PASTA_RESULTADOS = "resultados"
PASTA_GRAFICOS = os.path.join(PASTA_RESULTADOS, "graficos")
PASTA_MAPAS = os.path.join(PASTA_RESULTADOS, "mapas")


def preparar_diretorios():
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    os.makedirs(PASTA_MAPAS, exist_ok=True)


def gerar_grafico_orcamentos(resultados_orcamentos):

    #Compara quilômetros reativados, novos e lucro estimado para diferentes cenários de orçamento
    preparar_diretorios()

    orcamentos = []
    km_reativados = []
    km_novos = []
    lucros = []

    for resultado in resultados_orcamentos:
        orcamentos.append(resultado["orcamento_bi"])
        km_reativados.append(resultado["km_reativados"])
        km_novos.append(resultado["km_novos"])
        lucros.append(resultado["lucro_total_bi"])

    fig, ax1 = plt.subplots(figsize=(10, 6))

    largura = 0.35
    posicoes = range(len(orcamentos))

    ax1.bar(
        [p - largura / 2 for p in posicoes],
        km_reativados,
        largura,
        label="Km reativados"
    )

    ax1.bar(
        [p + largura / 2 for p in posicoes],
        km_novos,
        largura,
        label="Km novos"
    )

    ax1.set_xlabel("Orçamento (bilhões de R$)")
    ax1.set_ylabel("Quilômetros")
    ax1.set_xticks(list(posicoes))
    ax1.set_xticklabels(orcamentos)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    ax2.plot(
        list(posicoes),
        lucros,
        marker="o",
        linestyle="-",
        label="Lucro estimado em 10 anos"
    )
    ax2.set_ylabel("Lucro estimado (milhões de R$)")

    linhas1, legendas1 = ax1.get_legend_handles_labels()
    linhas2, legendas2 = ax2.get_legend_handles_labels()

    ax1.legend(
        linhas1 + linhas2,
        legendas1 + legendas2,
        loc="upper left"
    )

    plt.title("Impacto dos diferentes cenários orçamentários")
    fig.tight_layout()

    caminho = os.path.join(
        PASTA_GRAFICOS,
        "sensibilidade_orcamentaria.png"
    )

    plt.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)

def gerar_mapa_expansao(vertices, arestas, resultado):

    #Gera um mapa da malha ferroviária considerando as arestas selecionadas para o orçamento de referência
    preparar_diretorios()

    try:
        import geopandas as gpd
        from shapely.geometry import LineString

        caminho_shape = "dados/ShapeFileMar-2026/UF2026.shp"
        mapa_base = gpd.read_file(caminho_shape)

    except Exception as erro:
        print(f"Não foi possível carregar o mapa-base: {erro}")
        return

    coordenadas = {}

    for id_vertice, vertice in vertices.items():
        coordenadas[id_vertice] = (
            float(vertice["lon"]),
            float(vertice["lat"])
        )

    geometria_ativa = []
    geometria_reativada = []
    geometria_nova = []

    for aresta in arestas:
        origem = aresta["origem"]
        destino = aresta["destino"]

        if origem not in coordenadas or destino not in coordenadas:
            continue

        linha = LineString([
            coordenadas[origem],
            coordenadas[destino]
        ])

        tipo = aresta["tipo"]

        if tipo == "ativa":
            geometria_ativa.append(linha)

    for aresta in resultado["selecionadas"]:
        origem = aresta["origem"]
        destino = aresta["destino"]

        if origem not in coordenadas or destino not in coordenadas:
            continue

        linha = LineString([
            coordenadas[origem],
            coordenadas[destino]
        ])

        if aresta["tipo"] == "desativada":
            geometria_reativada.append(linha)

        elif aresta["tipo"] == "nova":
            geometria_nova.append(linha)

    fig, ax = plt.subplots(figsize=(12, 10))

    mapa_base.plot(
        ax=ax,
        color="whitesmoke",
        edgecolor="gray",
        linewidth=0.5
    )

    if geometria_ativa:
        gpd.GeoSeries(
            geometria_ativa,
            crs="EPSG:4326"
        ).plot(
            ax=ax,
            color="dimgray",
            linewidth=0.6,
            label="Malha ativa"
        )

    if geometria_reativada:
        gpd.GeoSeries(
            geometria_reativada,
            crs="EPSG:4326"
        ).plot(
            ax=ax,
            color="royalblue",
            linewidth=1.2,
            label="Trechos reativados"
        )

    if geometria_nova:
        gpd.GeoSeries(
            geometria_nova,
            crs="EPSG:4326"
        ).plot(
            ax=ax,
            color="forestgreen",
            linewidth=1.2,
            label="Novas conexões"
        )

    ax.set_title("Expansão ferroviária — orçamento de R$ 10 bilhões")
    ax.set_axis_off()
    ax.legend(loc="lower left")

    fig.tight_layout()

    caminho = os.path.join(
        PASTA_MAPAS,
        "mapa_expansao_10bi.png"
    )

    plt.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)

def gerar_grafico_estrategias(comparacao_estrategias):

    #Compara os resultados das estratégias de seleção de arestas para o mesmo orçamento
    preparar_diretorios()

    estrategias = list(comparacao_estrategias.keys())

    custos = []
    lucros = []

    for estrategia in estrategias:
        resultado = comparacao_estrategias[estrategia]

        custos.append(resultado["custo_gasto_bi"])
        lucros.append(resultado["lucro_total_bi"])

    fig, ax = plt.subplots(figsize=(10, 6))

    posicoes = range(len(estrategias))
    largura = 0.35

    ax.bar(
        [p - largura / 2 for p in posicoes],
        custos,
        largura,
        label="Custo de expansão"
    )

    ax.bar(
        [p + largura / 2 for p in posicoes],
        lucros,
        largura,
        label="Lucro estimado em 10 anos"
    )

    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(estrategias, rotation=15)
    ax.set_ylabel("Bilhões de R$")
    ax.set_title("Comparação das estratégias de expansão")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()

    caminho = os.path.join(
        PASTA_GRAFICOS,
        "comparacao_estrategias.png"
    )

    plt.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)

def gerar_grafico_demanda_custo(classificacao):

    #Mostra a relação entre demanda rodoviária e custo de integração ferroviária dos municípios
    preparar_diretorios()

    grupos = classificacao["grupos"]

    fig, ax = plt.subplots(figsize=(11, 7))

    configuracoes = [
        ("alta_demanda_baixo_custo", "Alta demanda / Baixo custo"),
        ("alta_demanda_alto_custo", "Alta demanda / Alto custo"),
        ("baixa_demanda_baixo_custo", "Baixa demanda / Baixo custo"),
        ("baixa_demanda_alto_custo", "Baixa demanda / Alto custo")
    ]

    for chave, legenda in configuracoes:
        municipios = grupos[chave]

        demandas = [
            municipio["demanda_rodo_total_ciots"]
            for municipio in municipios
        ]

        custos = [
            municipio["custo_integracao_milhoes"]
            for municipio in municipios
        ]

        ax.scatter(
            demandas,
            custos,
            label=legenda,
            alpha=0.7
        )

    mediana_demanda = classificacao["mediana_demanda"]
    mediana_custo = classificacao["mediana_custo"]

    ax.axvline(
        mediana_demanda,
        linestyle="--",
        color="black",
        alpha=0.7,
        label="Mediana da demanda"
    )

    ax.axhline(
        mediana_custo,
        linestyle=":",
        color="black",
        alpha=0.7,
        label="Mediana do custo"
    )

    ax.set_xlabel("Demanda rodoviária (CIOTs)")
    ax.set_ylabel("Custo de integração (milhões de R$)")
    ax.set_title("Demanda logística versus custo de integração")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout()

    caminho = os.path.join(
        PASTA_GRAFICOS,
        "demanda_vs_custo.png"
    )

    plt.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)

def gerar_grafico_classificacao(classificacao):

    #Exibe a quantidade de municípios em cada grupo da classificação por medianas
    preparar_diretorios()

    grupos = classificacao["grupos"]

    nomes = [
        "Alta demanda /\nBaixo custo",
        "Alta demanda /\nAlto custo",
        "Baixa demanda /\nBaixo custo",
        "Baixa demanda /\nAlto custo"
    ]

    chaves = [
        "alta_demanda_baixo_custo",
        "alta_demanda_alto_custo",
        "baixa_demanda_baixo_custo",
        "baixa_demanda_alto_custo"
    ]

    quantidades = [
        len(grupos[chave])
        for chave in chaves
    ]

    fig, ax = plt.subplots(figsize=(9, 6))

    barras = ax.bar(nomes, quantidades)

    ax.bar_label(barras, padding=3)

    ax.set_ylabel("Quantidade de municípios")
    ax.set_title("Distribuição dos municípios por classificação")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()

    caminho = os.path.join(
        PASTA_GRAFICOS,
        "distribuicao_classificacao.png"
    )

    plt.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)
