# PaveLedger architecture diagrams

## Implemented request boundary

```mermaid
flowchart TD
    UI[Phone or desktop browser] --> Auth[Supabase Auth]
    UI --> API[Next.js server API]
    API --> Check[Verified UUID and active membership]
    Check --> Scope[Role and case scope checks]
    Scope --> DB[PostgreSQL workspace and revision]
    Scope --> Files[Private evidence bucket]
    DB --> View[Filtered response]
    View --> UI
    Files --> Link[60-second signed evidence URL]
    Link --> UI
```

The server secret stays in the server environment. Direct browser access to the workspace table and evidence bucket is not granted.

## Investigation decisions

```mermaid
flowchart TD
    D[Detected] --> T[Team and analyst assigned]
    T --> I[Investigating]
    I --> C[Confirmed]
    I --> R[Rejected or linked duplicate]
    C --> W[Warranty scope review]
    W --> N[Notice prepared and acknowledged]
    C --> P[Repair in progress]
    N --> P
    P --> V[Awaiting verification]
    V --> E{Clear repeat evidence?}
    E -->|Yes and independent review| X[Verified closed]
    E -->|Failed repair| O[Reopened]
    E -->|Uncertain| V
    X -->|Later failure| O
    O --> I
```

A hold records the preceding stage and resumes that same stage. Notice preparation is internal in this release; outgoing delivery is a future integration.

## Target relational model — design, not deployed tables

```mermaid
erDiagram
    ORGANIZATION ||--o{ MEMBERSHIP : authorizes
    ORGANIZATION ||--o{ CASE : owns
    TEAM ||--o{ MEMBERSHIP : groups
    TEAM ||--o{ CASE : receives
    CASE ||--o{ CASE_EVENT : records
    CASE ||--o{ OBSERVATION : investigates
    OBSERVATION ||--o{ EVIDENCE : supports
    CASE ||--o{ VERIFICATION : reviews
    CONTRACT ||--o{ CASE : supports_match
    CONTRACTOR ||--o{ CONTRACT : performs
    CASE ||--o{ NOTICE : requests
    NOTICE ||--o{ OUTBOX_JOB : delivers
```

Use organization-scoped keys and foreign keys throughout. Audit/event and notice-outbox writes must commit with their corresponding state change. Spatial road-segment and contract-scope data require PostGIS and authoritative GIS/contract sources.
