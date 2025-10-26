# 🤖 Sistema di Classificazione Email AI

<div align="center">

[![en](https://img.shields.io/badge/lang-English-blue.svg)](README_ENG.md)
[![it](https://img.shields.io/badge/lang-Italiano-green.svg)](README.md)

**[🇬🇧 English Version](README_ENG.md)** | **🇮🇹 Versione Italiana**

</div>

---

## 📧 Panoramica

Un **sistema intelligente di classificazione email** basato su AI che automatizza la gestione delle email di customer support. Il sistema analizza automaticamente le email in arrivo e determina:

- **Livello di Urgenza**: Critica, Alta, Media, Bassa
- **Routing Dipartimentale**: Tecnico, Billing, Vendite, Supporto

Perfetto per aziende che gestiscono grandi volumi di email di supporto clienti.

---

## ✨ Caratteristiche Principali

- 🎯 **Classificazione AI Dual-Model**: Modelli specializzati per urgenza e routing dipartimentale
- 🚀 **API REST**: Implementazione FastAPI production-ready con autenticazione
- 📬 **Integrazione Gmail**: Integrazione diretta con Gmail API per elaborazione automatica
- ⚡ **Alte Performance**: Elaborazione rapida con supporto batch
- 🔧 **Hot-Reload Config**: Aggiorna parametri senza riavviare il servizio
- 📊 **Monitoraggio Real-time**: Metriche di performance e controlli di salute
- 🔒 **Sicurezza Enterprise**: Autenticazione JWT, rate limiting, API keys

---

## 🏗️ Architettura

```
📦 Struttura Progetto
├── 🎯 api.py                      # API REST FastAPI
├── 🧠 email_classifier.py         # Orchestratore principale AI
├── 📧 gmail_classifier.py         # Integrazione Gmail API
├── 📁 config/                     # Gestione configurazione
│   ├── models.py                  # Modelli dati configurazione
│   ├── classifier.yaml            # Parametri AI/ML
│   └── classifier_production.yaml # Configurazione produzione
├── 🔬 classifiers/                # Classificatori specializzati
│   ├── urgency_classifier.py      # Analisi urgenza
│   └── department_classifier.py   # Routing dipartimenti
└── 🛠️ core/                       # Componenti core
    ├── models.py                  # Manager modelli AI
    ├── patterns.py                # Riconoscimento pattern
    └── validators.py              # Validazione input
```

---

## 🚀 Avvio Rapido

### Prerequisiti
```bash
Python 3.8+
4GB RAM minimo (8GB consigliati)
(Opzionale) Credenziali Gmail API per integrazione Gmail
```

### Installazione

```bash
# 1. Clona il repository
git clone [repository-url]
cd AI_customer_support

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. (Opzionale) Configura Gmail API
# Vedi sezione "Configurazione Gmail API" sotto

# 4. Avvia il server API
python api.py
# Server in esecuzione su: http://localhost:8000

# 5. (Opzionale) Testa la classificazione Gmail
python gmail_classifier.py
```

---

## 🔐 Configurazione Gmail API (Opzionale)

L'integrazione Gmail è **opzionale**. Il sistema funziona perfettamente tramite API REST senza Gmail. Se vuoi testare la classificazione diretta delle tue email Gmail, segui questi passaggi:

### Passo 1: Crea un Progetto su Google Cloud Console

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Clicca su **"Seleziona un progetto"** → **"Nuovo progetto"**
3. Inserisci un nome (es. "Email Classifier")
4. Clicca **"Crea"**

### Passo 2: Abilita Gmail API

1. Nel menu laterale, vai su **"API e servizi"** → **"Libreria"**
2. Cerca **"Gmail API"**
3. Clicca su **"Gmail API"** nei risultati
4. Clicca **"Abilita"**

### Passo 3: Configura la Schermata di Consenso OAuth

1. Nel menu laterale, vai su **"API e servizi"** → **"Schermata consenso OAuth"**
2. Seleziona **"Esterno"** come tipo di utente
3. Clicca **"Crea"**
4. Compila i campi obbligatori:
   - **Nome applicazione**: "Email Classifier"
   - **Email assistenza utente**: la tua email
   - **Email contatto sviluppatore**: la tua email
5. Clicca **"Salva e continua"**
6. Nella sezione **"Ambiti"**, clicca **"Aggiungi o rimuovi ambiti"**
7. Cerca e seleziona: `https://www.googleapis.com/auth/gmail.readonly`
8. Clicca **"Aggiorna"** → **"Salva e continua"**
9. Nella sezione **"Utenti di test"**, aggiungi la tua email Gmail
10. Clicca **"Salva e continua"**

### Passo 4: Crea le Credenziali

1. Nel menu laterale, vai su **"API e servizi"** → **"Credenziali"**
2. Clicca **"Crea credenziali"** → **"ID client OAuth"**
3. Seleziona **"Applicazione desktop"** come tipo di applicazione
4. Inserisci un nome (es. "Email Classifier Desktop")
5. Clicca **"Crea"**
6. Nella finestra popup, clicca **"Scarica JSON"**
7. Rinomina il file scaricato in `credentials.json`
8. Sposta `credentials.json` nella directory principale del progetto

### Passo 5: Primo Utilizzo

1. Esegui `python gmail_classifier.py`
2. Si aprirà automaticamente il browser con la schermata di login Google
3. Accedi con l'account Gmail che hai aggiunto come "utente di test"
4. Autorizza l'applicazione (potresti vedere un avviso "App non verificata", clicca "Avanzate" → "Vai a Email Classifier")
5. Un file `token.pickle` verrà creato automaticamente per le sessioni future

### ⚠️ Note Importanti

- Le credenziali sono **personali** e non devono essere condivise o caricate su repository pubblici
- Il file `credentials.json` permette **solo** l'accesso in lettura alle tue email (ambito `readonly`)
- Puoi revocare l'accesso in qualsiasi momento da [Impostazioni account Google](https://myaccount.google.com/permissions)

### 🔒 File da NON Caricare su Git

Aggiungi al tuo `.gitignore`:
```
credentials.json
token.pickle
gmail_report_*.html
gmail_report_*.txt
```

---

## 📡 API Endpoints

```bash
# Controllo salute e stato modelli
GET  /health

# Classifica singola email
POST /classify
{
  "subject": "Server non funziona",
  "testo_email": "Il database di produzione è crashato...",
  "sender": "ops@azienda.com"
}

# Classificazione batch
POST /classify/batch

# Statistiche sistema
GET  /stats

# Hot-reload configurazione
POST /config/reload
```

### Esempio Utilizzo API

```python
import requests

response = requests.post(
    'http://localhost:8000/classify',
    headers={'Authorization': 'Bearer demo_key_12345'},
    json={
        'subject': 'Server database non risponde',
        'testo_email': 'Il nostro sistema principale sembra down da stamattina...',
        'sender': 'ops@azienda.com'
    }
)

risultato = response.json()
print(f"Urgenza: {risultato['urgency']}")              # critical
print(f"Dipartimento: {risultato['department']}")      # technical
print(f"Confidenza: {risultato['overall_confidence']}") # 0.94
```

### API Keys per Testing

Il sistema include due chiavi di test:
- `demo_key_12345` - Tier basic (per demo e sviluppo)
- `prod_key_67890` - Tier premium (per simulazione produzione)

**Nota**: In produzione, sostituire con un sistema di autenticazione sicuro.

---

## 🎯 Esempi di Classificazione

### Scenario 1: Emergenza Tecnica
```
Input: "CRITICO: Database di produzione crashato"
Output:
├── Urgenza: CRITICA (confidenza alta)
├── Dipartimento: TECNICO (confidenza alta)
└── Azione: Auto-escalation → Team DevOps
```

### Scenario 2: Lead Commerciale
```
Input: "Interessati a una demo per 500 utenti"
Output:
├── Urgenza: ALTA (confidenza alta)
├── Dipartimento: VENDITE (confidenza alta)
└── Azione: Routing → Sales Manager
```

### Scenario 3: Problema Billing
```
Input: "Discrepanza fattura - addebitato due volte"
Output:
├── Urgenza: ALTA (confidenza alta)
├── Dipartimento: BILLING (confidenza alta)
└── Azione: Routing → Team Finance
```

---

## 🤖 Tecnologia AI

### Approccio Dual-Model

Il sistema utilizza **due classificatori AI specializzati** che lavorano in parallelo:

#### 1. Classificatore Urgenza
- Analizza tono emotivo e parole chiave
- Rileva indicatori time-sensitive
- Valuta impatto business
- Pattern: "emergenza", "down", "asap", "critico"

#### 2. Classificatore Dipartimento
- Riconoscimento contenuti tecnici
- Rilevamento terminologia finanziaria
- Pattern linguaggio vendite
- Analisi dominio mittente

### Modelli AI Utilizzati

- **Sentiment Analysis**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Emotion Detection**: `j-hartmann/emotion-english-distilroberta-base`
- **Zero-shot Classification**: `facebook/bart-large-mnli`

### Logica Cross-Validation

```python
# Regole di escalation intelligente
if dipartimento == 'tecnico' and urgenza == 'alta':
    parole_critiche = ['down', 'crashato', 'morto', 'fallito']
    if any(parola in contenuto):
        urgenza = 'critica'  # Auto-escalation
        confidenza += 0.1
```

---

## 🔧 Configurazione

Personalizza il comportamento tramite `config/classifier.yaml`:

```yaml
# Configurazione modelli AI
models:
  sentiment_model: "cardiffnlp/twitter-roberta-base-sentiment-latest"
  emotion_model: "j-hartmann/emotion-english-distilroberta-base"
  bert_model: "facebook/bart-large-mnli"
  use_gpu: true  # Usa GPU se disponibile
  max_text_length: 512

# Soglie di urgenza
urgency:
  critical_threshold: 4.0
  high_threshold: 2.0
  medium_threshold: 1.0
  low_threshold: 0.5

# Parametri di elaborazione
processing:
  max_email_length: 5000
  batch_size: 32
  enable_emotion_model: true
  enable_bert_model: true
  log_level: INFO

# Pesi pattern
weights:
  core_pattern_weight: 2.0
  department_signal_weight: 3.0
  caps_ratio_weight: 3.0
```

### Hot-Reload Configurazione

Puoi modificare i parametri e ricaricarli senza riavviare il server:

```bash
# Modifica config/classifier.yaml
# Poi ricarica via API:
curl -X POST http://localhost:8000/config/reload \
  -H "Authorization: Bearer demo_key_12345"
```

---

## 💼 Valore Business

### Benefici Operativi
- **Riduzione tempi di risposta**: Instradamento automatico immediato
- **Scalabilità**: Gestione volumi elevati senza aumento team
- **Diminuzione costi operativi**: Automazione del triage manuale
- **Miglioramento customer satisfaction**: Prioritizzazione corretta

### Casi d'Uso
- 🏢 Automazione customer support enterprise
- 📨 Triage email ad alto volume
- 🎯 Routing basato su priorità
- 📊 Classificazione ticket supporto
- 🔄 Coordinamento multi-dipartimentale

---

## 🧪 Testing e Validazione

### Esegui Suite di Validazione

```bash
python email_classifier.py
```

Questo eseguirà:
- Test su 4 scenari diversi (critico, basso, billing, sales)
- Validazione accuratezza urgenza e dipartimento
- Misurazione tempi di risposta
- Test hot-reload configurazione
- Test elaborazione batch

### Test Personalizzato

```python
from email_classifier import EmailClassifier

classifier = EmailClassifier("config/classifier.yaml")
classifier.load_models()

result = classifier.classify_email({
    'subject': 'Il tuo test',
    'testo_email': 'Il tuo contenuto',
    'sender': 'test@example.com'
})

print(f"Urgenza: {result['urgency']}")
print(f"Dipartimento: {result['department']}")
print(f"Confidenza: {result['overall_confidence']:.1%}")
```

---

## ⚠️ Limitazioni 

Questo progetto è stato sviluppato su **hardware laptop personale** con risorse limitate:

- Modelli pre-addestrati piccoli (non fine-tuned su dataset aziendali specifici)
- Inferenza solo CPU (nessuna accelerazione GPU utilizzata durante lo sviluppo)
- Dati di training limitati per validazione
- Sistema ottimizzato principalmente per email in **lingua inglese**

**In un ambiente enterprise** con risorse adeguate:
- L'accuratezza potrebbe essere significativamente migliorata con fine-tuning su dati aziendali
- Il tempo di risposta potrebbe essere ridotto con GPU dedicate
- Supporto per transformer più avanzati (BERT large, GPT)
- Apprendimento continuo su dati reali dell'azienda
- Supporto multi-lingua nativo

---

## 🔮 Roadmap Futura

### Miglioramenti Tecnici
- [ ] Integrazione modelli Transformer più avanzati (BERT large, GPT-4)
- [ ] Supporto multi-lingua (italiano, spagnolo, francese, tedesco)
- [ ] Fine-tuning su dataset aziendali specifici
- [ ] Apprendimento real-time da correzioni manuali
- [ ] Supporto per attachments e immagini nelle email

### Integrazioni
- [ ] CRM: Salesforce, Zendesk, HubSpot, Freshdesk
- [ ] Notifiche: Slack, Microsoft Teams, Discord
- [ ] Ticketing: Jira, Linear, Asana
- [ ] Email providers: Outlook, Office 365, Exchange

### Features
- [ ] Dashboard analytics avanzata con grafici
- [ ] App mobile per gestione priorità
- [ ] Sistema di feedback e correzione manuale
- [ ] Esportazione report personalizzati
- [ ] Webhook per integrazioni custom

---

## 📚 Stack Tecnologico

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **AI/ML**: 
  - PyTorch 
  - Transformers (Hugging Face)
  - scikit-learn
- **Integrazione**: Gmail API, OAuth 2.0
- **Configurazione**: YAML, Pydantic
- **API**: REST, autenticazione JWT
- **Monitoring**: Metriche real-time, health checks

---

## 📄 Licenza

Questo progetto è sviluppato come **dimostrazione portfolio**.

- ✅ Implementazione AI/Machine Learning
- ✅ Design e sviluppo API REST production-ready
- ✅ Integrazione sistemi esterni (Gmail, OAuth)
- ✅ Architettura modulare e manutenibile
- ✅ Codice production-ready con error handling
- ✅ Risoluzione problemi business reali con AI

---

## 🎯 Utilizzo per Demo

### Demo Live Suggerite

**1. Demo API tramite Swagger UI**
```bash
# Avvia il server
python api.py

# Apri browser su:
http://localhost:8000/docs
```

**2. Demo Classificazione Singola Email**
```bash
curl -X POST http://localhost:8000/classify \
  -H "Authorization: Bearer demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "URGENTE: Server principale down",
    "testo_email": "Il nostro database di produzione non risponde da 30 minuti. I clienti non possono effettuare ordini.",
    "sender": "ops@company.com"
  }'
```

**3. Demo Health Check**
```bash
curl http://localhost:8000/health
```

**4. Demo Gmail Integration** (se configurata)
```bash
python gmail_classifier.py
# Classificherà le ultime 10 email e genererà report HTML
```

## 📧 Contatto

email: vin.cenzo96@hotmail.it
linkedin: https://www.linkedin.com/in/vincenzo-vigna-931a202a
researchgate: https://www.researchgate.net/profile/Vincenzo-Vigna-2

---

<div align="center">

### 🌟 Tech Stack

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Gmail](https://img.shields.io/badge/Gmail_API-EA4335?style=for-the-badge&logo=gmail&logoColor=white)
![AI](https://img.shields.io/badge/AI/ML-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)

---

**[⬆ Torna su](#-sistema-di-classificazione-email-ai)**

</div>

