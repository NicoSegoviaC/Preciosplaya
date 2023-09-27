import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

df = pd.read_csv("precios_database_27jul_2009_2022_Ed.csv", encoding="utf-8", sep=";")

# Filtrar el DataFrame para obtener solo los datos de los últimos 10 años
end_date = pd.to_datetime("2021-11-01")
start_date = end_date - pd.DateOffset(years=20)

df["Fecha"] = pd.to_datetime(df["año"].astype(int).astype(str) + "-" + df["mes"].astype(str).str.zfill(2))

df_last_10_years = df[(df["Fecha"] >= start_date) & (df["Fecha"] <= end_date)].copy()

# Convertir la columna "precio_ton" a valores numéricos y reemplazar valores no válidos por NaN
df_last_10_years["precio_ton"] = pd.to_numeric(df_last_10_years["precio_ton"], errors="coerce")

# Convertir la columna "año" a int
df_last_10_years["año"] = df_last_10_years["año"].astype(int)

# Eliminar filas con valores NaN en la columna "Especie"
df_last_10_years = df_last_10_years.dropna(subset=["Especie"])

# Filtrar las especies que tienen registros en al menos 5 años diferentes
species_counts = df_last_10_years.groupby("Especie")["año"].nunique()
valid_species = species_counts[species_counts >= 5].index.tolist()
df_last_10_years = df_last_10_years[df_last_10_years["Especie"].isin(valid_species)]

# Obtener la lista de especies únicas y ordenarlas alfabéticamente
especies = sorted(df_last_10_years["Especie"].unique())

# Inicializar la app
app = dash.Dash(__name__)

# Definir la estructura de la app
app.layout = html.Div([
    dcc.Dropdown(
        id='especie-dropdown',
        options=[{'label': especie, 'value': especie} for especie in especies],
        value=especies[0]
    ),
    dcc.Graph(id='especie-graph')
])

# Definir el comportamiento interactivo
@app.callback(
    Output('especie-graph', 'figure'),
    [Input('especie-dropdown', 'value')]
)
def update_figure(selected_especie):
    df_especie = df_last_10_years[df_last_10_years["Especie"] == selected_especie]
    df_especie_aggregated = df_especie.groupby("año")["precio_ton"].agg(['mean', 'std']).reset_index()

    # Obtener el nombre científico para la especie seleccionada
    spp_scname = df_especie["spp_scname"].iloc[0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_especie_aggregated["año"], 
        y=df_especie_aggregated["mean"],
        mode='lines+markers', 
        name="Precio promedio",
        line=dict(color='grey', width=1),
        error_y=dict(
            type='data', 
            array=df_especie_aggregated["std"],
            visible=True,
            color='black',
            thickness=1.2
        )
    ))

    fig.update_layout(title=f"Precio promedio anual de {selected_especie} ({spp_scname})",
                      xaxis_title="Año",
                      yaxis_title="Precio (Toneladas). CLP",
                      legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      showlegend=True,
                      template="plotly_white")
    
    return fig

# Iniciar la app
if __name__ == '__main__':
    app.run_server(app.run_server(debug=True))
