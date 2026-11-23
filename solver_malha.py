from collections import deque
import time

def construir_grafo(vertices, arestas_ativas):
    grafo = {i: [] for i in vertices}
    for linha in arestas_ativas:
        u, v = linha["origem"], linha["destino"]
        if u in grafo and v in grafo:
            grafo[u].append(v)
            grafo[v].append(u)
    return grafo

def bfs(grafo, inicio):
    visitados = set()
    fila = deque([inicio])
    visitados.add(inicio)

    while fila:
        atual = fila.popleft()
        for vizinho in grafo[atual]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)
    return visitados

def encontrar_componentes(grafo):
    visitados = set()
    componentes = []
    for vertice in grafo:
        if vertice not in visitados:
            vis = bfs(grafo, vertice)
            componentes.append(vis)
            visitados.update(vis)
    componentes.sort(key=len, reverse=True)
    return componentes

def criar_conjuntos(vertices):
    return {i: i for i in vertices}

def encontrar_representante(pai, vertice):
    if vertice == pai[vertice]:
        return vertice
    pai[vertice] = encontrar_representante(pai, pai[vertice])
    return pai[vertice]

def unir(pai, a, b):
    rep_a = encontrar_representante(pai, a)
    rep_b = encontrar_representante(pai, b)
    if rep_a != rep_b:
        pai[rep_b] = rep_a
        return True
    return False

def kruskal_expansao(vertices, arestas, orcamento_bilhoes, criterio="roi_total"):
    """
    Executa o algoritmo de Kruskal adaptado com restrição orçamentária.
    Critérios disponíveis:
      - 'custo_minimo': menor custo absoluto (expande máxima quilometragem)
      - 'roi_total': maior razão (lucro_total / custo)
      - 'roi_agro': maior razão (lucro_agro / custo)
      - 'roi_minerio': maior razão (lucro_minerio / custo)
    """
    inicio_tempo = time.perf_counter()
    orcamento_milhoes = orcamento_bilhoes * 1000.0

    pai = criar_conjuntos(vertices)
    arestas_ativas = [a for a in arestas if a["tipo"] == "ativa"]
    candidatas = [a for a in arestas if a["tipo"] in ("desativada", "nova")]

    #une inicialmente a espinha dorsal ja ativa (custo=0)
    for aresta in arestas_ativas:
        unir(pai, aresta["origem"], aresta["destino"])

    if criterio == "custo_minimo":
        candidatas.sort(key=lambda a: a["custo_milhoes"])
    elif criterio == "roi_agro":
        candidatas.sort(
            key=lambda a: a.get("lucro_agro_milhoes", 0.0) / max(a["custo_milhoes"], 0.001),
            reverse=True
        )
    elif criterio == "roi_minerio":
        candidatas.sort(
            key=lambda a: a.get("lucro_minerio_milhoes", 0.0) / max(a["custo_milhoes"], 0.001),
            reverse=True
        )
    else:  #roi_total
        candidatas.sort(
            key=lambda a: a.get("lucro_total_milhoes", 0.0) / max(a["custo_milhoes"], 0.001),
            reverse=True
        )

    selecionadas = []
    custo_gasto = 0.0
    km_reativados = 0.0
    km_novos = 0.0
    lucro_agro_acum = 0.0
    lucro_min_acum = 0.0
    lucro_total_acum = 0.0

    tem_ferrovia = {encontrar_representante(pai, i): True for i, v in vertices.items() if v.get("tipo_no") == "estacao"}

    for aresta in candidatas:
        if custo_gasto + aresta["custo_milhoes"] <= orcamento_milhoes:
            rep_u = encontrar_representante(pai, aresta["origem"])
            rep_v = encontrar_representante(pai, aresta["destino"])

            if rep_u != rep_v:
                if aresta["tipo"] == "nova" and not (tem_ferrovia.get(rep_u, False) or tem_ferrovia.get(rep_v, False)):
                    continue

                unir(pai, aresta["origem"], aresta["destino"])
                novo_rep = encontrar_representante(pai, aresta["origem"])
                tem_ferrovia[novo_rep] = True

                selecionadas.append(aresta)
                custo_gasto += aresta["custo_milhoes"]
                lucro_agro_acum += aresta.get("lucro_agro_milhoes", 0.0)
                lucro_min_acum += aresta.get("lucro_minerio_milhoes", 0.0)
                lucro_total_acum += aresta.get("lucro_total_milhoes", 0.0)

                if aresta["tipo"] == "desativada":
                    km_reativados += aresta["distancia_km"]
                else:
                    km_novos += aresta["distancia_km"]

    tempo_ms = (time.perf_counter() - inicio_tempo) * 1000.0

    grafo_pos = construir_grafo(vertices, arestas_ativas + selecionadas)
    comps_pos = encontrar_componentes(grafo_pos)

    return {
        "criterio": criterio,
        "orcamento_bi": orcamento_bilhoes,
        "custo_gasto_bi": round(custo_gasto / 1000.0, 3),
        "km_reativados": round(km_reativados, 2),
        "km_novos": round(km_novos, 2),
        "km_totais_expandidos": round(km_reativados + km_novos, 2),
        "lucro_agro_bi": round(lucro_agro_acum / 1000.0, 3),
        "lucro_minerio_bi": round(lucro_min_acum / 1000.0, 3),
        "lucro_total_bi": round(lucro_total_acum / 1000.0, 3),
        "roi_geral": round(lucro_total_acum / max(custo_gasto, 0.001), 2),
        "trechos_adicionados": len(selecionadas),
        "maior_componente": len(comps_pos[0]),
        "num_componentes": len(comps_pos),
        "tempo_ms": round(tempo_ms, 3),
        "selecionadas": selecionadas
    }

