# MetaTwin Platform

## Piattaforma Digital Twin con Autenticazione

Questo progetto implementa una piattaforma di Digital Twin per la gestione di dispositivi e sensori IoT con un sistema di autenticazione JWT per proteggere le API.

### Caratteristiche

- Autenticazione utenti con JWT (JSON Web Tokens)
- Gestione di dispositivi IoT e digital twins
- API sicure per la creazione, lettura, aggiornamento e cancellazione (CRUD)
- Controllo degli accessi basato sull'identità
- Autenticazione dei dispositivi tramite API keys

### Configurazione

Per eseguire il progetto, installare le dipendenze:

```bash
pip install -r requirements.txt
```

### Variabili d'ambiente

Il progetto utilizza le seguenti variabili d'ambiente che possono essere configurate in un file `.env`:

```
SECRET_KEY=chiave_segreta_per_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=digital_twins_db
```

### API di autenticazione

- `/api/v1/auth/register` - Registrazione utente
- `/api/v1/auth/login` - Login utente
- `/api/v1/auth/token` - Ottieni token JWT
- `/api/v1/auth/me` - Informazioni sull'utente corrente

### Utilizzo delle API protette

Tutte le API PUT e POST richiedono un token JWT valido nel header della richiesta:

```
Authorization: Bearer <token>
```

I dispositivi possono utilizzare l'autenticazione API key tramite l'header:

```
X-API-Key: <api_key>
```