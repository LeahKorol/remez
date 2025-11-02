# REMEZ - Documentation

This directory contains documentation files for the REMEZ project, including UML diagrams.

## UML Diagrams

### Component Diagram
The main component diagram shows the logical architecture:
- `REMEZ_Component_Diagram.puml` - Original version
- `REMEZ_Component_Diagram_FINAL.puml` - Final optimized version

### Deployment Diagram
The deployment diagram shows the infrastructure and runtime environment:
- `REMEZ_Deployment_Diagram.puml` - Shows servers, databases, and network connections

### Use Case Diagram
The use case diagram shows system functionality from user perspective:
- `REMEZ_Use_Case_Diagram.puml` - Shows actors, use cases, and relationships

### Sequence Diagrams
The sequence diagrams show interaction flows between components:
- `REMEZ_Sequence_Diagram_Part1.mmd` - User Login, Query Creation & Pipeline Processing
- `REMEZ_Sequence_Diagram_Part2.mmd` - Results Display, Query Management & Error Handling

## How to View the Diagrams

### PlantUML Diagrams (`.puml` files)

#### Online (Recommended)
1. Go to: https://www.plantuml.com/plantuml/uml/
2. Copy the contents of any `.puml` file
3. Paste into the text editor
4. Wait for the diagram to render
5. Click download button to save as PNG

#### Alternative Website
- https://www.planttext.com/ (same process)

#### VS Code / IntelliJ / PyCharm
1. Install the PlantUML extension/plugin
2. Open the `.puml` file
3. Use preview command to view
4. Export as needed

### Mermaid Diagrams (`.mermaid` files)

#### Online (Recommended)
1. Go to: https://mermaid.live/
2. Copy the contents of any `.mermaid` file
3. Paste into the code editor
4. View live preview
5. Export as PNG/SVG

#### VS Code
1. Install "Mermaid Preview" extension
2. Open the `.mermaid` file
3. Use preview command to view

#### GitHub/GitLab
- `.mermaid` files render automatically in markdown files
- Can be embedded directly in README.md

## Project Structure

```
REMEZ Project
├── backend/          # Django REST API
├── frontend/         # React Application  
├── pipeline/         # FastAPI Data Processing
└── docs/            # Documentation (you are here)
    ├── *.puml       # PlantUML diagrams
    └── *.mermaid        # Mermaid diagrams
```

## Diagram Contents

### Component Diagram (PlantUML)
Shows the logical architecture:
- **Frontend Server** (Port 3000) - React application
- **Backend Server** (Port 8000) - Django application
- **Pipeline Server** (Port 8001) - FastAPI application
- **Databases** - PostgreSQL (Supabase) and SQLite
- **External Services** - Google OAuth, SMTP, FAERS data

### Deployment Diagram (PlantUML)
Shows the physical infrastructure:
- **Port Mappings** - :3000, :8000, :8001
- **Cloud Services** - Supabase PostgreSQL
- **Local Storage** - SQLite and File System
- **Artifacts** - Deployment files and executables

### Use Case Diagram (PlantUML)
Shows system functionality:
- **Actors** - Visitor, Registered User
- **Authentication** - Register, Login, Reset Password
- **Analysis Workflow** - Search, Query Management, Results
- **External Systems** - Google OAuth, Email Service, Pipeline Service

### Sequence Diagrams (Mermaid)
Shows interaction flows:

#### Part 1 - Core Workflows
- User Login & Profile Access
- Query Creation Flow (with drug/reaction search)
- Pipeline Processing Flow
- Background Pipeline Execution
- Real-time Status Polling

#### Part 2 - Management & Error Handling
- Results Display Flow
- Query Management Flow (view, edit, delete)
- Query Editing Flow
- Query Deletion Flow
- Error Handling Flow
- Session Management Flow

## File Format Guide

| Format | Extension | Best For | Tools |
|--------|-----------|----------|-------|
| PlantUML | `.puml` | Component, Deployment, Use Case, Class diagrams | plantuml.com, VS Code |
| Mermaid | `.mermaid` | Sequence, Flowcharts, State diagrams | mermaid.live, GitHub |

## Diagram Status

- [x] Component Diagram (logical architecture) 
- [x] Deployment Diagram (infrastructure) 
- [x] Use Case Diagram (system functionality) 
- [x] Sequence Diagrams (interaction flows) 
- [x] Class Diagrams (detailed models)
- [x] Activity Diagrams (business processes)
- [x] State Diagrams (state transitions)
- [x] ER Diagram (database schema)

## Tools & Resources

### PlantUML Tools
- [PlantUML Online](https://www.plantuml.com/plantuml/uml/) - Web editor
- [PlantText](https://www.planttext.com/) - Alternative web editor
- [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml) - Local editing

### Mermaid Tools
- [Mermaid Live Editor](https://mermaid.live/) - Web editor
- [Mermaid Documentation](https://mermaid.js.org/) - Official docs
- [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) - Preview in markdown

## Tips

### PlantUML
- Use `!theme plain` for clean diagrams
- Optimize for standard screen widths (800-1200px)
- Use stereotypes for better categorization
- Group related components in packages

### Mermaid
- Use `%%{init: {...}}%%` for custom themes
- Add `rect` blocks for visual grouping
- Use notes for additional context
- Keep sequence diagrams focused (split if needed)

## Contributing

When adding new diagrams:
1. Use descriptive filenames with `REMEZ_` prefix
2. Follow existing naming conventions
3. Add diagram description to this README
4. Test rendering in online tools before committing
5. Update the "Diagram Status" checklist

## Notes

- All diagrams are version-controlled in this repository
- Diagrams are optimized for documentation and presentations
- For Component Diagram: Use `REMEZ_Component_Diagram_FINAL.puml` for best results
- For Sequence Diagrams: Both parts together show the complete application flow
- Mermaid diagrams render automatically in GitHub/GitLab markdown files

## Version History

- **v1.0** - Initial Component and Deployment diagrams (PlantUML)
- **v1.1** - Added Use Case diagram (PlantUML)
- **v1.2** - Added Sequence diagrams Part 1 & 2 (Mermaid)

---

For questions or issues with diagrams, please open an issue in the project repository.