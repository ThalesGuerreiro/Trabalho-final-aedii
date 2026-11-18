from collections import deque

def construir_grafo(vertices, arestas):
    grafo = {}
    for i in vertices:
        grafo[i] = []

    for linha in arestas:
        if linha["tipo"] == "ativa":
            grafo[linha["origem"]].append(linha["destino"])
            grafo[linha["destino"]].append(linha["origem"])

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

    return componentes

#Funções do Union-Find

def criar_conjuntos(vertices):
    pai = {}
    for i in vertices:
            pai[i] = i
    
    return pai

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