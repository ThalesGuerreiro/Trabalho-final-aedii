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