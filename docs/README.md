# REMEZ - Documentation

This directory contains documentation files for the REMEZ project, including UML diagrams.

## UML Diagrams

### Component Diagram

The main component diagram is available in:
- `REMEZ_Component_Diagram.puml` - Original version

### Deployment Diagram

The deployment diagram shows the infrastructure and runtime environment:
- **`REMEZ_Deployment_Diagram.puml`** - Shows servers, databases, and network connections

## How to View the Diagrams

### Online (Recommended)

1. Go to: https://www.plantuml.com/plantuml/uml/
2. Copy the contents of `REMEZ_Component_Diagram_FINAL.puml`
3. Paste into the text editor
4. Wait for the diagram to render
5. Click download button to save as PNG

### Alternative Website

- https://www.planttext.com/ (same process)

## Project Structure

```
REMEZ Project
├── backend/          # Django REST API
├── frontend/         # React Application  
├── pipeline/         # FastAPI Data Processing
└── docs/            # Documentation (you are here)
    └── *.puml       # UML diagrams
```

## Diagram Contents

### Component Diagram
Shows the logical architecture:
- **Frontend Server** (Port 3000) - React application
- **Backend Server** (Port 8000) - Django application
- **Pipeline Server** (Port 8001) - FastAPI application
- **Databases** - PostgreSQL (Supabase) and SQLite
- **External Services** - Google OAuth, SMTP, FAERS data

### Deployment Diagram
Shows the physical infrastructure:
- **Port Mappings** - :3000, :8000, :8001
- **Cloud Services** - Supabase PostgreSQL
- **Local Storage** - SQLite and File System
- **Artifacts** - Deployment files and executables

## Future Diagrams

Potential diagrams to add:
- [x] Component Diagrams (logical architecture) ✅
- [x] Deployment Diagrams (infrastructure) ✅
- [ ] Class Diagrams (detailed models)
- [ ] Sequence Diagrams (interaction flows)
- [ ] Activity Diagrams (business processes)
- [ ] State Diagrams (state transitions)

## Tools

### Required
- PlantUML syntax editor

### Recommended
- [PlantUML Online](https://www.plantuml.com/plantuml/uml/)
- [PlantText](https://www.planttext.com/)

## Notes

- All UML diagrams use PlantUML format (`.puml`)
- Diagrams are optimized for standard screen widths
- Recommended: Use `REMEZ_Component_Diagram_FINAL.puml` for best results

