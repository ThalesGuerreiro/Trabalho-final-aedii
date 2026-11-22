import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

CODIGO_SITUACAO_ATIVA = 1

CUSTO_KM_ATIVA      = 0.0#Já opera
CUSTO_KM_DESATIVADA = 3.0#Revitalização (R$ 3mi/km)
CUSTO_KM_NOVA       = 15.0#Construção nova (R$15 mi/km)

#Baseado na economia modal ferroviário vs. rodoviário por tonelada-km / viagem
FATOR_LUCRO_FERR_TON_KM = 0.0000015  # R$0,15/ton-km em 10 anos
FATOR_LUCRO_RODO_CIOT_KM = 0.0008    # R$800/viagem convertida por km em 10 anos

TOP_MUNICIPIOS_CANDIDATOS = 400
K_VIZINHOS_EXPANSAO       = 4

def carregar_shp(caminho):
    gdf = gpd.read_file(caminho)
    if gdf.crs is None:
        return gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=4326)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

print("1. Lendo fluxos Origem-Destino do IBGE (Ferroviário e Rodoviário)...")
df_ferr = gpd.read_file("Fluxos ferroviários/fluxos_ferr_od.gpkg", layer="base_para_app_produtos_ferr", ignore_geometry=True)
df_rodo = gpd.read_file("Fluxos rodoviáros/fluxos_rodo_od.gpkg", layer="base_para_app_produtos_rodo", ignore_geometry=True)

grupos_agro_ferr = ["Setor Agrícola, Extração Vegetal e Celulose"]
grupos_min_ferr  = ["Minério de Ferro", "Indústria Siderúrgica, Cimento e Construção Civil"]

ferr_agro = df_ferr[df_ferr["GR_MERC_ANTT"].isin(grupos_agro_ferr)]
ferr_min  = df_ferr[df_ferr["GR_MERC_ANTT"].isin(grupos_min_ferr)]

carga_ferr_agro_mun = pd.concat([
    ferr_agro.groupby("CODMUN_O")["QTD_CARGA"].sum(),
    ferr_agro.groupby("CODMUN_D")["QTD_CARGA"].sum()
]).groupby(level=0).sum().to_dict()

carga_ferr_min_mun = pd.concat([
    ferr_min.groupby("CODMUN_O")["QTD_CARGA"].sum(),
    ferr_min.groupby("CODMUN_D")["QTD_CARGA"].sum()
]).groupby(level=0).sum().to_dict()

df_rodo["Desc_secao_clean"] = df_rodo["Desc_secao"].astype(str).str.strip()
rodo_agro = df_rodo[df_rodo["Desc_secao_clean"] == "Produtos do reino vegetal"]
rodo_min  = df_rodo[df_rodo["Desc_secao_clean"] == "Produtos minerais"]

ciots_agro_mun = pd.concat([
    rodo_agro.groupby("CODMUN_O")["QTD_CIOTS"].sum(),
    rodo_agro.groupby("CODMUN_D")["QTD_CIOTS"].sum()
]).groupby(level=0).sum().to_dict()

ciots_min_mun = pd.concat([
    rodo_min.groupby("CODMUN_O")["QTD_CIOTS"].sum(),
    rodo_min.groupby("CODMUN_D")["QTD_CIOTS"].sum()
]).groupby(level=0).sum().to_dict()

print("2. Carregando Shapefiles da Malha e Municípios...")
estacoes = carregar_shp("ShapeFileMar-2026/Estação2026.shp")
linhas = carregar_shp("ShapeFileMar-2026/LinhaEstação2026.shp")
municipios = carregar_shp("ShapeFileMar-2026/Municipio2026.shp")

estacoes = estacoes[estacoes.geometry.notnull()].copy()
estacoes["lat"] = estacoes.geometry.y
estacoes["lon"] = estacoes.geometry.x

vertices_lista = []
mapa_codigo_para_id = {}

