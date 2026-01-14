# LoanGuard AI

**AI-Powered Syndicated Loan Management & ESG Compliance Platform**

---

## 🎯 What It Does

LoanGuard AI transforms how banks manage syndicated loans by combining **real-time covenant monitoring**, **ML-powered risk prediction**, and **automated ESG compliance** into a single platform.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Covenant Monitoring** | Tracks 26+ loans with real-time breach detection |
| **ML Breach Prediction** | 72.99% AUC using LightGBM trained on 720K+ loans |
| **ESG Compliance** | Tracks KPIs, SPTs, and carbon emissions (Climatiq API) |
| **Greenwashing Detection** | Real-time claim verification using Google Search API |
| **Document Parsing** | Affinda AI extracts covenants from loan agreements (99%+ accuracy) |
| **Risk Committee AI** | 5-agent debate system for loan decisions (EU AI Act compliant) |
| **Voice Alerts** | ElevenLabs AI calls Risk Committee for urgent breaches |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React, Tailwind CSS |
| **Backend** | Python, FastAPI, Google Cloud Run |
| **Database** | Google BigQuery (16 tables) |
| **AI/ML** | Gemini 2.0, LightGBM, XGBoost, SHAP |
| **Document AI** | Affinda REST API |
| **External APIs** | FRED (macro data), Climatiq (carbon), SendGrid (email), ElevenLabs (voice) |

---

## 📊 Data & Models

| Model | Training Data | Performance |
|-------|---------------|-------------|
| Breach Predictor | 720,966 Lending Club loans | AUC: 0.7299 |
| LGD Predictor | 148K charged-off loans | MAE: 6.45% |
| Prepayment Risk | 200K fully paid loans | AUC: 0.7809 |
| ESG Risk Scorer | 11K companies | Accuracy: 97.05% |

---

## 🚀 Live Demo

- **Frontend**: [Deployed on Vercel]
- **Backend**: `https://loanguard-api-403714473978.us-central1.run.app`

---

## 📁 Project Structure

```
lma/
├── api_gateway/          # FastAPI backend (main entry point)
├── frontend/             # Next.js React application
├── models/               # Trained ML models (.pkl files)
├── common/               # Shared utilities (BigQuery client, parsers)
├── risk_committee/       # 5-agent AI debate system
├── esg_service/          # ESG compliance tools
└── sample_documents/     # Test loan agreements
```

---

## 🏆 LMA Edge Hackathon Categories

This project addresses multiple hackathon categories:

- ✅ **Digital Loans** - AI-powered loan portfolio management
- ✅ **Keeping Loans on Track** - Real-time covenant monitoring & breach prediction
- ✅ **Greener Lending** - ESG compliance, carbon tracking, SLL monitoring

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file