def analisar_municipios(vertices):
    municipios = {}

    for id_v, vertice in vertices.items():
        codigo = vertice["codigo_muni"]

        if not codigo:
            continue

        if codigo not in municipios:
            municipios[codigo] = {
                "codigo_muni": codigo,
                "nome_municipio": None,
                "uf": vertice["uf"],
                "tem_estacao": False,
                "eh_porto": False,
                "demanda_ferr_agro_ton": vertice["demanda_ferr_agro_ton"],
                "demanda_ferr_min_ton": vertice["demanda_ferr_min_ton"],
                "demanda_rodo_agro_ciots": vertice["demanda_rodo_agro_ciots"],
                "demanda_rodo_min_ciots": vertice["demanda_rodo_min_ciots"]
            }

        municipio = municipios[codigo]

        if vertice["tipo_no"] == "estacao":
            municipio["tem_estacao"] = True

        if vertice["eh_porto"]:
            municipio["eh_porto"] = True

        if vertice["tipo_no"] == "municipio_candidato":
            municipio["nome_municipio"] = vertice["nome"]

    # Calcula a demanda rodoviária total de cada município
    resultado = []

    for municipio in municipios.values():
        municipio["demanda_rodo_total_ciots"] = (
            municipio["demanda_rodo_agro_ciots"]
            + municipio["demanda_rodo_min_ciots"]
        )

        municipio["demanda_ferr_total_ton"] = (
            municipio["demanda_ferr_agro_ton"]
            + municipio["demanda_ferr_min_ton"]
        )

        resultado.append(municipio)

    # Ordena pela demanda rodoviária total, em ordem decrescente
    resultado.sort(
        key=lambda municipio: municipio["demanda_rodo_total_ciots"],
        reverse=True
    )

    return resultado


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    raio_terra = 6371.0

    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return raio_terra * c


def analisar_distancia_estacoes(vertices):
    estacoes = [
        (id_v, v) for id_v, v in vertices.items()
        if v["tipo_no"] == "estacao"
    ]

    candidatos = []

    for id_v, municipio in vertices.items():
        if municipio["tipo_no"] != "municipio_candidato":
            continue

        if not estacoes:
            continue

        menor_distancia = float("inf")
        estacao_proxima = None

        for id_estacao, estacao in estacoes:
            distancia = calcular_distancia_km(
                municipio["lat"],
                municipio["lon"],
                estacao["lat"],
                estacao["lon"]
            )

            if distancia < menor_distancia:
                menor_distancia = distancia
                estacao_proxima = (id_estacao, estacao)

        id_estacao, estacao = estacao_proxima

        candidatos.append({
            "codigo_muni": municipio["codigo_muni"],
            "uf": municipio["uf"],
            "demanda_rodo_total_ciots": (
                municipio["demanda_rodo_agro_ciots"]
                + municipio["demanda_rodo_min_ciots"]
            ),
            "id_estacao_proxima": id_estacao,
            "nome_estacao_proxima": estacao["nome"],
            "distancia_estacao_km": menor_distancia
        })

    candidatos.sort(
        key=lambda m: m["demanda_rodo_total_ciots"],
        reverse=True
    )

    return candidatos


def analisar_conexoes_candidatas(vertices, arestas):
    candidatos = {
        id_v: v
        for id_v, v in vertices.items()
        if v["tipo_no"] == "municipio_candidato"
    }

    # Identifica estações que possuem pelo menos uma
    # aresta ativa na malha ferroviária
    estacoes_na_malha = set()

    for aresta in arestas:
        if aresta["tipo"] == "ativa":
            estacoes_na_malha.add(aresta["origem"])
            estacoes_na_malha.add(aresta["destino"])

    resultado = []

    for id_v, municipio in candidatos.items():
        conexoes = []

        for aresta in arestas:
            if aresta["tipo"] != "nova":
                continue

            if aresta["origem"] == id_v:
                id_vizinho = aresta["destino"]
            elif aresta["destino"] == id_v:
                id_vizinho = aresta["origem"]
            else:
                continue

            vizinho = vertices[id_vizinho]

            conexoes.append({
                "id_vizinho": id_vizinho,
                "nome_vizinho": vizinho["nome"],
                "tipo_vizinho": vizinho["tipo_no"],
                "conecta_estacao_ativa": (
                    vizinho["tipo_no"] == "estacao"
                    and id_vizinho in estacoes_na_malha
                ),
                "distancia_km": aresta["distancia_km"],
                "custo_milhoes": aresta["custo_milhoes"],
                "lucro_total_milhoes": aresta["lucro_total_milhoes"]
            })

        conexoes_diretas = [
            c for c in conexoes
            if c["conecta_estacao_ativa"]
        ]

        resultado.append({
            "codigo_muni": municipio["codigo_muni"],
            "uf": municipio["uf"],
            "demanda_rodo_total_ciots": (
                municipio["demanda_rodo_agro_ciots"]
                + municipio["demanda_rodo_min_ciots"]
            ),
            "quantidade_conexoes": len(conexoes),
            "tem_conexao_direta_malha": bool(conexoes_diretas),
            "menor_custo_direto_milhoes": (
                min(c["custo_milhoes"] for c in conexoes_diretas)
                if conexoes_diretas else None
            ),
            "conexoes": conexoes
        })

    resultado.sort(
        key=lambda m: m["demanda_rodo_total_ciots"],
        reverse=True
    )

    return resultado
