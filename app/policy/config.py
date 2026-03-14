# Configurable and versioned policy rules for Output Validation Filter (Agent 13)

POLICY_VERSION = "1.0"

class PolicyConfig:
    """
    Configuration for the policy guard. Externalized rules to ensure no
    hardcoded word lists are embedded inside the agent logic itself.
    This serves as the source of truth for the Output Validation Filter.
    """
    
    # Authoritative prohibited terms list from Section 5 of the Stage 1.7 Contract
    ALL_PROHIBITED = [
        "Strength", "Weakness", "Outstanding", "Exceptional", "Deficiency", 
        "Below average", "Underperformance", "High potential", "Top candidate", 
        "Risk factor", "Admit", "Reject", "Likelihood", "Impressive", 
        "Concerning", "Excellent", "Poor", "Weak", "Strong", "Competitive", "Uncompetitive"
    ]

    @classmethod
    def get_version(cls) -> str:
        return POLICY_VERSION
    
    @classmethod
    def get_prohibited_terms(cls) -> list[str]:
        return cls.ALL_PROHIBITED
