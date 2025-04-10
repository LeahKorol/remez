# REMEZ

**REMEZ** is a web application designed to identify and visualize risk signals for pharmaceutical drugs using data-driven analysis.  
It provides valuable insights by analyzing post-marketing surveillance data (FAERS).

This project reimplements the logic from faers-analysis by Dr. Boris Gorelik.
It adapts the original CSV-based computations into a scalable, queryable database-backed approach.

## Technology Stack
- **Frontend**: REACT, JavaScript, CSS
- **Backend**: Django (Python)
- **Database**: Supabase (PostgreSQL)
- **Data Source**: FDA Adverse Event Reporting System (FAERS)

## Key Features
- Import and normalize FAERS CSV data into a relational database
- Perform risk signal calculations using efficient SQL queries
- Avoid redundant work by indexing and linking entities (drugs, reactions)
- Explore results through a web-based UI
