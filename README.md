# REMEZ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**REMEZ** is a web application designed to identify and visualize risk signals for pharmaceutical drugs using data-driven analysis.  
It provides valuable insights by analyzing post-marketing surveillance data from the FDA Adverse Event Reporting System (FAERS).

This project reimplements the logic from [faers-analysis](https://github.com/Boris-Gorelik/faers-analysis) by Dr. Boris Gorelik, adapting the original CSV-based computations into a scalable, queryable database-backed approach.

---

## 🏗️ Architecture

**Stack:**
- Frontend: React, JavaScript, CSS  
- Backend: Django (Python)  
- Database: Supabase (PostgreSQL)  
- Data Source: FDA Adverse Event Reporting System (FAERS)  

---

## ✨ Key Features
- Import and normalize FAERS CSV data into a relational database  
- Perform risk signal calculations using efficient SQL queries  
- Avoid redundant work by indexing and linking entities (drugs, reactions)  
- Explore results through a web-based UI  

---

## 🚀 Installation

```bash
# Clone the repo
git clone https://github.com/LeahKorol/remez.git
cd remez

# Backend setup
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend setup
cd frontend
npm install
npm start
