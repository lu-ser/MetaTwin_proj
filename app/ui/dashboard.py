# app/ui/dashboard.py
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import requests
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import networkx as nx
import plotly.figure_factory as ff
from app.config import settings
from app.ontology.manager import OntologyManager

# Inizializza il gestore dell'ontologia
ontology = OntologyManager()

# Inizializza l'app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# URL base per le API
API_BASE_URL = f"http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}"

# Layout dell'app
app.layout = dbc.Container([
    html.H1(settings.PROJECT_NAME, className="mt-4 mb-4"),
    
    dbc.Tabs([
        # Tab per la visualizzazione dei Digital Twins
        dbc.Tab([
            html.Div([
                html.H3("Seleziona un Digital Twin", className="mt-3"),
                dcc.Dropdown(
                    id='digital-twin-dropdown',
                    options=[],
                    placeholder="Seleziona un digital twin..."
                ),
                
                html.Div(id='digital-twin-info', className="mt-3"),
                
                html.H4("Dati dei Sensori", className="mt-4"),
                dcc.Dropdown(
                    id='sensor-type-dropdown',
                    options=[],
                    placeholder="Seleziona un tipo di sensore..."
                ),
                
                dcc.Graph(id='sensor-data-graph'),
                
                dbc.Button("Aggiorna", id="refresh-btn", color="primary", className="mt-3 me-2"),
                dbc.Button("Genera Dati Casuali", id="generate-data-btn", color="success", className="mt-3")
            ])
        ], label="Visualizza Digital Twin"),
        
        # Tab per la gestione dei Dispositivi
        dbc.Tab([
            html.Div([
                html.H3("Crea un Nuovo Dispositivo", className="mt-3"),
                
                dbc.Input(id="device-name-input", placeholder="Nome del dispositivo", type="text", className="mb-2"),
                
                html.H5("Tipo di Dispositivo:", className="mt-3"),
                dcc.Dropdown(
                    id='device-type-dropdown',
                    options=[],
                    placeholder="Seleziona un tipo di dispositivo..."
                ),
                
                html.H5("Attributi (opzionali):", className="mt-3"),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id='attr-name-dropdown',
                            options=[],
                            placeholder="Seleziona attributo..."
                        ), 
                        width=4
                    ),
                    dbc.Col(dbc.Input(id="attr-value-input", placeholder="Valore", type="number"), width=4),
                    dbc.Col(html.Div(id="attr-unit-display"), width=4),
                ]),
                dbc.Button("Aggiungi Attributo", id="add-attr-btn", color="secondary", className="mt-2"),
                
                html.Div(id="attributes-list", className="mt-3"),
                
                dbc.Button("Crea Dispositivo", id="create-device-btn", color="success", className="mt-4")
            ])
        ], label="Gestisci Dispositivi"),
        
        # Tab per la visualizzazione dell'Ontologia
        dbc.Tab([
            html.Div([
                html.H3("Visualizza Ontologia", className="mt-3"),
                
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Classi Radice"),
                            dcc.Dropdown(
                                id='root-class-dropdown',
                                options=[],
                                placeholder="Seleziona una classe radice..."
                            ),
                        ], width=6),
                        dbc.Col([
                            html.H5("Tutte le Classi"),
                            dcc.Dropdown(
                                id='all-class-dropdown',
                                options=[],
                                placeholder="Seleziona una classe..."
                            ),
                        ], width=6)
                    ]),
                    
                    html.Div(id="class-details", className="mt-4"),
                    
                    html.H5("Grafo delle Relazioni", className="mt-4"),
                    dcc.Graph(id="ontology-graph"),
                ]),
            ])
        ], label="Ontologia")
    ]),
    
], fluid=True)

# Callback per caricare i digital twins
@app.callback(
    Output('digital-twin-dropdown', 'options'),
    Input('refresh-btn', 'n_clicks')
)
def load_digital_twins(n_clicks):
    try:
        response = requests.get(f'{API_BASE_URL}/digital-twins/')
        if response.status_code == 200:
            digital_twins = response.json()
            return [{'label': dt['name'], 'value': dt['id']} for dt in digital_twins]
        return []
    except:
        return []

# Callback per caricare tutti i tipi di dispositivo dall'ontologia
@app.callback(
    Output('device-type-dropdown', 'options'),
    Input('refresh-btn', 'n_clicks')
)
def load_device_types(n_clicks):
    try:
        # Ottieni tutti i tipi dall'ontologia
        all_types = ontology.get_all_sensor_types()
        return [{'label': t, 'value': t} for t in all_types]
    except:
        return []

# Callback per caricare gli attributi in base al tipo di dispositivo selezionato
@app.callback(
    Output('attr-name-dropdown', 'options'),
    Input('device-type-dropdown', 'value')
)
def load_compatible_attributes(device_type):
    if not device_type:
        return []
    
    try:
        # Ottieni tutti gli attributi compatibili
        compatible_attrs = ontology.get_compatible_sensors(device_type)
        return [{'label': attr, 'value': attr} for attr in compatible_attrs]
    except:
        return []

