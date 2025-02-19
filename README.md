# MailMate – Your Email Assistant

## Team Members
- Shubh Desai  
- Pushkar Kurhekar  
- Aalap Desai  
- Deep Prajapati  
- Shubham Mendapara  

## Introduction
In today’s fast-paced professional environment, email overload is a significant challenge, particularly after returning from a break or vacation. **MailMate** is designed to alleviate this burden by:
- Summarizing important messages to help users quickly catch up upon return.
- Suggesting draft replies for email threads.
- Identifying action items from email conversations.

This project leverages **Natural Language Processing (NLP)** to summarize email threads, generate draft replies, and extract action items. We plan to integrate this tool with at least one major email service via its API and deploy it as a **browser extension**.

---

## Dataset Information
### **Dataset: Enron Email Dataset**
- **Records:** ~500,000 emails  
- **Size:** 1.7GB  
- **Format:** Plain text files  
- **Fields:** Sender, Recipient, Subject, Body, Date  
- **Language:** English  
- **Usage:** Training and fine-tuning NLP models for summarization and draft reply generation  

### **Data Sources**
- **Enron Email Dataset**: [Link](https://www.cs.cmu.edu/~enron/)
- **Additional APIs**: Gmail API

### **Data Rights and Privacy**
- The **Enron Email Dataset** is publicly available for research.
- Real-world user data will be accessed **only via API** with explicit user consent.
- GDPR-compliant measures will be followed to ensure data privacy.

---

## Data Planning and Processing
1. **Loading Data**: Convert raw emails into structured format (CSV, SQL, NoSQL).
2. **Preprocessing**:
   - Remove email footers, disclaimers, signatures, and forward headers.
   - Normalize text (lowercasing, removing extra spaces, stripping HTML tags).
   - Extract metadata such as word count, sentiment, named entities.
3. **Splitting Data**:
   - **Train (70%)** – Model training.
   - **Validation (15%)** – Hyperparameter tuning.
   - **Test (15%)** – Model performance evaluation.

---

## GitHub Repository
🔗 **GitHub Link**: [https://github.com/pshkrh/mlops-project](https://github.com/pshkrh/mlops-project)

### **Folder Structure**
```
email-assistant/
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── notebooks/
│   ├── EDA.ipynb
│   ├── classification.ipynb
│   └── summarization.ipynb
├── src/
│   ├── data_preprocessing.py
│   ├── classification_model.py
│   ├── summarization_model.py
│   └── inference_api.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
│   ├── test_data_preprocessing.py
│   ├── test_classification_model.py
│   └── test_summarization_model.py
├── README.md
└── requirements.txt
```

---

## Project Scope
### **Problems**
- Users spend **significant time skimming** emails to find important information.
- Email threads often contain **hidden action items** that require manual identification.
- Writing replies for long email threads can be time-consuming.

### **Current Solutions & Limitations**
| **Current Solution** | **Limitations** |
|----------------------|----------------|
| **Manual Review** | Time-consuming, error-prone |
| **Microsoft Copilot for Outlook** | Works only for Outlook, lacks action item detection |
| **Gmail Auto-Complete** | Requires user input to generate suggestions, lacks contextual awareness |

### **Proposed Solution**
- **Summarize** email threads into concise bullet points.
- **Generate draft replies** using **LLM APIs** based on email thread context.
- **Identify action items** and pending tasks for the user.

---

## Metrics, Objectives, and Business Goals
### **Key Metrics**
- **Summarization Quality** – ROUGE-1, ROUGE-L (Target ROUGE-1: **0.7+**)
- **Action Item Extraction** – Precision/Recall/F1 Score (Target Precision: **80%**, Recall: **75%**)
- **User Satisfaction** – User feedback (Target **80%+** positive ratings)
- **Efficiency** – Processing time per email (Target **10-15 sec** per thread)

### **Business Goals**
✅ **Enhance User Productivity** – Automate summarization and reply generation.
✅ **Improve Email Management Efficiency** – Reduce time spent on email reviews.
✅ **Ensure Seamless Integration** – Integrate with major email providers (Gmail, Outlook).
✅ **Maintain Data Privacy & Security** – GDPR-compliant, user-controlled data access.

---

## Deployment Infrastructure
### **Key Components**
- **Browser Extension** – User interface for easy interaction.
- **API Backend (FastAPI/Flask)** – Handles email processing and NLP tasks.
- **Model Serving (GCP Vertex AI)** – Deploys and serves NLP models.
- **Cloud Storage (GCP)** – Securely stores metadata and summaries.
- **CI/CD Pipeline (GitHub Actions, Google Cloud Build)** – Automates deployment and testing.

### **Monitoring Plan**
| **Metric** | **Objective** |
|-----------|--------------|
| **API Response Time** | <15 seconds per request |
| **Error Rate** | <5% failures |
| **Summarization Accuracy** | ROUGE-1 > 0.7 |
| **User Feedback Acceptance** | >80% positive ratings |

---

## Success and Acceptance Criteria
| **Criteria** | **Threshold** |
|------------|--------------|
| **Summarization Accuracy** | ROUGE-1 ≥ 0.7 |
| **Action Item Extraction** | Precision & Recall ≥ 70% |
| **Processing Efficiency** | 10-15 sec per thread |
| **Integration** | Works with at least one email provider (Gmail/Outlook) |
| **Reliability** | No major crashes/errors, 80%+ positive user feedback |

---

## Timeline Planning
| **Phase** | **Duration** |
|----------|------------|
| **Week 1-3** | Data acquisition, EDA, cleaning, preprocessing |
| **Week 4-6** | Model training (summarization, classification, action item extraction) |
| **Week 7-9** | Backend integration, API setup, UI development |
| **Week 10+** | Final testing, deployment, and demo preparation |

---

## How to Run the Project
### **1. Clone the Repository**
```bash
git clone https://github.com/pshkrh/mlops-project.git
cd mlops-project
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Run the API Server**
```bash
python src/inference_api.py
```

### **4. Test the Setup**
```bash
pytest tests/
```

### **5. Run the Browser Extension (Development Mode)**
- Load the `browser-extension/` directory as an unpacked extension in Chrome.

---

## Contributing
1. **Fork the repo** and clone it locally.
2. Create a **new feature branch**.
3. Make changes and **commit with clear messages**.
4. Push to **your fork** and open a **pull request**.

---

## License
This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Contact
For questions or collaboration, contact any team member or open an issue in GitHub.

