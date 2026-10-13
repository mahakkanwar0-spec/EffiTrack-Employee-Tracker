# EffiTrack – AI-Powered Employee Performance Analytics

EffiTrack is an AI-powered employee performance analytics system that helps understand employee performance, work patterns, and well-being.

## 🚀 Features

- **Employee Data Upload:** Upload employee data through the Upload button to process and analyze it.
- **Burnout Risk Prediction:** Helps identify employees who may be at risk of burnout.
- **Performance Prediction:** Predicts employee performance scores using machine learning.
- **Work Personality Classification:** Classifies employee work styles based on the available data.
- **AI-Generated Insights:** Uses Google's Gemini API to convert analytical results into easy-to-understand summaries.
- **Interactive Dashboard:** Displays employee analytics in a visually engaging, Spotify Wrapped-inspired format.
- **Secure Backend:** Uses FastAPI, MongoDB, and JWT authentication for API access and data management.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend API development |
| MongoDB | Employee data storage |
| Streamlit | Interactive dashboard |
| Scikit-learn | Machine learning |
| Google Gemini API | AI-generated summaries and insights |
| JWT | Authentication and API security |

## ⚙️ How It Works

1. **Upload Data:** The user uploads employee data using the Upload button.
2. **Process Data:** The backend processes the uploaded information.
3. **Analyze Performance:** Machine learning models generate predictions and insights based on the available employee data.
4. **Generate Summary:** Gemini AI converts analytical results into understandable text.
5. **View Dashboard:** The dashboard presents performance analytics, predictions, and summaries.

## 🏗️ System Architecture

**Streamlit Dashboard → FastAPI Backend → MongoDB + Machine Learning Models → Gemini AI Insights → Dashboard Results**

## 💡 Why EffiTrack?

Traditional employee performance reviews can require considerable manual effort. EffiTrack aims to simplify this process by bringing employee data, machine learning predictions, and AI-generated insights together in one dashboard.

## 🔐 Security and Data Privacy

- JWT-based authentication for protected API access.
- Environment variables for sensitive configuration and API keys.
- Employee data should be handled carefully and should not be exposed in the public repository.

## ▶️ Getting Started

### Prerequisites

- Python 3.10 or later
- MongoDB or a MongoDB Atlas connection
- Google Gemini API key
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/mahakkanwar0-spec/EffiTrack-Employee-Tracker
   cd EffiTrack
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   ```

   On Windows:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the required environment variables in your `.env` file, following the variable names expected by the project.

5. Start the FastAPI backend using the entry point configured in your repository. For example:

   ```bash
   uvicorn main:app --reload
   ```

6. Start the Streamlit dashboard using the appropriate frontend file. For example:

   ```bash
   streamlit run app.py
   ```


## 🔮 Future Improvements

- Improve prediction accuracy through further model evaluation.
- Add more employee analytics and visualizations.
- Improve explainability of machine learning predictions.
- Enhance data privacy and access controls.

## 👩‍💻 Project Goal

EffiTrack combines machine learning, backend APIs, database management, and generative AI to make employee performance analytics more accessible and easier to understand.
