# 🎯 FreshLense - Intelligent Web Content Monitoring & Fact-Checking System

![FreshLense Logo](https://img.shields.io/badge/FreshLense-Web%20Monitoring-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb)
![License](https://img.shields.io/badge/License-MIT-green)

A sophisticated web content monitoring platform that automatically tracks changes, fact-checks technical content, and provides intelligent version comparison for blogs, documentation, and information websites.

## ✨ Features

### 🔍 **Smart Fact-Checking**
- **AI-Powered Verification**: Automatically verifies technical claims using OpenAI and SERP API
- **Multi-Type Analysis**: Supports version info, performance claims, security assertions, and compatibility statements
- **Confidence Scoring**: Each verification includes a confidence percentage and detailed explanation

### 📊 **Version Comparison**
- **Change Detection**: Track modifications between different versions of web pages
- **Enhanced Diff Viewer**: Side-by-side comparison with syntax highlighting
- **Change Metrics**: Words added/removed, similarity scores, and detailed change summaries

### 🔄 **Content Monitoring**
- **Automatic Crawling**: Scheduled monitoring of tracked websites
- **Version History**: Complete archive of all content versions
- **Change Alerts**: Email notifications via Resend when content changes

### 🛡️ **Security & Management**
- **Email-Based MFA**: Secure authentication with multi-factor verification
- **Dashboard**: Centralized management of all monitored pages
- **Direct Input**: Manual content analysis for non-crawlable pages

### 📱 **User Experience**
- **Modern UI**: Beautiful React interface with Tailwind CSS
- **Real-time Updates**: Live notifications and status updates
- **Responsive Design**: Works seamlessly on desktop and mobile

## 🏗️ Architecture
FreshLense/
├── 📁 backend/ # FastAPI Backend
│ ├── app/
│ │ ├── routers/ # API Endpoints
│ │ ├── schemas/ # Pydantic Models
│ │ ├── services/ # Business Logic
│ │ └── utils/ # Utilities
│ ├── database.py # MongoDB Connection
│ ├── main.py # FastAPI Application
│ └── requirements.txt # Python Dependencies
├── 📁 frontend/ # React Frontend
│ ├── src/
│ │ ├── components/ # Reusable Components
│ │ ├── pages/ # Page Components
│ │ ├── services/ # API Services
│ │ ├── types/ # TypeScript Definitions
│ │ └── contexts/ # React Contexts
│ ├── public/ # Static Assets
│ └── package.json # Node.js Dependencies
├── 📁 chrome_extension/ # Browser Extension
├── 📄 README.md # This File


## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- API Keys (OpenAI, SERP API, Resend)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/freshlense.git
cd freshlense/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000


##Frontend Setup

bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your backend URL

# Start development server
npm start


##Backend (.env)
# ========= DATABASE =========
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=freshlense

# ========= JWT AUTHENTICATION =========
SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ========= FRONTEND URLS =========
FRONTEND_URL=http://localhost:3000

# ========= EXTERNAL APIS =========
SERPAPI_API_KEY=your-serpapi-api-key-here

# ========= EMAIL SERVICE (RESEND) =========
RESEND_API_KEY=re_your-resend-api-key-here
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_ENABLED=true

# ========= APPLICATION SETTINGS =========
APP_NAME=FreshLense
ENVIRONMENT=development
DEBUG=true

# ========= SECURITY SETTINGS =========
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000


##Frontend (.env.local)
# ========= API CONFIGURATION =========
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development


##📚 API Documentation
Once the backend is running, access the interactive API documentation:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Key Endpoints
Method	Endpoint	Description
POST	/api/auth/register	User registration
POST	/api/auth/login	User login
POST	/api/auth/verify-mfa	MFA verification
GET	/api/fact-check/pages	Get tracked pages
POST	/api/fact-check/check	Fact-check content
POST	/api/fact-check/compare	Compare versions
GET	/api/fact-check/pages/{id}/versions	Get page versions


##🤖 How It Works

##1. Content Crawling
a.Scheduler automatically fetches content from tracked URLs
b.Stores HTML and text versions in MongoDB
c.Detects changes between versions

##2. Fact-Checking Pipeline
a. Extract claims from content
b. Categorize claims (version, performance, security, etc.)
c. Query external APIs for verification
d. Analyze results and assign confidence scores
e. Generate detailed explanations

##3. Change Detection
a.Uses advanced diff algorithms to compare versions
b.Highlights additions, deletions, and modifications
c.Calculates similarity metrics and change summaries

##4. Notification System
a.Sends email alerts via Resend when content changes
b.Includes fact-check results and change summaries
c.Configurable notification preferences


##🔍 Use Cases
##🔧 Technical Documentation
Monitor API documentation for breaking changes
Verify version compatibility claims
Track library/framework updates

##📝 Blogs & Articles
Fact-check technical tutorials
Monitor editorial changes
Detect misinformation

##🏢 Corporate Websites
Track policy/document updates
Monitor press releases
Ensure regulatory compliance

##🎓 Educational Content
Verify course material accuracy
Track syllabus updates
Monitor research publications

