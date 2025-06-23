# AI Multi-Agent Customer Support Ticket Analyzer

This project implements a multi-agent AI system to automatically analyze, prioritize, and route customer support tickets. It uses two specialized AI agents and a deterministic routing engine to ensure high accuracy, consistency, and explainability.

## How to Run
### Clone the repo:

```bash
git clone https://github.com/S-panda1/Subhankar-Panda---Customer-Support-Ticket-Analyzer.git

cd Subhankar-Panda---Customer-Support-Ticket-Analyzer
```

### Start a virtual environment:

```bash
python -m venv New

New/Scripts/Activate
```
### Install all the necessary libraries:

```bash
pip install -r requirements.txt
```
### Set the API Key:

```bash
GROQ_API_KEY="YOUR_API_HERE"
```
### Run the evaluation Script:

```bash
python evaluation.py
```
### To analyze a single ticket:

```bash
python main.py <TICKET_ID>
# Example: python main.py SUP-001
```

## System Architecture

The system is designed with a clear separation of concerns, following a pipeline model where each component has a distinct, specialized role. This aligns with the case study's requirement to build a system with at least two specialized agents.

![System Architecture Funnel]()

1.  **Triage Agent**
    * **Role**: Analyzes the raw, unstructured text of a support ticket (`subject` and `message`).
      
    * **Task**: Its responsibility is to understand the user's intention and classify the ticket's `category`, assess the user-expressed `urgency_score`, and determine the `sentiment`. The output is structured according to the `TriageAnalysis` schema.
      
    * **Core Principle**: It operates on the "Knowledge vs. Malfunction" principle to differentiate between user questions and system failures, a rule defined in its system prompt.

2.  **Prioritization Agent **
    * **Role**: Assesses the business value and risk associated with the ticket.
      
    * **Task**: It takes structured data about the customer (e.g., tier, revenue) and the sentiment from the Triage Agent to calculate `business_impact` and `customer_risk`. It does *not* analyze the ticket text.
      
    * **Core Principle**: It acts as a deterministic "Executor," applying a fixed set of business rules defined in its prompt with no room for interpretation.

3.  **Deterministic Router **
    * **Role**: This is a standard Python function (`route_decision_maker`), not an AI agent.
      
    * **Task**: It takes the structured outputs from both agents and applies a strict, hierarchical decision tree to determine the final `recommended_queue` and `priority`. This ensures the final routing decision is 100% predictable and auditable. The output is structured as `FinalRoute`.

## The Funnel Model: Filter -> Rank -> Priority Order

The system explicitly follows a funnel model to process tickets efficiently and logically, orchestrated by the `run_analysis_pipeline` function.

1.  **Filter & Categorize (Top of the Funnel)**: The `TriageAgent` acts as the initial filter. It ingests a raw ticket and transforms it into structured data, categorizing the core issue.

2.  **Rank & Score (Middle of the Funnel)**: The `PrioritizationAgent` takes the categorized ticket and ranks it based on business value. It adds a layer of context that is independent of the ticket's content, answering the question, "How important is this customer?".
   
3.  **Prioritize & Assign (Bottom of the Funnel)**: The `route_decision_maker` function makes the final decision. It synthesizes the "what" from the Triage Agent and the "who" from the Prioritization Agent to assign a final priority and route the ticket to the correct team.

## Design Approach and Rationale

The project was guided by several key principles outlined in the case study, including designing specialized agents and implementing a robust evaluation framework.

### What Worked: The Successful Approach

* **Agent Specialization**: Instead of one large, monolithic agent, separating tasks into a language expert (`TriageAgent`) and a business logic engine (`PrioritizationAgent`). This separation was key to achieving high accuracy and was a core requirement.
  
* **Deterministic Logic for Final Routing**: Using a standard Python `if/elif/else` function (`route_decision_maker`) for the final routing decision removed all ambiguity from the most critical step.
  
* **Focused Prompt Engineering**:
    * **Triage Agent**: The breakthrough came from adding the **"Knowledge vs. Malfunction"** guiding principle to the prompt. This heuristic allowed the agent to correctly distinguish between a user needing help (`General Question`) and a system failing (`Bug`), which was the biggest source of errors in the initial version.
      
    * **Prioritization Agent**: The initial prompt was too descriptive. **Simplifying and hardening it** to be a direct, programmatic list of rules made it faster, cheaper, and virtually error-proof, turning it into a pure "Executor".

### What Didn't Work: The Initial Approach

* **Vague Triage Rules**: The first version of the `TriageAgent` prompt had rules that were too general. The agent struggled to differentiate between a frustrated new user unable to log in and a system-wide login failure, leading to a cascade of routing errors.
  
* **Overly Complex Prioritization**: The initial `PrioritizationAgent` prompt contained more complex, multi-conditional rules. This was unnecessary complexity that introduced risk and processing overhead without adding significant value.
  
* **Relying on a Single Agent**: Early consideration was given to using a single agent for all tasks. This was rejected because it would require an extremely complex prompt, making it difficult to debug and less explainable, contradicting the goal of having specialized agents.

### Possible Improvements
* **Frequency-Based Anomaly Detection:**
Add a new agent to monitor ticket volume and contextual similarity, automatically escalating issues during outages.

* **Priority Boost for Regular Users:**
Giving more weight to users who frequently raise tickets—regardless of tier—by considering ticket history to adjust risk or priority.

* **Intelligent Fallback System:**
Implement fallback logic to use rule-based logic or a lightweight model when the main AI agent fails, times out, or is overloaded.

* **Data Hygiene: Null & Duplicate Filtering:**
Add checks to skip tickets with missing fields or nearly identical content to avoid redundant processing and noise in analytics.


## Codebase Structure

* `main.py`: Entry point to run the analysis on a single ticket from the command line.
* `evaluation.py`: The evaluation framework to test the system's accuracy and consistency against a ground truth dataset.
* `system.py`: The core logic of the system. Contains the prompts for the AI agents, the agent definitions, and the final routing function.
* `schemas.py`: Defines the Pydantic data models (`TriageAnalysis`, `PrioritizationAnalysis`, `FinalRoute`) that ensure structured and validated data flows between components.
* `data/`: Contains `test_cases.json` and `ground_truth.json` for evaluation.


