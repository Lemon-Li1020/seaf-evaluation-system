"""
Grade calculation utilities.
"""

from typing import Dict


def calculate_grade(weighted_score: float, by_dimension: Dict[str, float]) -> str:
    """
    Calculate letter grade from weighted score.
    
    Rules:
    - A: 90-100
    - B: 80-89
    - C: 70-79
    - D: 60-69
    - F: <60
    
    Additional constraint:
    - If any dimension score < 60, Grade <= C
    """
    # Check dimension constraints
    min_dimension = min(by_dimension.values()) if by_dimension else weighted_score
    
    if min_dimension < 60:
        # Constrained by dimension - can only be C, D, or F
        if weighted_score >= 60:
            return "C"
        elif weighted_score >= 50:
            return "D"
        else:
            return "F"
    
    # Normal grade assignment
    if weighted_score >= 90:
        return "A"
    elif weighted_score >= 80:
        return "B"
    elif weighted_score >= 70:
        return "C"
    elif weighted_score >= 60:
        return "D"
    else:
        return "F"


def get_grade_threshold(grade: str) -> tuple[float, float]:
    """Get the score threshold range for a given grade."""
    thresholds = {
        "A": (90.0, 100.0),
        "B": (80.0, 89.99),
        "C": (70.0, 79.99),
        "D": (60.0, 69.99),
        "F": (0.0, 59.99),
    }
    return thresholds.get(grade, (0.0, 0.0))


def grade_to_numeric(grade: str) -> float:
    """Convert letter grade to numeric value (4.0 scale)."""
    mapping = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
    return mapping.get(grade, 0.0)
