from pydantic import BaseModel, Field
from typing import Literal

class TriageAnalysis(BaseModel):
    """Structured analysis of a support ticket's content."""
    category: Literal[
        'Bug',
        'Feature Request',
        'Security Concern',
        'Billing Inquiry',
        'General Question'
    ] = Field(..., description="The primary category of the ticket.")
    
    urgency_score: int = Field(
        ...,
        ge=1, le=5,
        description="A score from 1 (low) to 5 (critical) based ONLY on the user's language."
    )
    
    sentiment: Literal['Positive', 'Neutral', 'Negative', 'Frustrated'] = Field(
        ...,
        description="The sentiment of the user's message."
    )

class PrioritizationAnalysis(BaseModel):
    """Structured analysis of a customer's business value."""
    business_impact: Literal['Critical', 'High', 'Medium', 'Low'] = Field(
        ...,
        description="The business impact level of this customer."
    )
    customer_risk: Literal['High', 'Medium', 'Low'] = Field(
        ...,
        description="The risk of customer churn based on their history and recent sentiment."
    )

class FinalRoute(BaseModel):
    """The final routing decision for a support ticket."""
    recommended_queue: Literal[
        'Security_Response_Team',
        'Tier_3_Engineering',
        'Tier_2_Technical',
        'Tier_1_Support',
        'Sales',
        'Product_Feedback'
    ] = Field(..., description="The recommended support queue for this ticket.")
    
    priority: Literal['Critical', 'High', 'Medium', 'Low'] = Field(
        ...,
        description="The final priority level for the ticket."
    )
    
    reasoning: str = Field(
        ...,
        description="A concise explanation for the routing decision and priority."
    )