# Callback per mostrare l'unità di misura dell'attributo selezionato
@app.callback(
    Output('attr-unit-display', 'children'),
    Input('attr-name-dropdown', 'value')
)
def display_unit_measure(attr_name):
    if not attr_name:
        return ""
    
    details = ontology.get_sensor_details(attr_name)
    if details and 'unitMeasure' in details:
        unit_measures = details['unitMeasure']
        if isinstance(unit_measures, list) and len(unit_measures) > 0:
            return f"Unità: {unit_measures[0]}"
    return "Unità: N/A"

# Callback per caricare le classi radice dell'ontologia
@app.callback(
    Output('root-class-dropdown', 'options'),
    Input('refresh-btn', 'n_clicks')
)
def load_root_classes(n_clicks):
    try:
        root_classes = ontology.get_root_classes()
        return [{'label': cls, 'value': cls} for cls in root_classes]
    except:
        return []

# Callback per caricare tutte le classi dell'ontologia
@app.callback(
    Output('all-class-dropdown', 'options'),
    Input('refresh-btn', 'n_clicks')
)
def load_all_classes(n_clicks):
    try:
        all_classes = ontology.get_all_sensor_types()
        return [{'label': cls, 'value': cls} for cls in all_classes]
    except:
        return []

# Callback per visualizzare i dettagli di una classe
@app.callback(
    [Output('class-details', 'children'),
     Output('ontology-graph', 'figure')],
    [Input('root-class-dropdown', 'value'),
     Input('all-class-dropdown', 'value')]
)
def display_class_details(root_class, all_class):
    # Prendi la classe selezionata (priorità alla classe specifica)
    selected_class = all_class if all_class else root_class
    
    if not selected_class:
        return html.Div(), go.Figure()
    
    details = ontology.get_sensor_details(selected_class)
    superclasses = ontology.get_all_superclasses(selected_class)
    subclasses = ontology.get_all_subclasses(selected_class)
    
    # Crea la visualizzazione dei dettagli
    details_div = html.Div([
        html.H4(f"Classe: {selected_class}"),
        
        html.H5("Dettagli:", className="mt-3"),
        html.Ul([
            html.Li(f"Unità di misura: {', '.join(details.get('unitMeasure', ['N/A']))}"),
            html.Li(f"Valore minimo: {details.get('min', 'N/A')}"),
            html.Li(f"Valore massimo: {details.get('max', 'N/A')}"),
            html.Li(f"Valore medio: {details.get('mean', 'N/A')}"),
        ]),
        
        html.H5("Superclassi:", className="mt-3"),
        html.Ul([html.Li(sc) for sc in superclasses]) if superclasses else html.P("Nessuna superclasse"),
        
        html.H5("Sottoclassi:", className="mt-3"),
        html.Ul([html.Li(sc) for sc in subclasses]) if subclasses else html.P("Nessuna sottoclasse"),
    ])
    
    # Crea il grafo delle relazioni
    G = nx.DiGraph()
    
    # Aggiungi nodi
    G.add_node(selected_class)
    for sc in superclasses:
        G.add_node(sc)
    for sc in subclasses:
        G.add_node(sc)
    
    # Aggiungi archi
    for sc in superclasses:
        if sc in details.get('superclass', []):
            G.add_edge(selected_class, sc)
        else:
            # Trova la connessione indiretta
            for direct_super in details.get('superclass', []):
                if sc in ontology.get_all_superclasses(direct_super):
                    G.add_edge(direct_super, sc)
                    if direct_super != selected_class:
                        G.add_edge(selected_class, direct_super)
    
    for sc in subclasses:
        if sc in ontology.subclass_relations.get(selected_class, []):
            G.add_edge(sc, selected_class)
        else:
            # Aggiungi eventuali connessioni indirette
            for direct_sub in ontology.subclass_relations.get(selected_class, []):
                if sc in ontology.get_all_subclasses(direct_sub):
                    G.add_edge(sc, direct_sub)
                    if direct_sub != selected_class:
                        G.add_edge(direct_sub, selected_class)
    
    # Crea la visualizzazione del grafo
    pos = nx.spring_layout(G)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        if node == selected_class:
            node_color.append('red')
        elif node in superclasses:
            node_color.append('blue')
        elif node in subclasses:
            node_color.append('green')
        else:
            node_color.append('gray')
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        marker=dict(
            showscale=False,
            color=node_color,
            size=15,
            line_width=2))
    
    fig = go.Figure(data=[edge_trace, node_trace],
                  layout=go.Layout(
                      showlegend=False,
                      hovermode='closest',
                      margin=dict(b=20, l=5, r=5, t=40),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                  )
    
    fig.update_layout(
        title=f"Grafo delle relazioni per {selected_class}",
        height=600,
    )
    
    return details_div, fig

# Callback per caricare le informazioni del digital twin
@app.callback(
    [Output('digital-twin-info', 'children'),
     Output('sensor-type-dropdown', 'options')],
    Input('digital-twin-dropdown', 'value')
)
def load_digital_twin_info(digital_twin_id):
    if not digital_twin_id:
        return html.Div(), []
    
    try:
        response = requests.get(f'{API_BASE_URL}/digital-twins/{digital_twin_id}')
        if response.status_code == 200:
            dt = response.json()
            
            # Informazioni del digital twin
            info = html.Div([
                html.P(f"Nome: {dt['name']}"),
                html.P(f"ID Dispositivo: {dt['device_id']}"),
                html.P(f"Tipo: {dt['device_type']}"),
                html.P(f"Ultimo aggiornamento: {dt['digital_replica'].get('last_updated', 'N/A')}"),
                
                html.H5("Sensori compatibili:", className="mt-3"),
                html.Ul([html.Li(sensor) for sensor in dt.get('compatible_sensors', [])]),
                
                html.H5("Operazioni disponibili:", className="mt-3"),
                html.Ul([html.Li(op) for op in dt['service_layer'].get('available_operations', [])]),
                
                html.H5("Dashboard disponibili:", className="mt-3"),
                html.Ul([html.Li(dash) for dash in dt['application_layer'].get('dashboards', [])]),
            ])
            
            # Opzioni del sensore
            sensor_options = []
            compatible_sensors = dt.get('compatible_sensors', [])
            sensor_data = dt['digital_replica'].get('sensor_data', {})
            
            for sensor in compatible_sensors:
                label = f"{sensor}"
                if sensor in sensor_data:
                    label += f" ({len(sensor_data[sensor])} misurazioni)"
                sensor_options.append({'label': label, 'value': sensor})
            
            return info, sensor_options
        
        return html.Div("Errore nel caricamento dei dati del digital twin"), []
    except:
        return html.Div("Errore nella richiesta"), []

# Callback per visualizzare i dati del sensore
@app.callback(
    Output('sensor-data-graph', 'figure'),
    [Input('digital-twin-dropdown', 'value'),
     Input('sensor-type-dropdown', 'value')]
)
def update_sensor_graph(digital_twin_id, sensor_type):
    if not digital_twin_id or not sensor_type:
        return go.Figure()
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/digital-twins/{digital_twin_id}/data',
            params={'sensor_type': sensor_type}
        )
        
        if response.status_code == 200:
            data = response.json()
            if sensor_type in data and data[sensor_type]:
                # Converte i dati in un dataframe
                df = pd.DataFrame(data[sensor_type])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                # Ottieni i dettagli del sensore dall'ontologia
                sensor_details = ontology.get_sensor_details(sensor_type)
                
                # Crea il grafico
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['value'],
                    mode='lines+markers',
                    name=sensor_type
                ))
                
                # Aggiungi linee di riferimento per min, max e mean se disponibili
                if sensor_details:
                    if 'min' in sensor_details:
                        fig.add_shape(
                            type="line",
                            x0=df['timestamp'].min(),
                            x1=df['timestamp'].max(),
                            y0=sensor_details['min'],
                            y1=sensor_details['min'],
                            line=dict(color="red", width=1, dash="dash"),
                            name="Min"
                        )
                    
                    if 'max' in sensor_details:
                        fig.add_shape(
                            type="line",
                            x0=df['timestamp'].min(),
                            x1=df['timestamp'].max(),
                            y0=sensor_details['max'],
                            y1=sensor_details['max'],
                            line=dict(color="red", width=1, dash="dash"),
                            name="Max"
                        )
                    
                    if 'mean' in sensor_details:
                        fig.add_shape(
                            type="line",
                            x0=df['timestamp'].min(),
                            x1=df['timestamp'].max(),
                            y0=sensor_details['mean'],
                            y1=sensor_details['mean'],
                            line=dict(color="green", width=1, dash="dash"),
                            name="Mean"
                        )
                
                # Formatta il grafico
                unit = df['unit_measure'].iloc[0] if not df['unit_measure'].empty else ""
                fig.update_layout(
                    title=f'Dati del sensore: {sensor_type}',
                    xaxis_title='Tempo',
                    yaxis_title=f'Valore ({unit})',
                    template='plotly_white'
                )
                
                return fig
        
        return go.Figure()
    except Exception as e:
        print(f"Errore: {e}")
        return go.Figure()

# Callback per generare dati casuali
@app.callback(
    Output('sensor-data-graph', 'figure', allow_duplicate=True),
    Input('generate-data-btn', 'n_clicks'),
    [State('digital-twin-dropdown', 'value'),
     State('sensor-type-dropdown', 'value')],
    prevent_initial_call=True
)
def generate_random_data(n_clicks, digital_twin_id, sensor_type):
    if not digital_twin_id:
        return go.Figure()
    
    try:
        # Genera dati casuali
        response = requests.post(
            f'{API_BASE_URL}/digital-twins/{digital_twin_id}/generate-data'
        )
        
        if response.status_code == 201:
            # Aggiorna il grafico
            return update_sensor_graph(digital_twin_id, sensor_type)
        
        return go.Figure()
    except:
        return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=settings.DEBUG, port=settings.DASHBOARD_PORT)