# Configurable and versioned policy rules for Output Validation Filter (Agent 13)

POLICY_VERSION = "1.0"

class PolicyConfig:
    """
    Configuration for the policy guard. Externalized rules to ensure no
    hardcoded word lists are embedded inside the agent logic itself.
    This serves as the source of truth for the Output Validation Filter.
    """
    
    # Categories of prohibited language constraints per the contract
    EVALUATIVE_PHRASES = [
        "strong academic record",
        "weak extracurricular profile",
        "top-performing student",
        "area of concern",
        "needs improvement",
        "competitive applicant",
        "excellent leadership",
        "outstanding performance",
        "weak candidate",
        "strong candidate",
        "good fit",
        "poor fit",
        "impressive",
        "lacking",
        "below average",
        "above average"
    ]
    
    COMPARATIVE_CONSTRUCTS = [
        "better than average",
        "worse than",
        "compared to peers",
        "stands out among",
        "in the top",
        "in the bottom",
        "outperforms",
        "underperforms"
    ]
    
    RANKING_STATEMENTS = [
        "top tier",
        "low tier",
        "highly ranked",
        "poorly ranked",
        "number one",
        "best in class"
    ]
    
    PRESCRIPTIVE_LANGUAGE = [
        "should be admitted",
        "should be rejected",
        "is a clear admit",
        "is a clear deny",
        "recommend admission",
        "recommend rejection",
        "must improve",
        "needs to show"
    ]
    
    NORMATIVE_LANGUAGE = [
        "unacceptable grade",
        "acceptable score",
        "satisfactory performance",
        "unsatisfactory performance",
        "inadequate"
    ]
    
    ALL_PROHIBITED = (
        EVALUATIVE_PHRASES + 
        COMPARATIVE_CONSTRUCTS + 
        RANKING_STATEMENTS + 
        PRESCRIPTIVE_LANGUAGE + 
        NORMATIVE_LANGUAGE
    )

    @classmethod
    def get_version(cls) -> str:
        return POLICY_VERSION
    
    @classmethod
    def get_prohibited_terms(cls) -> list[str]:
        return cls.ALL_PROHIBITED
