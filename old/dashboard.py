import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Qui puoi visualizzare gli utenti.", className="card-text"),
            dbc.Button("Visualizza Utenti", id="view-users-btn", color="primary"),
        ]
    ),
    className="mt-3",
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Utilizza questa scheda per cercare gli utenti per ID.", className="card-text"),
            dbc.Input(id="user-id-input", placeholder="Inserisci ID utente...", type="text"),
            dbc.Button("Cerca Utente", id="search-user-btn", color="secondary", className="mt-2"),
        ]
    ),
    className="mt-3",
)

app.layout = dbc.Container(
    [
        dbc.Tabs(
            [
                dbc.Tab(tab1_content, label="Visualizza Utenti"),
                dbc.Tab(tab2_content, label="Cerca Utente"),
            ]
        ),
        html.Div(id="page-content")
    ],
    fluid=True,
)

def fetch_user_data():
    response = requests.get('http://localhost:8000/users')
    if response.status_code == 200:
        data = response.json()
        print(data)  # Aggiungi questa linea per debug
        return data
    return []


def search_user_by_id(user_id):
    url = f'http://localhost:8000/users/{user_id}'
    response = requests.get(url)
    print(f"URL requested: {url}")  # Stampa l'URL per confermare che sia corretto
    print(f"Status Code: {response.status_code}")  # Controlla lo status code della risposta
    if response.status_code == 200:
        print("Response: ", response.json())  # Stampa la risposta per confermare i dati
        return response.json()
    else:
        print("Failed to fetch data")  # Informazioni aggiuntive in caso di errore
    return None


@app.callback(
    Output('page-content', 'children'),
    [Input('view-users-btn', 'n_clicks'),
     Input('search-user-btn', 'n_clicks')],
    [State('user-id-input', 'value')],
    prevent_initial_call=True
)
def render_content(view_users_n_clicks, search_user_n_clicks, user_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Premi un bottone per visualizzare i dati."
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "view-users-btn":
            users = fetch_user_data()
            if users and all('_id' in user for user in users):  # Verifica che tutti gli utenti abbiano un '_id'
                return html.Ul([
                    html.Li(f"ID: {user['_id']}, Nome: {user['name']}, Dispositivi: {[device['name'] for device in user.get('devices', [])]}")
                    for user in users
                ])
            else:
                return "Nessun utente trovato o dati utente non completi."
        elif button_id == "search-user-btn" and user_id:
            result = search_user_by_id(user_id)
            if result and '_id' in result:
                devices_list = ', '.join([device['name'] for device in result.get('devices', [])])
                return html.Div(f"Risultato della ricerca: ID: {result['_id']}, Nome: {result['name']}, Dispositivi: {devices_list}")
            else:
                return html.Div("Nessun utente trovato con l'ID specificato.")

if __name__ == "__main__":
    app.run_server(debug=True)
