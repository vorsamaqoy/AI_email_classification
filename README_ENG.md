# 🤖 AI Email Classification System

<div align="center">

[![en](https://img.shields.io/badge/lang-English-blue.svg)](README_ENG.md)
[![it](https://img.shields.io/badge/lang-Italiano-green.svg)](README.md)

**🇬🇧 English Version** | **[🇮🇹 Versione Italiana](README.md)**

</div>

---

## 📧 Overview

An **intelligent email classification system** powered by AI that automates customer support email management. The system automatically analyzes incoming emails and determines:

- **Urgency Level**: Critical, High, Medium, Low
- **Department Routing**: Technical, Billing, Sales, Support

Perfect for companies handling high volumes of customer support emails.

---

## ✨ Key Features

- 🎯 **Dual-Model AI Classification**: Specialized models for urgency and department routing
- 🚀 **REST API**: Production-ready FastAPI implementation with authentication
- 📬 **Gmail Integration**: Direct integration with Gmail API for automated processing
- ⚡ **High Performance**: Fast processing with batch support
- 🔧 **Hot-Reload Config**: Update parameters without restarting the service
- 📊 **Real-time Monitoring**: Performance metrics and health checks
- 🔒 **Enterprise Security**: JWT authentication, rate limiting, API keys

---

## 🏗️ Architecture

```
📦 Project Structure
├── 🎯 api.py                      # FastAPI REST API
├── 🧠 email_classifier.py         # Main AI orchestrator
├── 📧 gmail_classifier.py         # Gmail API integration
├── 📁 config/                     # Configuration management
│   ├── models.py                  # Config data models
│   ├── classifier.yaml            # AI/ML parameters
│   └── classifier_production.yaml # Production configuration
├── 🔬 classifiers/                # Specialized classifiers
│   ├── urgency_classifier.py      # Urgency analysis
│   └── department_classifier.py   # Department routing
└── 🛠️ core/                       # Core components
    ├── models.py                  # AI model manager
    ├── patterns.py                # Pattern recognition
    └── validators.py              # Input validation
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
4GB RAM minimum (8GB recommended)
(Optional) Gmail API credentials for Gmail integration
```

### Installation

```bash
# 1. Clone the repository
git clone [repository-url]
cd AI_customer_support

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure Gmail API
# See "Gmail API Configuration" section below

# 4. Start the API server
python api.py
# Server running at: http://localhost:8000

# 5. (Optional) Test Gmail classification
python gmail_classifier.py
```

---

## 🔐 Gmail API Configuration (Optional)

Gmail integration is **optional**. The system works perfectly via REST API without Gmail. If you want to test direct classification of your Gmail emails, follow these steps:

### Step 1: Create a Project on Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New project"**
3. Enter a name (e.g., "Email Classifier")
4. Click **"Create"**

### Step 2: Enable Gmail API

1. In the side menu, go to **"APIs & Services"** → **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"** in the results
4. Click **"Enable"**

### Step 3: Configure OAuth Consent Screen

1. In the side menu, go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** as user type
3. Click **"Create"**
4. Fill in the required fields:
   - **Application name**: "Email Classifier"
   - **User support email**: your email
   - **Developer contact email**: your email
5. Click **"Save and continue"**
6. In the **"Scopes"** section, click **"Add or remove scopes"**
7. Search for and select: `https://www.googleapis.com/auth/gmail.readonly`
8. Click **"Update"** → **"Save and continue"**
9. In the **"Test users"** section, add your Gmail email
10. Click **"Save and continue"**

### Step 4: Create Credentials

1. In the side menu, go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create credentials"** → **"OAuth client ID"**
3. Select **"Desktop app"** as application type
4. Enter a name (e.g., "Email Classifier Desktop")
5. Click **"Create"**
6. In the popup window, click **"Download JSON"**
7. Rename the downloaded file to `credentials.json`
8. Move `credentials.json` to the project root directory

### Step 5: First Use

1. Run `python gmail_classifier.py`
2. Your browser will automatically open with the Google login screen
3. Sign in with the Gmail account you added as a "test user"
4. Authorize the application (you may see a "App not verified" warning, click "Advanced" → "Go to Email Classifier")
5. A `token.pickle` file will be automatically created for future sessions

### ⚠️ Important Notes

- Credentials are **personal** and should not be shared or uploaded to public repositories
- The `credentials.json` file allows **only** read-only access to your emails (`readonly` scope)
- You can revoke access anytime from [Google Account Settings](https://myaccount.google.com/permissions)

### 🔒 Files NOT to Upload to Git

Add to your `.gitignore`:
```
credentials.json
token.pickle
gmail_report_*.html
gmail_report_*.txt
```

---

## 📡 API Endpoints

```bash
# Health check and model status
GET  /health

# Classify single email
POST /classify
{
  "subject": "Server is down",
  "testo_email": "Production database crashed...",
  "sender": "ops@company.com"
}

# Batch classification
POST /classify/batch

# System statistics
GET  /stats

# Hot-reload configuration
POST /config/reload
```

### Example API Usage

```python
import requests

response = requests.post(
    'http://localhost:8000/classify',
    headers={'Authorization': 'Bearer demo_key_12345'},
    json={
        'subject': 'Database server not responding',
        'testo_email': 'Our main system appears to be down since this morning...',
        'sender': 'ops@company.com'
    }
)

result = response.json()
print(f"Urgency: {result['urgency']}")              # critical
print(f"Department: {result['department']}")        # technical
print(f"Confidence: {result['overall_confidence']}") # 0.94
```

### API Keys for Testing

The system includes two test keys:
- `demo_key_12345` - Basic tier (for demo and development)
- `prod_key_67890` - Premium tier (for production simulation)

**Note**: In production, replace with a secure authentication system.

---

## 🎯 Classification Examples

### Scenario 1: Technical Emergency
```
Input: "CRITICAL: Production database crashed"
Output:
├── Urgency: CRITICAL (high confidence)
├── Department: TECHNICAL (high confidence)
└── Action: Auto-escalation → DevOps Team
```

### Scenario 2: Sales Lead
```
Input: "Interested in a demo for 500 users"
Output:
├── Urgency: HIGH (high confidence)
├── Department: SALES (high confidence)
└── Action: Route → Sales Manager
```

### Scenario 3: Billing Issue
```
Input: "Invoice discrepancy - charged twice"
Output:
├── Urgency: HIGH (high confidence)
├── Department: BILLING (high confidence)
└── Action: Route → Finance Team
```

---

## 🤖 AI Technology

### Dual-Model Approach

The system uses **two specialized AI classifiers** working in parallel:

#### 1. Urgency Classifier
- Analyzes emotional tone and keywords
- Detects time-sensitive indicators
- Evaluates business impact
- Patterns: "emergency", "down", "asap", "critical"

#### 2. Department Classifier
- Technical content recognition
- Financial terminology detection
- Sales language patterns
- Sender domain analysis

### AI Models Used

- **Sentiment Analysis**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Emotion Detection**: `j-hartmann/emotion-english-distilroberta-base`
- **Zero-shot Classification**: `facebook/bart-large-mnli`

### Cross-Validation Logic

```python
# Intelligent escalation rules
if department == 'technical' and urgency == 'high':
    critical_keywords = ['down', 'crashed', 'dead', 'failed']
    if any(keyword in content):
        urgency = 'critical'  # Auto-escalate
        confidence += 0.1
```

---

## 🔧 Configuration

Customize behavior via `config/classifier.yaml`:

```yaml
# AI models configuration
models:
  sentiment_model: "cardiffnlp/twitter-roberta-base-sentiment-latest"
  emotion_model: "j-hartmann/emotion-english-distilroberta-base"
  bert_model: "facebook/bart-large-mnli"
  use_gpu: true  # Use GPU if available
  max_text_length: 512

# Urgency thresholds
urgency:
  critical_threshold: 4.0
  high_threshold: 2.0
  medium_threshold: 1.0
  low_threshold: 0.5

# Processing parameters
processing:
  max_email_length: 5000
  batch_size: 32
  enable_emotion_model: true
  enable_bert_model: true
  log_level: INFO

# Pattern weights
weights:
  core_pattern_weight: 2.0
  department_signal_weight: 3.0
  caps_ratio_weight: 3.0
```

### Hot-Reload Configuration

You can modify parameters and reload them without restarting the server:

```bash
# Edit config/classifier.yaml
# Then reload via API:
curl -X POST http://localhost:8000/config/reload \
  -H "Authorization: Bearer demo_key_12345"
```

---

### Use Cases
- 🏢 Enterprise customer support automation
- 📨 High-volume email triage
- 🎯 Priority-based routing
- 📊 Support ticket classification
- 🔄 Multi-department coordination

---

## 🧪 Testing and Validation

### Run Validation Suite

```bash
python email_classifier.py
```

This will execute:
- Tests on 4 different scenarios (critical, low, billing, sales)
- Urgency and department accuracy validation
- Response time measurement
- Hot-reload configuration test
- Batch processing test

### Custom Test

```python
from email_classifier import EmailClassifier

classifier = EmailClassifier("config/classifier.yaml")
classifier.load_models()

result = classifier.classify_email({
    'subject': 'Your test',
    'testo_email': 'Your content',
    'sender': 'test@example.com'
})

print(f"Urgency: {result['urgency']}")
print(f"Department: {result['department']}")
print(f"Confidence: {result['overall_confidence']:.1%}")
```

---

## ⚠️ Known Limitations

**Transparency:**

This project was developed on **personal laptop hardware** with limited resources:

- Small pre-trained models (not fine-tuned on company-specific datasets)
- CPU-only inference (no GPU acceleration used during development)
- Limited training data for validation
- System optimized primarily for **English language** emails

**In an enterprise environment** with adequate resources:
- Accuracy could be significantly improved with fine-tuning on company data
- Response time could be reduced with dedicated GPUs
- Support for more advanced transformers (BERT large, GPT)
- Continuous learning on real company data
- Native multi-language support

---

## 🔮 Future Roadmap

### Technical Improvements
- [ ] Integration of more advanced Transformer models (BERT large, GPT-4)
- [ ] Multi-language support (Italian, Spanish, French, German)
- [ ] Fine-tuning on company-specific datasets
- [ ] Real-time learning from manual corrections
- [ ] Support for attachments and images in emails

### Integrations
- [ ] CRM: Salesforce, Zendesk, HubSpot, Freshdesk
- [ ] Notifications: Slack, Microsoft Teams, Discord
- [ ] Ticketing: Jira, Linear, Asana
- [ ] Email providers: Outlook, Office 365, Exchange

### Features
- [ ] Advanced analytics dashboard with charts
- [ ] Mobile app for priority management
- [ ] Feedback and manual correction system
- [ ] Custom report exports
- [ ] Webhooks for custom integrations

---

## 📚 Technical Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **AI/ML**: 
  - PyTorch 
  - Transformers (Hugging Face)
  - scikit-learn
- **Integration**: Gmail API, OAuth 2.0
- **Configuration**: YAML, Pydantic
- **API**: REST, JWT authentication
- **Monitoring**: Real-time metrics, health checks

---

## 📄 License

This project is developed as a **portfolio demonstration** of AI/ML capabilities and software engineering skills.

---

## 🎯 Demo Usage

### Suggested Live Demos

**1. API Demo via Swagger UI**
```bash
# Start the server
python api.py

# Open browser at:
http://localhost:8000/docs
```

**2. Single Email Classification Demo**
```bash
curl -X POST http://localhost:8000/classify \
  -H "Authorization: Bearer demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "URGENT: Main server down",
    "testo_email": "Our production database has not been responding for 30 minutes. Customers cannot place orders.",
    "sender": "ops@company.com"
  }'
```

**3. Health Check Demo**
```bash
curl http://localhost:8000/health
```

**4. Gmail Integration Demo** (if configured)
```bash
python gmail_classifier.py
# Will classify the last 10 emails and generate HTML report
```

## 📧 Contact

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

**[⬆ Back to top](#-ai-email-classification-system)**

</div>
