# REMEZ - Pharmaceutical Safety Analysis Platform

**License:** MIT | **Python:** 3.9+ | **React:** 18+

REMEZ is a comprehensive web platform for pharmaceutical safety analysis that enables researchers and healthcare professionals to identify and visualize adverse drug reaction signals using FDA Adverse Event Reporting System (FAERS) data.

## Research Attribution

This project builds upon a research by **Dr. Boris Gorelik**. The core statistical algorithm and FAERS data processing are adapted from his original work.

### Academic Foundation
- **Research Paper**: [*"The cardiovascular safety of antiobesity drugs-analysis of signals in the FDA Adverse Event Report System Database"*](https://www.nature.com/articles/s41366-020-0544-4) - Nature (2020)
- **Original Implementation**: [faers-analysis repository](https://github.com/bgbg/faers_analysis) by Dr. Boris Gorelik

### Data Sources
**FAERS Database**: [FDA Adverse Event Reporting System](https://data.nber.org/fda/faers/) via NBER. It includes quarterly data files: demographic, drug, reaction, and outcome data from FDA post-marketing surveillance

## Project Goals

- **Statistical Analysis**: Calculate Reporting Odds Ratios (ROR) to identify potential drug safety signals
- **Visualization**: Provide interactive charts and reports for analysis results
- **Scalability**: Handle large-scale FAERS data processing with efficient background job management
- **User Experience**: Offer an intuitive web interface for creating and managing safety analyses

## System Architecture

REMEZ consists of three main components working together:

```
                    ┌──────────────────────────┐
                    │     React Frontend       │
                    │  • User Interface        │
                    │  • Query Management      │
                    │  • Data Visualization    │
                    └─────────┬────────────────┘
                              ↕ HTTP
                    ┌─────────┴────────────────┐
                    │     Django Backend       │
                    │  • REST API Endpoints    │
                    │  • User Authentication   │
                    │  • Query Coordination    │
                    └─────┬───────────┬────────┘
                          ↕           ↕
                      HTTP│           │ psycopg2
         ┌────────────────┴───┐       │
         │  FastAPI Pipeline  │   ┌───┴─────────┐
         │  • FAERS Analysis  │   │ PostgreSQL  │
         │  • ROR Calculation │   │  Database   │
         │  • Background Jobs │   │             │
         └─────────┬──────────┘   └─────────────┘
                   ↕
         ┌─────────┴─────────┐
         │   FAERS Data      │
         │   Quarterly CSV   │
         └───────────────────┘
```

**Component Flow:**
1. **Frontend** → User creates analysis queries via React interface
2. **Backend** → Django API validates and stores queries
3. **Pipeline** → FastAPI service processes FAERS data and calculates statistics  
4. **Database** → PostgreSQL stores results and provides fast query access

## Project Structure

```
remez/
├── frontend/           # React web application
├── backend/           # Django REST API service  
├── pipeline/          # FastAPI data processing service
├── docs/              # Project documentation
├── docker-compose.yml # Container orchestration
└── README.md          # This file
```

## Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 16+** 
- **PostgreSQL** (or Supabase account)
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/LeahKorol/remez.git
cd remez
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
# Configure .env file and initialise the database
python manage.py migrate
python manage.py runserver
```

**[See Backend README](./backend/README.md) for detailed setup including database configuration and initialisation**

### 3. Pipeline Setup

```bash
cd pipeline  
pip install -r requirements.txt
# Configure .env file and download FAERS data files
python main.py
```

**[See Pipeline README](./pipeline/README.md) for FAERS data download instructions**

### 4. Frontend Setup

```bash
cd frontend
npm install
# Setup Google OAuth and configure .env file
npm start
```

**[See Frontend README](./frontend/README.md) for Google OAuth setup and component details**

## Component Documentation

Each component has detailed setup and usage documentation:

- **[Backend Documentation](./backend/README.md)** - Django REST API setup, authentication, database configuration
- **[Pipeline Documentation](./pipeline/README.md)** - FastAPI service setup, FAERS data processing, background jobs  
- **[Frontend Documentation](./frontend/README.md)** - React application setup, component overview, authentication flows

## Key Features

- **User Authentication**: JWT-based auth with Google OAuth integration
- **FAERS Data Management**: Automated download and processing of quarterly FAERS data
- **Statistical Analysis**: Calculate ROR values with confidence intervals
- **Interactive Visualization**: Dynamic charts with zoom, pan, and export capabilities
- **Background Processing**: Asynchronous analysis jobs with real-time status tracking
- **Result Management**: Persistent storage and retrieval of analysis results
- **Email Notifications**: Automated alerts when analyses complete

## Contributing

We welcome contributions to the REMEZ project! To contribute:

1. **Fork the repository** and create your feature branch from `main`
2. **Make your changes** with clear commit messages and tests
3. **Submit a pull request** with a detailed description

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines and [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for community standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
