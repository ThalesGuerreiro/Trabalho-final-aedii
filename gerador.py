import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

CODIGO_SITUACAO_ATIVA = 1   

CUSTO_KM_ATIVA      = 0.0   
CUSTO_KM_DESATIVADA = 3.0   
CUSTO_KM_NOVA       = 15.0  

TOP_MUNICIPIOS_CANDIDATOS = 400 
K_VIZINHOS_EXPANSAO       = 4   

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def carregar_shp(caminho):
    gdf = gpd.read_file(caminho)
    if gdf.crs is None:
        return gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=4326)

estacoes = carregar_shp("dados/ShapeFileMar-2026/Estação2026.shp")
linhas = carregar_shp("dados/ShapeFileMar-2026/LinhaEstação2026.shp")
municipios = carregar_shp("dados/ShapeFileMar-2026/Municipio2026.shp")

estacoes = estacoes[estacoes.geometry.notnull()].copy()
estacoes["lat"] = estacoes.geometry.y
estacoes["lon"] = estacoes.geometry.x

vertices_lista = []
mapa_codigo_para_id = {}

for _, row in estacoes.iterrows():
    cod_est = int(row["CodigoEsta"])
    if cod_est not in mapa_codigo_para_id:
        novo_id = len(vertices_lista)
        mapa_codigo_para_id[cod_est] = novo_id
        vertices_lista.append({
            "id": novo_id,
            "codigo_original": cod_est,
            "nome": str(row["NomeEstaca"]).strip(),
            "uf": str(row["CodigoMuni"])[:2], 
            "lat": round(row["lat"], 6),
            "lon": round(row["lon"], 6),
            "populacao": 0,
            "tipo_no": "estacao"
        })

df_vertices = pd.DataFrame(vertices_lista)

arestas_dict = {}
linhas_ordenadas = linhas.sort_values(by=["CodigoLi_1", "NumeroSequ"])

for cod_linha, grupo in linhas_ordenadas.groupby("CodigoLi_1"):
    registros = grupo.to_dict("records")
    for i in range(len(registros) - 1):
        atual = registros[i]
        prox = registros[i + 1]

        cod_u = int(atual["CodigoEsta"])
        cod_v = int(prox["CodigoEsta"])

        if cod_u in mapa_codigo_para_id and cod_v in mapa_codigo_para_id:
            u = mapa_codigo_para_id[cod_u]
            v = mapa_codigo_para_id[cod_v]
            if u == v:
                continue

            dist = float(prox["NumeroExte"]) if pd.notnull(prox["NumeroExte"]) and prox["NumeroExte"] > 0 else haversine(
                df_vertices.loc[u, "lat"], df_vertices.loc[u, "lon"],
                df_vertices.loc[v, "lat"], df_vertices.loc[v, "lon"]
            )

            situacao = prox["CodigoSitu"]
            if situacao == CODIGO_SITUACAO_ATIVA:
                tipo = "ativa"
                custo = dist * CUSTO_KM_ATIVA
            else:
                tipo = "desativada"
                custo = dist * CUSTO_KM_DESATIVADA

            chave = (min(u, v), max(u, v))
            if chave not in arestas_dict or custo < arestas_dict[chave]["custo_milhoes"]:
                arestas_dict[chave] = {
                    "origem": chave[0],
                    "destino": chave[1],
                    "distancia_km": round(dist, 3),
                    "custo_milhoes": round(custo, 3),
                    "tipo": tipo
                }

municipios_com_trem = set(estacoes["CodigoMuni"].dropna().astype(int))
mun_sem_trem = municipios[~municipios["CodigoMuni"].astype(int).isin(municipios_com_trem)].copy()

mun_sem_trem = mun_sem_trem.sort_values(by="PopulacaoM", ascending=False).head(TOP_MUNICIPIOS_CANDIDATOS)
centroides = mun_sem_trem.to_crs(epsg=5880).geometry.centroid.to_crs(epsg=4326)

novos_nos = []
for (_, row), pt in zip(mun_sem_trem.iterrows(), centroides):
    novos_nos.append({
        "id": len(df_vertices) + len(novos_nos),
        "codigo_original": int(row["CodigoMuni"]),
        "nome": str(row["NomeMunici"]).strip(),
        "uf": str(row["CodigoUF"]),
        "lat": round(pt.y, 6),
        "lon": round(pt.x, 6),
        "populacao": int(row["PopulacaoM"]) if pd.notnull(row["PopulacaoM"]) else 0,
        "tipo_no": "municipio_candidato"
    })

df_vertices = pd.concat([df_vertices, pd.DataFrame(novos_nos)], ignore_index=True)

tree_total = cKDTree(df_vertices[["lon", "lat"]].values)
coords_totais = df_vertices[["lon", "lat"]].values

for u in range(len(df_vertices)):
    _, vizinhos = tree_total.query(coords_totais[u], k=K_VIZINHOS_EXPANSAO + 1)
    for v in vizinhos[1:]:
        chave = (min(int(u), int(v)), max(int(u), int(v)))
        if chave not in arestas_dict:
            dist = haversine(df_vertices.loc[u, "lat"], df_vertices.loc[u, "lon"],
                             df_vertices.loc[v, "lat"], df_vertices.loc[v, "lon"])
            arestas_dict[chave] = {
                "origem": chave[0],
                "destino": chave[1],
                "distancia_km": round(dist, 3),
                "custo_milhoes": round(dist * CUSTO_KM_NOVA, 3),
                "tipo": "nova"
            }

df_arestas = pd.DataFrame(list(arestas_dict.values()))
df_vertices.to_csv("dados/vertices.csv", index=False)
df_arestas.to_csv("dados/arestas.csv", index=False)

print("=== DATASET GERADO COM SUCESSO ===")
print("Total de Vértices:", len(df_vertices))
print(df_vertices["tipo_no"].value_counts(), "\n")
print("Total de Arestas:", len(df_arestas))
print(df_arestas["tipo"].value_counts())