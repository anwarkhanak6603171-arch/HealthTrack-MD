# HealthTrack MD | Doctor Portal

A secure, high-performance clinical dashboard for healthcare providers. This portal allows doctors to manage patient records, track diagnostics like BMI, and maintain medical notes with a modern, glassmorphism interface.

## 🚀 Features
- **Secure Authentication**: Doctor-specific accounts using JWT tokens and bcrypt password hashing.
- **Patient Management**: Full CRUD (Create, Read, Update, Delete) operations for patient files.
- **Clinical Analytics**: Automatic BMI calculation and health status verdict.
- **Modern UI**: Fully responsive design with glassmorphism aesthetics and smooth transitions.
- **Search & Sort**: Quickly find patients by name, ID, or city, and sort by various metrics.

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Vanilla JavaScript, CSS3 (Glassmorphism), HTML5
- **Deployment**: Optimized for Render/GitHub

## 📦 Installation & Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/healthtrack-md.git
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```

## 🌐 Deployment
This project is ready for deployment on **Render**.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---
*Created for clinical efficiency and data isolation.*