for _, row in estacoes.iterrows():
    cod_est = int(row["CodigoEsta"])
    cod_mun = int(row["CodigoMuni"]) if pd.notnull(row["CodigoMuni"]) else 0
    if cod_est not in mapa_codigo_para_id:
        novo_id = len(vertices_lista)
        mapa_codigo_para_id[cod_est] = novo_id
        vertices_lista.append({
            "id": novo_id,
            "codigo_original": cod_est,
            "codigo_muni": cod_mun,
            "nome": str(row["NomeEstaca"]).strip(),
            "uf": str(cod_mun)[:2],
            "lat": round(row["lat"], 6),
            "lon": round(row["lon"], 6),
            "eh_porto": int(pd.notnull(row["CodigoPort"])),
            "demanda_ferr_agro_ton": float(carga_ferr_agro_mun.get(cod_mun, 0.0)),
            "demanda_ferr_min_ton": float(carga_ferr_min_mun.get(cod_mun, 0.0)),
            "demanda_rodo_agro_ciots": float(ciots_agro_mun.get(cod_mun, 0.0)),
            "demanda_rodo_min_ciots": float(ciots_min_mun.get(cod_mun, 0.0)),
            "tipo_no": "estacao"
        })

df_vertices = pd.DataFrame(vertices_lista)

municipios_com_trem = set(estacoes["CodigoMuni"].dropna().astype(int))
mun_sem_trem = municipios[~municipios["CodigoMuni"].astype(int).isin(municipios_com_trem)].copy()

mun_sem_trem["score_demanda"] = mun_sem_trem["CodigoMuni"].astype(int).map(
    lambda m: ciots_agro_mun.get(m, 0.0) + ciots_min_mun.get(m, 0.0)
)
mun_sem_trem = mun_sem_trem.sort_values(by="score_demanda", ascending=False).head(TOP_MUNICIPIOS_CANDIDATOS)
centroides = mun_sem_trem.to_crs(epsg=5880).geometry.centroid.to_crs(epsg=4326)

novos_nos = []
for (_, row), pt in zip(mun_sem_trem.iterrows(), centroides):
    cod_mun = int(row["CodigoMuni"])
    novos_nos.append({
        "id": len(df_vertices) + len(novos_nos),
        "codigo_original": cod_mun,
        "codigo_muni": cod_mun,
        "nome": str(row["NomeMunici"]).strip(),
        "uf": str(row["CodigoUF"]),
        "lat": round(pt.y, 6),
        "lon": round(pt.x, 6),
        "eh_porto": 0,
        "demanda_ferr_agro_ton": 0.0,
        "demanda_ferr_min_ton": 0.0,
        "demanda_rodo_agro_ciots": float(ciots_agro_mun.get(cod_mun, 0.0)),
        "demanda_rodo_min_ciots": float(ciots_min_mun.get(cod_mun, 0.0)),
        "tipo_no": "municipio_candidato"
    })

df_vertices = pd.concat([df_vertices, pd.DataFrame(novos_nos)], ignore_index=True)

def calcular_lucros_aresta(u, v, dist_km):
    row_u = df_vertices.loc[u]
    row_v = df_vertices.loc[v]
    
    fator_porto = 1.4 if (row_u["eh_porto"] == 1 or row_v["eh_porto"] == 1) else 1.0
    
    ton_agro = (row_u["demanda_ferr_agro_ton"] + row_v["demanda_ferr_agro_ton"]) / 2.0
    ton_min  = (row_u["demanda_ferr_min_ton"]  + row_v["demanda_ferr_min_ton"]) / 2.0
    ciot_agro = (row_u["demanda_rodo_agro_ciots"] + row_v["demanda_rodo_agro_ciots"]) / 2.0
    ciot_min  = (row_u["demanda_rodo_min_ciots"]  + row_v["demanda_rodo_min_ciots"]) / 2.0
    
    lucro_agro = dist_km * (ton_agro * FATOR_LUCRO_FERR_TON_KM + ciot_agro * FATOR_LUCRO_RODO_CIOT_KM) * fator_porto
    lucro_min  = dist_km * (ton_min  * FATOR_LUCRO_FERR_TON_KM + ciot_min  * FATOR_LUCRO_RODO_CIOT_KM) * fator_porto
    
    return round(lucro_agro, 4), round(lucro_min, 4), round(lucro_agro + lucro_min, 4)

