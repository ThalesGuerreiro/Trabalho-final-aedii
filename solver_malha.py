from collections import deque
import time
import heapq
from statistics import median

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



def analisar_distancia_estacoes(vertices, estacoes_principais):
    estacoes = [
        (id_v, v) for id_v, v in vertices.items()
        if v["tipo_no"] == "estacao"
    ]

    estacoes_malha_principal = [
        (id_v, vertices[id_v])
        for id_v in estacoes_principais
    ]

    candidatos = []

    for id_v, municipio in vertices.items():
        if municipio["tipo_no"] != "municipio_candidato":
            continue

        menor_distancia = float("inf")
        estacao_proxima = None

        for id_estacao, estacao in estacoes:
            distancia = calcular_distancia_km(
                municipio["lat"], municipio["lon"],
                estacao["lat"], estacao["lon"]
            )

            if distancia < menor_distancia:
                menor_distancia = distancia
                estacao_proxima = (id_estacao, estacao)

        menor_distancia_principal = float("inf")
        estacao_principal_proxima = None

        for id_estacao, estacao in estacoes_malha_principal:
            distancia = calcular_distancia_km(
                municipio["lat"], municipio["lon"],
                estacao["lat"], estacao["lon"]
            )

            if distancia < menor_distancia_principal:
                menor_distancia_principal = distancia
                estacao_principal_proxima = (id_estacao, estacao)

        id_estacao, estacao = estacao_proxima
        id_principal, estacao_principal = estacao_principal_proxima

        candidatos.append({
            "codigo_muni": municipio["codigo_muni"],
            "uf": municipio["uf"],
            "demanda_rodo_total_ciots": (
                municipio["demanda_rodo_agro_ciots"]
                + municipio["demanda_rodo_min_ciots"]
            ),
            "id_estacao_proxima": id_estacao,
            "nome_estacao_proxima": estacao["nome"],
            "distancia_estacao_km": menor_distancia,
            "id_estacao_malha_principal": id_principal,
            "nome_estacao_malha_principal": estacao_principal["nome"],
            "distancia_malha_principal_km": menor_distancia_principal
        })

    candidatos.sort(
        key=lambda m: m["demanda_rodo_total_ciots"],
        reverse=True
    )

    return candidatos



def analisar_conexoes_candidatas(vertices, arestas, estacoes_principais):
    candidatos = {
        id_v: v
        for id_v, v in vertices.items()
        if v["tipo_no"] == "municipio_candidato"
    }

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
                ),
                "conecta_malha_principal": (
                    id_vizinho in estacoes_principais
                ),
                "distancia_km": aresta["distancia_km"],
                "custo_milhoes": aresta["custo_milhoes"],
                "lucro_total_milhoes": aresta["lucro_total_milhoes"]
            })

        conexoes_principais = [
            c for c in conexoes
            if c["conecta_malha_principal"]
        ]

        resultado.append({
            "codigo_muni": municipio["codigo_muni"],
            "uf": municipio["uf"],
            "demanda_rodo_total_ciots": (
                municipio["demanda_rodo_agro_ciots"]
                + municipio["demanda_rodo_min_ciots"]
            ),
            "quantidade_conexoes": len(conexoes),
            "tem_conexao_direta_malha_principal": bool(conexoes_principais),
            "menor_custo_direto_malha_principal_milhoes": (
                min(
                    c["custo_milhoes"]
                    for c in conexoes_principais
                )
                if conexoes_principais else None
            ),
            "conexoes": conexoes
        })

    resultado.sort(
        key=lambda m: m["demanda_rodo_total_ciots"],
        reverse=True
    )

    return resultado

def obter_estacoes_maior_componente(vertices, arestas):
    arestas_ativas = [
        aresta for aresta in arestas
        if aresta["tipo"] == "ativa"
    ]

    grafo = construir_grafo(vertices, arestas_ativas)
    componentes = encontrar_componentes(grafo)

    if not componentes:
        return set()

    maior_componente = componentes[0]

    estacoes = {
        id_v for id_v in maior_componente
        if vertices[id_v]["tipo_no"] == "estacao"
    }

    return estacoes


def construir_grafo_expansao(vertices, arestas):
    """
    Cria um grafo ponderado para a busca de caminhos de expansão.

    Arestas ativas possuem custo zero.
    Arestas novas possuem o custo de construção.
    Arestas desativadas são ignoradas.
    """
    grafo = {id_v: [] for id_v in vertices}

    for aresta in arestas:
        if aresta["tipo"] not in ("ativa", "nova"):
            continue

        u = aresta["origem"]
        v = aresta["destino"]

        if u not in grafo or v not in grafo:
            continue

        custo = 0.0 if aresta["tipo"] == "ativa" else aresta["custo_milhoes"]

        grafo[u].append((v, custo, aresta))
        grafo[v].append((u, custo, aresta))

    return grafo


