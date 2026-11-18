import csv, solver_malha

arestas = []
vertices = {}

with open('dados/arestas.csv', 'r', encoding='utf-8', newline='') as arq_arestas:
    for linha in csv.DictReader(arq_arestas):
        origem = int(linha["origem"])
        destino = int(linha["destino"])
        distancia_km = float(linha["distancia_km"])
        custo_milhoes = float(linha["custo_milhoes"])
        tipo = linha["tipo"]
        arestas.append({
            "origem": origem,
            "destino": destino,
            "distancia_km": distancia_km,
            "custo_milhoes": custo_milhoes,
            "tipo": tipo
        })

with open('dados/vertices.csv', 'r', encoding='utf-8', newline='') as arq_vertices:
    for linha in csv.DictReader(arq_vertices):
        id_vertice = int(linha["id"])
        nome = linha["nome"]
        uf = linha["uf"]
        lat = float(linha["lat"])
        lon = float(linha["lon"])

        vertices[id_vertice] = {
            "nome": nome,
            "uf": uf,
            "lat": lat,
            "lon": lon
        }

grafo = solver_malha.construir_grafo(vertices, arestas)

componentes = solver_malha.encontrar_componentes(grafo)
print(solver_malha.encontrar_componentes(grafo))

for i, componente in enumerate(componentes):
    print(f"Componente {i + 1}: {len(componente)} vértices")