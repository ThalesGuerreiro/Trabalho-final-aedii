import geopandas as gpd

estacoes = gpd.read_file("dados/ShapeFileMar-2026/Estação2026.shp")
linhas = gpd.read_file("dados/ShapeFileMar-2026/LinhaEstação2026.shp")
municipios = gpd.read_file("dados/ShapeFileMar-2026/Municipio2026.shp")

print("=====================================================================================================================================================================")

print("\nEstações")
print("Total:", len(estacoes))
print("Colunas:", estacoes.columns.tolist())
print(estacoes.drop(columns="geometry").head(3), "\n")

print("=====================================================================================================================================================================")

print("\nLinhas")
print("Total:", len(linhas))
print("Colunas:", linhas.columns.tolist())
print(linhas.drop(columns="geometry").head(3), "\n")

print("=====================================================================================================================================================================")

for col in linhas.select_dtypes(include=["object"]).columns:
    valores = linhas[col].dropna().unique()
    if len(valores) < 20:
        print(f"Valores únicos em '{col}':", valores)

print("=====================================================================================================================================================================")

print("\nMunicípios")
print("Total:", len(municipios))
print("Colunas:", municipios.columns.tolist())

print("=====================================================================================================================================================================")

print("Situação Estações:\n", estacoes["CodigoSitu"].value_counts(dropna=False))
print("\nSituação Linhas:\n", linhas["CodigoSitu"].value_counts(dropna=False))

print("=====================================================================================================================================================================")