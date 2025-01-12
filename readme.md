# WhatsApp Chat Analyzer

## Description
WhatsApp Chat Analyzer is a web-based application designed to analyze exported WhatsApp chat data. It provides insightful metrics, visualizations, and patterns for users or groups, enabling deeper understanding of conversations.

### Key Features:
- **User Authentication**: Secure login and signup with email verification and password reset options.
- **Chat Analysis**: Upload WhatsApp chat files to generate metrics like total messages, active users, word count, media shared, etc.
- **Visualization**: Interactive charts and graphs using Plotly and Matplotlib.
- **Profile Management**: Update username, email, password, and profile photo.
- **Data Management**: Save and manage datasets for analysis.

---

## Table of Contents
1. [Installation](#installation)
2. [Setup](#setup)
3. [Run Instructions](#run-instructions)
4. [Project Output](#project-output)
5. [Tech Stack](#tech-stack)

---

## Installation

### Prerequisites
- Python 3.9 or above installed.
- [SQLite](https://www.sqlite.org/index.html) for the local database.
- Cloudinary account for storing profile photos.
- Email server credentials for sending OTPs and welcome emails.

### Steps
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd whatsapp-chat-analyzer
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up a `.env` file with the following:
   ```plaintext
   CLOUDINARY_CLOUD_NAME=<Your Cloudinary Cloud Name>
   CLOUDINARY_API_KEY=<Your Cloudinary API Key>
   CLOUDINARY_API_SECRET=<Your Cloudinary API Secret>

   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=<Your Email>
   SMTP_PASSWORD=<Your Email Password>
   ```

---

## Setup

1. Initialize the database:
   - The application will automatically create the necessary tables when run for the first time.

2. Optional: Populate initial data for testing using SQLite:
   ```bash
   sqlite3 app_data.db
   ```

3. Configure Streamlit for wide-mode display (recommended for better visualization).

---

## Run Instructions

1. Launch the application:
   ```bash
   streamlit run app.py
   ```
2. Open the provided URL (e.g., `http://localhost:8501`) in your browser.

---

## Project Output

### Login Page:
![Screenshot 2025-01-12 125109](https://github.com/user-attachments/assets/36ecd6e3-e46a-4105-bec5-7858d1db8beb)


### Dashboard:
![Dashboard Example](link_to_dashboard_image)

### Chat Analysis:
![Chat Analysis Example](link_to_analysis_image)

### Profile Settings:
![Profile Settings Example](link_to_profile_settings_image)

---

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite
- **Visualization**: Plotly, Matplotlib
- **Hosting Images**: Cloudinary
- **Authentication**: Email-based OTP and password hashing (bcrypt)

---
