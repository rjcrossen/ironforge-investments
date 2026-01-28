## Relevant Files

- `docs/code/architecture.md` - Main documentation file to be created/updated with architectural diagrams
- `src/models/models.py` - Contains database models that need to be documented
- `src/scraper/auction_collector.py` - Auction data collection logic
- `src/scraper/scraper.py` - Main scraper service
- `src/repository/auction_repository_eu.py` - EU auction repository
- `src/repository/auction_repository_us.py` - US auction repository
- `src/repository/recipe_repository.py` - Recipe repository
- `src/repository/reagent_repository.py` - Reagent repository
- `src/seeding/recipes.py` - Recipe seeding logic
- `src/seeding/reagents.py` - Reagent seeding logic

### Notes

- All diagrams should use Mermaid syntax for version control and rendering in GitHub
- Ensure diagrams are kept up-to-date with code changes
- Test diagram rendering by viewing the markdown file in GitHub

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:

- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [x] 0.0 Use existing branch (already on `tests` branch)
- [x] 1.0 Commit or stash current changes
  - [x] 1.1 Check git status for uncommitted changes
  - [x] 1.2 Commit current changes to the `tests` branch or stash them
- [x] 2.0 Analyze codebase structure and components
  - [x] 2.1 Read src/models/models.py to understand database models
  - [x] 2.2 Read src/scraper/auction_collector.py to understand auction collection
  - [x] 2.3 Read src/scraper/scraper.py to understand main scraper service
  - [x] 2.4 Read repository files (auction_repository_eu.py, auction_repository_us.py, recipe_repository.py, reagent_repository.py)
  - [x] 2.5 Read seeding files (recipes.py, reagents.py) to understand seeding logic
  - [x] 2.6 Read src/main.py to understand service orchestration
  - [x] 2.7 Document key components and their relationships
- [x] 3.0 Create high-level system architecture diagram
  - [x] 3.1 Create Mermaid flowchart showing Scheduler Service, PostgreSQL, and API Service
  - [x] 3.2 Add connections between services
  - [x] 3.3 Add notes explaining each service's role
  - [x] 3.4 Add the diagram to docs/code/architecture.md
- [x] 4.0 Create data flow diagram
  - [x] 4.1 Create Mermaid diagram showing Blizzard API → Scraper → Database flow
  - [x] 4.2 Include data transformation steps
  - [x] 4.3 Show EU and US region data paths
  - [x] 4.4 Add the diagram to docs/code/architecture.md
- [x] 5.0 Create component interaction diagrams
  - [x] 5.1 Create diagram showing Scraper → Collector → Repository → Models flow
  - [x] 5.2 Create diagram showing Seeder → API Client → Repository flow
  - [x] 5.3 Add error handling paths to diagrams
  - [x] 5.4 Add the diagrams to docs/code/architecture.md
- [x] 6.0 Create data model overview diagram
  - [x] 6.1 Create Mermaid entity-relationship diagram for auction tables
  - [x] 6.2 Create diagram for recipe/reagent/item tables
  - [x] 6.3 Show table relationships and foreign keys
  - [x] 6.4 Add the diagrams to docs/code/architecture.md
- [x] 7.0 Create sequence diagrams for critical operations
  - [x] 7.1 Create sequence diagram for auction data collection
  - [x] 7.2 Create sequence diagram for recipe seeding process
  - [x] 7.3 Create sequence diagram for reagent seeding process
  - [x] 7.4 Include error handling in sequence diagrams
  - [x] 7.5 Add the diagrams to docs/code/architecture.md
- [x] 8.0 Add component inventory and documentation structure
  - [x] 8.1 Create table of contents for architecture.md
  - [x] 8.2 Write component inventory with descriptions
  - [x] 8.3 Add links to source files for each component
  - [x] 8.4 Add section explaining PostgreSQL partitioning strategy
  - [x] 8.5 Organize content with clear headings
- [x] 9.0 Review and validate diagrams
  - [x] 9.1 Verify all Mermaid diagrams render correctly in GitHub
  - [x] 9.2 Check for consistency with actual codebase
  - [x] 9.3 Review with ruff formatter
  - [x] 9.4 Run basedpyright to check for any issues
  - [x] 9.5 Commit all changes to the tests branch