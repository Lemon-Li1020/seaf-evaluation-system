"""
Tests for grade calculation.
"""

import pytest

from evaluation_system.utils.grade import calculate_grade, get_grade_threshold, grade_to_numeric


class TestGradeCalculation:
    """Test cases for grade calculation utilities."""
    
    def test_grade_a(self):
        """Test Grade A (90-100)."""
        assert calculate_grade(95.0, {}) == "A"
        assert calculate_grade(90.0, {}) == "A"
        assert calculate_grade(92.5, {}) == "A"
    
    def test_grade_b(self):
        """Test Grade B (80-89)."""
        assert calculate_grade(85.0, {}) == "B"
        assert calculate_grade(80.0, {}) == "B"
        assert calculate_grade(88.9, {}) == "B"
    
    def test_grade_c(self):
        """Test Grade C (70-79)."""
        assert calculate_grade(75.0, {}) == "C"
        assert calculate_grade(70.0, {}) == "C"
        assert calculate_grade(79.9, {}) == "C"
    
    def test_grade_d(self):
        """Test Grade D (60-69)."""
        assert calculate_grade(65.0, {}) == "D"
        assert calculate_grade(60.0, {}) == "D"
        assert calculate_grade(69.9, {}) == "D"
    
    def test_grade_f(self):
        """Test Grade F (<60 and <50)."""
        assert calculate_grade(49.9, {}) == "F"  # < 50 -> F
        assert calculate_grade(30.0, {}) == "F"
        assert calculate_grade(0.0, {}) == "F"
        assert calculate_grade(59.99, {}) == "D"  # >= 60 -> D
    
    def test_grade_with_low_dimension(self):
        """Test that low dimension score constrains the grade."""
        # High overall score but one dimension below 60
        by_dimension = {
            "correctness": 95.0,
            "tool_usage": 50.0,  # Low score
            "efficiency": 90.0,
            "relevance": 88.0,
        }
        
        # Overall score is 80.75, but tool_usage < 60 should constrain
        assert calculate_grade(80.75, by_dimension) == "C"
    
    def test_grade_with_all_low_dimensions(self):
        """Test grade when all dimensions are low."""
        by_dimension = {
            "correctness": 55.0,
            "tool_usage": 50.0,
            "efficiency": 45.0,
            "relevance": 40.0,
        }
        
        # Overall ~47.5, min_dimension 40 < 60
        assert calculate_grade(47.5, by_dimension) == "F"
    
    def test_grade_empty_dimensions(self):
        """Test grade with no dimension data."""
        assert calculate_grade(85.0, {}) == "B"
        assert calculate_grade(49.9, {}) == "F"  # < 50 -> F
    
    def test_grade_boundary_90(self):
        """Test exact boundary at 90."""
        assert calculate_grade(89.99, {}) == "B"
        assert calculate_grade(90.0, {}) == "A"
    
    def test_grade_boundary_80(self):
        """Test exact boundary at 80."""
        assert calculate_grade(79.99, {}) == "C"
        assert calculate_grade(80.0, {}) == "B"
    
    def test_grade_boundary_70(self):
        """Test exact boundary at 70."""
        assert calculate_grade(69.99, {}) == "D"
        assert calculate_grade(70.0, {}) == "C"
    
    def test_grade_boundary_60(self):
        """Test exact boundary at 60."""
        assert calculate_grade(59.99, {}) == "D"  # >= 60 -> D
        assert calculate_grade(60.0, {}) == "D"
    
    def test_grade_dimension_constraint_exactly_60(self):
        """Test that dimension exactly at 60 is not constrained."""
        by_dimension = {
            "correctness": 95.0,
            "tool_usage": 60.0,  # Exactly 60 - should NOT constrain
            "efficiency": 90.0,
        }
        
        # Overall ~88.3, all dimensions >= 60
        assert calculate_grade(88.3, by_dimension) == "B"


class TestGradeThreshold:
    """Test cases for grade threshold utilities."""
    
    def test_get_grade_threshold_a(self):
        """Test threshold for Grade A."""
        low, high = get_grade_threshold("A")
        assert low == 90.0
        assert high == 100.0
    
    def test_get_grade_threshold_b(self):
        """Test threshold for Grade B."""
        low, high = get_grade_threshold("B")
        assert low == 80.0
        assert high == 89.99
    
    def test_get_grade_threshold_c(self):
        """Test threshold for Grade C."""
        low, high = get_grade_threshold("C")
        assert low == 70.0
        assert high == 79.99
    
    def test_get_grade_threshold_d(self):
        """Test threshold for Grade D."""
        low, high = get_grade_threshold("D")
        assert low == 60.0
        assert high == 69.99
    
    def test_get_grade_threshold_f(self):
        """Test threshold for Grade F."""
        low, high = get_grade_threshold("F")
        assert low == 0.0
        assert high == 59.99
    
    def test_get_grade_threshold_invalid(self):
        """Test threshold for invalid grade."""
        low, high = get_grade_threshold("X")
        assert low == 0.0
        assert high == 0.0


class TestGradeToNumeric:
    """Test cases for grade to numeric conversion."""
    
    def test_grade_to_numeric_values(self):
        """Test conversion of all grades."""
        assert grade_to_numeric("A") == 4.0
        assert grade_to_numeric("B") == 3.0
        assert grade_to_numeric("C") == 2.0
        assert grade_to_numeric("D") == 1.0
        assert grade_to_numeric("F") == 0.0
    
    def test_grade_to_numeric_invalid(self):
        """Test conversion of invalid grade."""
        assert grade_to_numeric("X") == 0.0
        assert grade_to_numeric("") == 0.0
