# Fitpulse-health-
 FitPulse is a Flask-based health monitoring app that lets users register, log in, enter daily health data, and view trends through a clean dark-themed dashboard. It includes SQL database support, data visualization, and simple UI pages for easy tracking and analysis.
FitPulse – Health Anomaly Detection
Python • Flask • MIT License
FitPulse is a web-based health monitoring application designed to track vital signs, visualize health trends, and automatically detect anomalies. Built as an Infosys project, it provides users with actionable insights into heart rate, daily activity, and sleep patterns.
📖 Table of Contents
.Features
.Tech Stack
.Project Structure
.Dataset
.Installation
.Usage
.License
✨ Features
User Authentication
Secure registration & login system with password hashing.
Data Entry
Simple forms to log Heart Rate, Steps, and Sleep duration.
Automated Anomaly Detection
Calculates health status → Healthy / Warning / Critical
Visual alerts for abnormal heart rate or sleep deprivation.
Interactive Dashboard
Real-time visualization using HTML5 Canvas
Clickable table rows that highlight corresponding graph points.
Data Export
One-click CSV export of all health records.
Responsive Design
Modern dark-themed UI for mobile & desktop.
🛠 Tech Stack
Backend
Python 3.x
Flask (Web Framework)
Frontend
HTML5, CSS3, JavaScript
HTML5 Canvas API
Jinja2 Templates
📁 Project Structure

FitPulse/
│
├── app.py                # Main Flask application logic
├── database.sql          # Database schema
├── health_dataset.csv    # Sample dataset
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
│
├── static/
│   └── style.css         # Dark theme styling
│
└── templates/
    ├── welcome.html
    ├── login.html
    ├── register.html
    ├── home.html
    ├── dashboard.html
    ├── data_entry.html
    └── profile.html
📊 Dataset
File: health_dataset.csv
Contains sample health log entries.
Column
Description
Date
Timestamp of the entry
Heart_Rate
Heart rate in bpm
Steps
Daily step count
Sleep
Hours of sleep
Status
Healthy / Warning / Critical
Can be viewed in Excel, Google Sheets, or any text editor.
⚙️ Installation
1. Clone the Repository
Bash
git clone https://github.com/yourusername/fitpulse.git
cd fitpulse
2. (Optional) Create Virtual Environment
Windows
Bash
python -m venv venv
venv\Scripts\activate
Mac/Linux
Bash
source venv/bin/activate
3. Install Dependencies
Your requirements.txt should contain:

Flask
mysql-connector-python
werkzeug
Install using:
Bash
pip install -r requirements.txt
4. Database Setup
Create a MySQL database
Run database.sql
Configure DB credentials inside app.py
5. Run the Application
Bash
python app.py
Open in browser:
👉 http://127.0.0.1:5000⁠�
🚀 Usage
Register: Create your account
Login: Access your dashboard
Add Data: Log your daily health metrics
Analyze:
View averages
See trends in the visual graphs
Click table rows to highlight graph points
Export: Download full CSV dataset
📄 License
This project is licensed under the MIT License.
Developed with ❤️ for the Infosys Project.
