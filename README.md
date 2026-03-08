# AuditHawk
The Tech Stack
Frontend: Vanilla JavaScript, HTML5, Tailwind CSS, Flask (Proxy Server).

Backend API: Django, GraphQL (Graphene).

Database: MongoDB (using PyMongo with atomic, session-based transactions).

Machine Learning: PyTorch/TensorFlow (Autoencoders), Scikit-Learn (Local Outlier Factor), NetworkX (Graph Theory).

Client-Side Libraries: html2canvas & jsPDF (for compliance reporting).

The Main Components
1. The Ingestion Engine (CSV Parser)
A secure data pipeline that ingests raw, unstructured corporate financial data, cleanses the data types, and prepares it for multi-dimensional feature extraction.

2. The Independent ML Decision Matrix (The Brains)
An unsupervised machine learning orchestrator that routes data through four distinct, parallel mathematical engines:

Deep Learning Autoencoder: Learns the behavioral "embedding" of every employee to catch Account Takeovers (ATOs).

Local Outlier Factor (LOF): Calculates multi-dimensional spatial density to catch mathematically manufactured clusters of transactions.

NetworkX Graph Topology: Maps the flow of money as nodes and edges to detect Shell Companies and Sinkholes.

Temporal & Velocity Rules Engine: Tracks the velocity of capital over 7-day rolling windows to catch Smurfing/Structuring.

3. The State Machine (GraphQL + MongoDB)
A strongly typed GraphQL API that communicates with a MongoDB database. It handles complex, nested data retrieval and executes atomic transactional rollbacks (meaning if an ML calculation fails halfway through, the database completely reverses the action to prevent corruption).

4. The Threat Inbox (Optimistic UI)
A decoupled, lightning-fast dashboard that immediately updates the DOM before the server even responds. It handles real-time metric calculations, interactive data visualization, and human-in-the-loop (HITL) auditing.

How It Works (The Core Features)
Data Ingestion: The auditor uploads a CSV of 50,000+ transactions.

The Matrix Trap: The data hits the Python backend, which filters the noise and catches four specific threat vectors:

The Micro-ATO: An attacker stealing $9.99 at 3:00 AM.

The Embezzlement Ring: Insiders spreading out identical $2,499 transactions across multiple accounts to dodge thresholds.

The Shell Company: A brand new vendor with zero historical pagerank suddenly receiving massive funds.

The Whale: A transaction whose magnitude is in the 99.9th percentile of corporate spending.

Human-in-the-Loop (HITL) Masking: The auditor sees the flagged items. If the system flags a legitimate $10,000 AWS bill, the auditor adds "AWS" to the Trusted Vendors list. The system instantly recalculates the matrix and drops all AWS-related false positives.

Real-Time Adjudication: The auditor processes the Threat Inbox, clicking "Accept" (Confirmed Fraud) or "Reject" (Dismissed False Positive). The UI updates instantly via state badges without page reloads.

Compliance Export: Once the inbox is cleared, the auditor clicks Download Dashboard. The browser stitches together a pixel-perfect snapshot of the data and generates an offline PDF report for the Chief Risk Officer.
