import geopandas as gpd
import pyogrio  

arquivo = "Fluxos rodoviáros/fluxos_rodo_od.gpkg"

camadas = pyogrio.list_layers(arquivo)
print("Camadas disponíveis:", camadas)

nome_camada = camadas[0][0]
df = gpd.read_file(arquivo, layer=nome_camada, ignore_geometry=True)

print("\nTotal de linhas:", len(df))
print("Colunas:", df.columns.tolist())
print("\nPrimeiras 3 linhas:")
print(df.head(3))

for col in df.columns:
    if any(p in col.lower() for p in ["merc", "prod", "carga", "grupo", "desc"]):
        print(f"\nValores únicos em '{col}':")
        print(df[col].dropna().unique()[:25])