arestas_dict = {}
linhas_ordenadas = linhas.sort_values(by=["CodigoLi_1", "NumeroSequ"])

for _, grupo in linhas_ordenadas.groupby("CodigoLi_1"):
    registros = grupo.to_dict("records")
    for i in range(len(registros) - 1):
        atual, prox = registros[i], registros[i + 1]
        cod_u, cod_v = int(atual["CodigoEsta"]), int(prox["CodigoEsta"])

        if cod_u in mapa_codigo_para_id and cod_v in mapa_codigo_para_id:
            u, v = mapa_codigo_para_id[cod_u], mapa_codigo_para_id[cod_v]
            if u == v:
                continue

            dist = float(prox["NumeroExte"]) if pd.notnull(prox["NumeroExte"]) and prox["NumeroExte"] > 0 else haversine(
                df_vertices.loc[u, "lat"], df_vertices.loc[u, "lon"],
                df_vertices.loc[v, "lat"], df_vertices.loc[v, "lon"]
            )
            if dist > 300.0:  #remove saltos de cadastro incorretos no shapefile da antt
                continue

            if prox["CodigoSitu"] == CODIGO_SITUACAO_ATIVA:
                tipo, custo = "ativa", dist * CUSTO_KM_ATIVA
            else:
                tipo, custo = "desativada", dist * CUSTO_KM_DESATIVADA

            l_agro, l_min, l_tot = calcular_lucros_aresta(u, v, dist)
            chave = (min(u, v), max(u, v))
            if chave not in arestas_dict or custo < arestas_dict[chave]["custo_milhoes"]:
                arestas_dict[chave] = {
                    "origem": chave[0],
                    "destino": chave[1],
                    "distancia_km": round(dist, 3),
                    "custo_milhoes": round(custo, 3),
                    "lucro_agro_milhoes": l_agro,
                    "lucro_minerio_milhoes": l_min,
                    "lucro_total_milhoes": l_tot,
                    "tipo": tipo
                }

tree_total = cKDTree(df_vertices[["lon", "lat"]].values)
coords_totais = df_vertices[["lon", "lat"]].values

for u in range(len(df_vertices)):
    _, vizinhos = tree_total.query(coords_totais[u], k=K_VIZINHOS_EXPANSAO + 1)
    for v in vizinhos[1:]:
        chave = (min(int(u), int(v)), max(int(u), int(v)))
        if chave not in arestas_dict:
            dist = haversine(df_vertices.loc[u, "lat"], df_vertices.loc[u, "lon"],
                             df_vertices.loc[v, "lat"], df_vertices.loc[v, "lon"])
            l_agro, l_min, l_tot = calcular_lucros_aresta(chave[0], chave[1], dist)
            arestas_dict[chave] = {
                "origem": chave[0],
                "destino": chave[1],
                "distancia_km": round(dist, 3),
                "custo_milhoes": round(dist * CUSTO_KM_NOVA, 3),
                "lucro_agro_milhoes": l_agro,
                "lucro_minerio_milhoes": l_min,
                "lucro_total_milhoes": l_tot,
                "tipo": "nova"
            }

df_arestas = pd.DataFrame(list(arestas_dict.values()))
df_vertices.to_csv("vertices.csv", index=False)
df_arestas.to_csv("arestas.csv", index=False)

print("=== DATASET ENRIQUECIDO GERADO COM SUCESSO ===")
print("Vértices:", len(df_vertices), "| Arestas:", len(df_arestas))
print("Lucro Potencial Médio por Aresta (R$ mi):", round(df_arestas["lucro_total_milhoes"].mean(), 2))