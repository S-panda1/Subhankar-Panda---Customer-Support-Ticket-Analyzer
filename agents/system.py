
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from .schemas import TriageAnalysis, PrioritizationAnalysis, FinalRoute

load_dotenv()


# Configure agents with lower temperature for more deterministic outputs
agent_config = {
    "temperature": 0.1,  # Lower temperature for more consistent results
    "top_p": 0.9,       # Nucleus sampling
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# Enhanced TriageAgent with more specific examples and clearer boundaries
triage_agent_prompt = """
You are an expert Triage Specialist. Your goal is to provide CONSISTENT and ACCURATE classifications.

**Core Guiding Principle: Knowledge vs. Malfunction**
First, determine the core nature of the request. Is the user asking for KNOWLEDGE (how to do something) or reporting a MALFUNCTION (something is not working as it should)?

- **Knowledge Request -> General Question**
- **Malfunction Report -> Bug**

**STRICT CLASSIFICATION RULES:**

1.  **Bug** - A feature is not working as intended.
    - Keywords: "error", "broken", "failed", "not working".
    - **Crucial Clarification**: Also a `Bug` if **system behavior contradicts the documentation**. (e.g., "Doc says 1000 requests, I only get 500").
    - **Crucial Clarification**: Also a `Bug` for any **visual defects or UI issues**, even if described politely. (e.g., "numbers are misaligned", "button is wrong color").

2.  **General Question** - The user needs to know how to do something.
    - Keywords: "how do I", "can you help", "where can I find".
    - **Crucial Clarification**: For **new users (low account age)** reporting critical issues like "can't log in", classify as a `General Question` first, as it is likely a user setup problem, not a system-wide failure.

3.  **Feature Request** - A request for new functionality.
    - Keywords: "add", "improve", "would be great if", "suggestion".

4.  **Security Concern** - A potential security issue.
    - Keywords: "security", "vulnerability", "unauthorized", "breach".

5.  **Billing Inquiry** - Anything related to payments or subscription.
    - Keywords: "invoice", "payment", "charge", "subscription".

**URGENCY SCORING (Be Consistent and Objective):**
- 5 (Critical): Complete system failure; user's business is stopped. (e.g., "production is down", "can't log in to the whole system").
- 4 (High): A core feature is broken, significantly impacting workflow.
- 3 (Medium): A non-critical feature is broken or behaving incorrectly.
- 2 (Low): Minor issue or visual bug with an easy workaround.
- 1 (Very Low): General questions, documentation requests.

**SENTIMENT ANALYSIS (Objective):**
- 'Frustrated': Expresses extreme anger or threats to cancel.
- 'Negative': Expresses disappointment or unhappiness with a problem.
- 'Neutral': Factual, no emotional language.
- 'Positive': Expresses thanks or provides constructive feedback.
"""



# Create agents with consistency settings
TriageAgent = Agent(
    model="groq:llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    output_type=TriageAnalysis,
    system_prompt=triage_agent_prompt,
  
)

# Enhanced PrioritizationAgent with deterministic rules
prioritization_agent_prompt = """


You are a Business Value Analyst. You apply a fixed set of rules to determine business impact and customer risk. Follow these rules EXACTLY.

**INPUTS PROVIDED:**
- Customer Tier
- Monthly Revenue
- Previous Tickets
- Account Age Days
- Current Sentiment

**RULES FOR BUSINESS IMPACT (Apply in this exact order):**
1. IF `Customer Tier` is "enterprise" -> `business_impact` is "High".
2. IF `Customer Tier` is "premium" -> `business_impact` is "Medium".
3. IF `Customer Tier` is "free" -> `business_impact` is "Low".

**RULES FOR CUSTOMER RISK (Apply in this exact order):**
1. IF `Customer Tier` is "free" -> `customer_risk` is "Low".
2. IF `Current Sentiment` is "Frustrated" -> `customer_risk` is "High".
3. IF `Current Sentiment` is "Negative" -> `customer_risk` is "High".
4. IF `Previous Tickets` > 10 AND `Current Sentiment` is "Neutral" -> `customer_risk` is "Medium".
5. ELSE -> `customer_risk` is "Low".

Execute these rules based on the provided inputs and return the structured analysis.
""" 

PrioritizationAgent = Agent(
    model="groq:llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    output_type=PrioritizationAnalysis,
    system_prompt=prioritization_agent_prompt
)

# Create a deterministic input formatter for consistency
def format_triage_input(ticket_data: dict) -> str:
    """Format triage input consistently."""
    return f"""TICKET ANALYSIS REQUEST

Subject: {ticket_data['subject'].strip()}

Message: {ticket_data['message'].strip()}

Please analyze this ticket and classify it according to the rules provided. Be consistent and accurate."""

def format_prioritization_input(ticket_data: dict, sentiment: str) -> str:
    """Format prioritization input consistently."""
    return f"""CUSTOMER BUSINESS VALUE ANALYSIS

Customer Tier: {ticket_data['customer_tier']}
Monthly Revenue: {ticket_data['monthly_revenue']}
Previous Tickets: {ticket_data['previous_tickets']}
Account Age Days: {ticket_data['account_age_days']}
Current Sentiment: {sentiment}

Apply the business impact and customer risk rules exactly as specified."""

# Enhanced routing with more explicit decision tree
def route_decision_maker(triage: TriageAnalysis, priority: PrioritizationAnalysis) -> FinalRoute:
    """
    Deterministic routing decision maker with explicit decision tree.
    """
    
    # Decision Tree Approach for Consistency
    
    # Level 1: Security Always Wins
    if triage.category == 'Security Concern':
        return FinalRoute(
            recommended_queue='Security_Response_Team',
            priority='Critical',
            reasoning="Security concern - mandatory escalation to security team"
        )
    
    # Level 2: Critical Business Impact + Urgent Bug
    if (priority.business_impact == 'Critical' and 
        triage.category == 'Bug' and 
        triage.urgency_score >= 4):
        return FinalRoute(
            recommended_queue='Tier_3_Engineering',
            priority='Critical',
            reasoning=f"Critical customer with urgent bug (urgency {triage.urgency_score}) - escalate to engineering"
        )
    
    # Level 3: High Business Impact + Urgent Bug  
    if (priority.business_impact == 'High' and 
        triage.category == 'Bug' and 
        triage.urgency_score >= 4):
        return FinalRoute(
            recommended_queue='Tier_3_Engineering',
            priority='Critical',
            reasoning=f"High-value customer with urgent bug (urgency {triage.urgency_score}) - escalate to engineering"
        )
    
    # Level 4: Any Bug from Paying Customers
    if (triage.category == 'Bug' and 
        priority.business_impact in ['Critical', 'High', 'Medium']):
        if priority.business_impact in ['Critical', 'High']:
            final_priority = 'High'
        else:
            final_priority = 'Medium'
        return FinalRoute(
            recommended_queue='Tier_2_Technical',
            priority=final_priority,
            reasoning=f"Bug from {priority.business_impact.lower()}-impact customer - route to technical support"
        )
    
    # Level 5: Feature Requests
    if triage.category == 'Feature Request':
        if priority.business_impact in ['Critical', 'High']:
            final_priority = 'Medium'
        else:
            final_priority = 'Low'
        return FinalRoute(
            recommended_queue='Product_Feedback',
            priority=final_priority,
            reasoning=f"Feature request from {priority.business_impact.lower()}-impact customer"
        )
    
    # Level 6: Billing Issues
    if triage.category == 'Billing Inquiry':
        if priority.business_impact in ['Critical', 'High']:
            final_priority = 'High'
        else:
            final_priority = 'Medium'
        return FinalRoute(
            recommended_queue='Sales',
            priority=final_priority,
            reasoning=f"Billing inquiry from {priority.business_impact.lower()}-impact customer"
        )
    
    # Level 7: High-Risk Customer Protection (any issue type)
    if (priority.customer_risk == 'High' and 
        priority.business_impact in ['Critical', 'High']):
        return FinalRoute(
            recommended_queue='Tier_2_Technical',
            priority='High',
            reasoning=f"High-risk {priority.business_impact.lower()}-impact customer - prevent churn"
        )
    
    # Level 8: Default Routing for General Questions and Other Issues
    # Determine priority based on business impact
    if priority.business_impact == 'Critical':
        final_priority = 'Medium'
    elif priority.business_impact == 'High':
        final_priority = 'Medium'
    elif priority.business_impact == 'Medium':
        final_priority = 'Low'
    else:  # Low business impact
        final_priority = 'Low'
    
    return FinalRoute(
        recommended_queue='Tier_1_Support',
        priority=final_priority,
        reasoning=f"General inquiry from {priority.business_impact.lower()}-impact customer"
    )


# Enhanced pipeline with consistent input formatting
async def run_analysis_pipeline(ticket_data: dict) -> FinalRoute:
    """Enhanced analysis pipeline with improved consistency."""
    print(f"\n----- Starting Analysis for {ticket_data['ticket_id']} -----")
    
    try:
        # Step 1: Triage Agent analysis with consistent formatting
        print("1. Running TriageAgent...")
        triage_input = format_triage_input(ticket_data)
        triage_result = await TriageAgent.run(triage_input)
        triage_analysis = triage_result.output
        print(f"   - Category: {triage_analysis.category}")
        print(f"   - Urgency: {triage_analysis.urgency_score}")
        print(f"   - Sentiment: {triage_analysis.sentiment}")
        
        # Step 2: Prioritization Agent analysis with consistent formatting
        print("2. Running PrioritizationAgent...")
        priority_input = format_prioritization_input(ticket_data, triage_analysis.sentiment)
        prioritization_result = await PrioritizationAgent.run(priority_input)
        prioritization_analysis = prioritization_result.output
        print(f"   - Business Impact: {prioritization_analysis.business_impact}")
        print(f"   - Customer Risk: {prioritization_analysis.customer_risk}")
        
        # Step 3: Deterministic routing decision
        print("3. Making final routing decision...")
        final_decision = route_decision_maker(triage_analysis, prioritization_analysis)
        print(f"   - Queue: {final_decision.recommended_queue}")
        print(f"   - Priority: {final_decision.priority}")
        
        print("----- Analysis Complete -----")
        return final_decision
        
    except Exception as e:
        print(f"Error in analysis pipeline: {str(e)}")
        # Return a safe default routing
        return FinalRoute(
            recommended_queue='Tier_1_Support',
            priority='Medium',
            reasoning=f"Pipeline error - defaulting to standard routing: {str(e)}"
        )

# Additional utility functions for debugging and analysis

def analyze_ticket_keywords(subject: str, message: str) -> dict:
    """Analyze keywords in ticket for debugging classification issues."""
    
    # Combine subject and message
    full_text = f"{subject} {message}".lower()
    
    # Define keyword categories
    bug_keywords = ['not working', 'broken', 'error', 'bug', 'issue', 'problem', 'failed', 'failure', 'crash']
    question_keywords = ['how do i', 'how to', 'can you help', 'where is', 'where can i', 'help me', 'guide', 'tutorial']
    feature_keywords = ['add', 'enhancement', 'improvement', 'feature request', 'would like', 'suggestion', 'could you']
    security_keywords = ['security', 'vulnerability', 'breach', 'unauthorized', 'suspicious', 'hack']
    billing_keywords = ['payment', 'billing', 'invoice', 'charge', 'subscription', 'refund', 'pricing']
    
    urgency_keywords = {
        5: ['production down', 'system down', 'critical', 'emergency', 'urgent', 'immediately'],
        4: ['high priority', 'important', 'asap', 'urgent', 'major issue'],
        3: ['issue', 'problem', 'not working'],
        2: ['minor', 'small issue', 'cosmetic'],
        1: ['question', 'help', 'guidance']
    }
    
    # Count matches
    keyword_analysis = {
        'bug_matches': sum(1 for kw in bug_keywords if kw in full_text),
        'question_matches': sum(1 for kw in question_keywords if kw in full_text),
        'feature_matches': sum(1 for kw in feature_keywords if kw in full_text),
        'security_matches': sum(1 for kw in security_keywords if kw in full_text),
        'billing_matches': sum(1 for kw in billing_keywords if kw in full_text),
        'urgency_indicators': {}
    }
    
    # Check urgency indicators
    for level, keywords in urgency_keywords.items():
        keyword_analysis['urgency_indicators'][level] = sum(1 for kw in keywords if kw in full_text)
    
    # Suggest category based on keyword analysis
    category_scores = {
        'Bug': keyword_analysis['bug_matches'],
        'General Question': keyword_analysis['question_matches'],
        'Feature Request': keyword_analysis['feature_matches'],
        'Security Concern': keyword_analysis['security_matches'],
        'Billing Inquiry': keyword_analysis['billing_matches']
    }
    
    suggested_category = max(category_scores, key=category_scores.get)
    
    return {
        'keyword_analysis': keyword_analysis,
        'suggested_category': suggested_category,
        'category_confidence': category_scores[suggested_category],
        'text_length': len(full_text),
        'word_count': len(full_text.split())
    }

def debug_routing_decision(ticket_data: dict, triage: TriageAnalysis, priority: PrioritizationAnalysis) -> dict:
    """Debug the routing decision process step by step."""
    
    debug_info = {
        'ticket_id': ticket_data['ticket_id'],
        'input_data': {
            'category': triage.category,
            'urgency_score': triage.urgency_score,
            'sentiment': triage.sentiment,
            'business_impact': priority.business_impact,
            'customer_risk': priority.customer_risk
        },
        'decision_path': [],
        'final_decision': None
    }
    
    # Follow the same decision tree as route_decision_maker
    if triage.category == 'Security Concern':
        debug_info['decision_path'].append("Level 1: Security Concern → Security_Response_Team")
        debug_info['final_decision'] = 'Security_Response_Team'
    elif (priority.business_impact == 'Critical' and triage.category == 'Bug' and triage.urgency_score >= 4):
        debug_info['decision_path'].append("Level 2: Critical + Urgent Bug → Tier_3_Engineering")
        debug_info['final_decision'] = 'Tier_3_Engineering'
    elif (priority.business_impact == 'High' and triage.category == 'Bug' and triage.urgency_score >= 4):
        debug_info['decision_path'].append("Level 3: High + Urgent Bug → Tier_3_Engineering")
        debug_info['final_decision'] = 'Tier_3_Engineering'
    elif (triage.category == 'Bug' and priority.business_impact in ['Critical', 'High', 'Medium']):
        debug_info['decision_path'].append("Level 4: Bug from Paying Customer → Tier_2_Technical")
        debug_info['final_decision'] = 'Tier_2_Technical'
    elif triage.category == 'Feature Request':
        debug_info['decision_path'].append("Level 5: Feature Request → Product_Feedback")
        debug_info['final_decision'] = 'Product_Feedback'
    elif triage.category == 'Billing Inquiry':
        debug_info['decision_path'].append("Level 6: Billing Inquiry → Sales")
        debug_info['final_decision'] = 'Sales'
    elif (priority.customer_risk == 'High' and priority.business_impact in ['Critical', 'High']):
        debug_info['decision_path'].append("Level 7: High-Risk Customer → Tier_2_Technical")
        debug_info['final_decision'] = 'Tier_2_Technical'
    else:
        debug_info['decision_path'].append("Level 8: Default → Tier_1_Support")
        debug_info['final_decision'] = 'Tier_1_Support'
    
    return debug_info