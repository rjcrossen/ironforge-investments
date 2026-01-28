# Product Requirements Document: Architectural Diagrams and Codebase Understanding

## Introduction/Overview

This document outlines the requirements for creating comprehensive architectural diagrams and codebase understanding documentation in `/docs/code/architecture.md`. The goal is to provide clear visual representations of the system architecture, data flows, and component interactions to support ongoing maintenance and development of the Ironforge Investments platform.

## Goals

1. Create clear, visual architectural diagrams using Mermaid markdown syntax
2. Document data flow through the system from API collection to database storage
3. Explain component interactions and dependencies
4. Provide reference documentation for maintenance tasks
5. Ensure diagrams are version-controlled and easy to update

## User Stories

**As a** developer maintaining the codebase  
**I want** to understand the system architecture through visual diagrams  
**So that** I can quickly identify where changes need to be made and understand the impact of modifications

**As a** developer investigating data flow issues  
**I want** to see how data moves from the Blizzard API through to the database  
**So that** I can trace and debug data collection problems

**As a** developer onboarding to the project  
**I want** clear documentation of component interactions  
**So that** I can understand how the scraper, repositories, and models work together

## Functional Requirements

1. **The documentation must include a high-level system architecture diagram** showing the main services (Scheduler, PostgreSQL, API Service) and their relationships

2. **The documentation must include a data flow diagram** illustrating the journey of auction data from Blizzard API through processing to database storage

3. **The documentation must include component interaction diagrams** showing how the scraper, collectors, repositories, and models interact

4. **All diagrams must use Mermaid markdown syntax** to ensure they render in GitHub/GitLab and can be version controlled

5. **The documentation must include a component inventory** listing all major components with brief descriptions of their responsibilities

6. **The documentation must include a data model overview** showing key entities and their relationships

7. **The documentation must include sequence diagrams** for critical operations like auction data collection and recipe seeding

8. **The documentation must be organized with clear sections** and table of contents for easy navigation

## Non-Goals (Out of Scope)

- Detailed API endpoint documentation (covered elsewhere)
- Deployment architecture diagrams (Docker/Kubernetes specifics)
- Security architecture documentation
- Performance optimization guides
- User-facing documentation or tutorials

## Design Considerations

- Use Mermaid flowchart syntax for system architecture
- Use Mermaid sequence diagrams for interaction flows
- Use Mermaid entity-relationship diagrams for data models
- Include both high-level overviews and detailed component views
- Use consistent naming conventions matching the codebase
- Include links to relevant source files where applicable

## Technical Considerations

- All diagrams must be valid Mermaid syntax
- Diagrams should be embedded directly in the markdown file
- Use subgraphs to organize complex diagrams logically
- Include comments in Mermaid code for maintainability
- Consider diagram readability at different zoom levels

## Success Metrics

1. New developers can understand the system architecture within 30 minutes of reading the documentation
2. All major components (scraper, repositories, models) are documented with diagrams
3. Data flow from API to database is clearly visualized
4. Documentation is kept up-to-date with code changes
5. Diagrams render correctly in GitHub's markdown viewer

## Open Questions - Now Closed

1. Should we include error handling flows in the sequence diagrams? - Yes
2. Are there specific edge cases or complex interactions that need special attention? - No
3. Should we document the partitioning strategy for the PostgreSQL database? - Yes