def dijkstra_ate_malha_principal(grafo, origem, estacoes_principais):
    #Encontra o caminho de menor custo entre a origem e qualquer estação pertencente à maior componente da malha ativa
    distancias = {vertice: float("inf") for vertice in grafo}
    predecessores = {}

    distancias[origem] = 0.0
    fila = [(0.0, origem)]

    destino_encontrado = None

    while fila:
        custo_atual, atual = heapq.heappop(fila)

        if custo_atual > distancias[atual]:
            continue

        if atual in estacoes_principais:
            destino_encontrado = atual
            break

        for vizinho, custo_aresta, aresta in grafo[atual]:
            novo_custo = custo_atual + custo_aresta

            if novo_custo < distancias[vizinho]:
                distancias[vizinho] = novo_custo
                predecessores[vizinho] = (atual, aresta)
                heapq.heappush(fila, (novo_custo, vizinho))

    if destino_encontrado is None:
        return None

    caminho = [destino_encontrado]
    arestas_caminho = []

    atual = destino_encontrado

    while atual != origem:
        anterior, aresta = predecessores[atual]
        arestas_caminho.append(aresta)
        caminho.append(anterior)
        atual = anterior

    caminho.reverse()
    arestas_caminho.reverse()

    distancia_total = sum(
        aresta["distancia_km"] for aresta in arestas_caminho
    )

    quantidade_novas = sum(
        1 for aresta in arestas_caminho
        if aresta["tipo"] == "nova"
    )

    return {
        "id_estacao_destino": destino_encontrado,
        "custo_milhoes": distancias[destino_encontrado],
        "distancia_km": distancia_total,
        "quantidade_novas": quantidade_novas,
        "caminho": caminho,
        "arestas_caminho": arestas_caminho
    }


def analisar_caminhos_dijkstra(vertices, arestas, estacoes_principais):
    #Analisa o caminho de menor custo de cada município candidato até a maior componente da malha ferroviária ativa
    grafo = construir_grafo_expansao(vertices, arestas)

    resultado = []

    for id_v, municipio in vertices.items():
        if municipio["tipo_no"] != "municipio_candidato":
            continue

        caminho = dijkstra_ate_malha_principal(
            grafo,
            id_v,
            estacoes_principais
        )

        registro = {
            "id_municipio": id_v,
            "codigo_muni": municipio["codigo_muni"],
            "nome_municipio": municipio["nome"],
            "uf": municipio["uf"],
            "demanda_rodo_total_ciots": (
                municipio["demanda_rodo_agro_ciots"]
                + municipio["demanda_rodo_min_ciots"]
            )
        }

        if caminho is None:
            registro.update({
                "alcançavel": False,
                "custo_milhoes": None,
                "distancia_km": None,
                "quantidade_novas": None,
                "nome_estacao_destino": None,
                "caminho": []
            })
        else:
            registro.update({
                "alcançavel": True,
                "custo_milhoes": caminho["custo_milhoes"],
                "distancia_km": caminho["distancia_km"],
                "quantidade_novas": caminho["quantidade_novas"],
                "nome_estacao_destino": vertices[
                    caminho["id_estacao_destino"]
                ]["nome"],
                "caminho": [
                    {
                        "id": id_no,
                        "nome": vertices[id_no]["nome"],
                        "tipo_no": vertices[id_no]["tipo_no"]
                    }
                    for id_no in caminho["caminho"]
                ],
                "arestas_caminho": caminho["arestas_caminho"]
            })

        resultado.append(registro)

    resultado.sort(
        key=lambda m: (
            m["custo_milhoes"] is None,
            m["custo_milhoes"] if m["custo_milhoes"] is not None else float("inf")
        )
    )

    return resultado


def cruzar_demanda_custo(municipios, caminhos):

    dados_municipais = {
        municipio["codigo_muni"]: municipio
        for municipio in municipios
    }

    resultado = []

    for caminho in caminhos:
        codigo = caminho["codigo_muni"]

        municipio = dados_municipais.get(codigo)

        if municipio is None:
            continue

        if not caminho["alcançavel"]:
            continue

        custo = caminho["custo_milhoes"]
        demanda = municipio["demanda_rodo_total_ciots"]

        resultado.append({
            "codigo_muni": codigo,
            "nome_municipio": caminho["nome_municipio"],
            "uf": caminho["uf"],

            "demanda_rodo_agro_ciots": municipio[
                "demanda_rodo_agro_ciots"
            ],
            "demanda_rodo_min_ciots": municipio[
                "demanda_rodo_min_ciots"
            ],
            "demanda_rodo_total_ciots": demanda,

            "custo_integracao_milhoes": custo,
            "distancia_km": caminho["distancia_km"],
            "quantidade_novas": caminho["quantidade_novas"],
            "estacao_destino": caminho["nome_estacao_destino"],

            "ciots_por_milhao": (
                demanda / custo if custo > 0 else 0
            )
        })

    resultado.sort(
        key=lambda m: m["ciots_por_milhao"],
        reverse=True
    )

    return resultado


def classificar_municipios(cruzamento):
    
    #Classifica municípios conforme demanda logística custo de integração, utilizando as medianas
    if not cruzamento:
        return None

    mediana_demanda = median(
        m["demanda_rodo_total_ciots"] for m in cruzamento
    )

    mediana_custo = median(
        m["custo_integracao_milhoes"] for m in cruzamento
    )

    grupos = {
        "alta_demanda_baixo_custo": [],
        "alta_demanda_alto_custo": [],
        "baixa_demanda_baixo_custo": [],
        "baixa_demanda_alto_custo": []
    }

    for municipio in cruzamento:
        demanda_alta = (
            municipio["demanda_rodo_total_ciots"] >= mediana_demanda
        )

        custo_baixo = (
            municipio["custo_integracao_milhoes"] <= mediana_custo
        )

        if demanda_alta and custo_baixo:
            grupo = "alta_demanda_baixo_custo"

        elif demanda_alta and not custo_baixo:
            grupo = "alta_demanda_alto_custo"

        elif not demanda_alta and custo_baixo:
            grupo = "baixa_demanda_baixo_custo"

        else:
            grupo = "baixa_demanda_alto_custo"

        dados = municipio.copy()
        dados["classificacao"] = grupo

        grupos[grupo].append(dados)

    for grupo in grupos.values():
        grupo.sort(
            key=lambda m: m["ciots_por_milhao"],
            reverse=True
        )

    return {
        "mediana_demanda": mediana_demanda,
        "mediana_custo": mediana_custo,
        "grupos": grupos
    }
