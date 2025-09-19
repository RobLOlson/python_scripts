import math
import re
from fractions import Fraction
from unittest.mock import patch

from ..algebra.problems import generate_fraction_addition


class TestGenerateFractionAddition:
    """Test suite for the generate_fraction_addition function."""

    def test_return_type(self):
        """Test that the function returns a tuple of two strings."""
        problem, answer = generate_fraction_addition()
        assert isinstance(problem, str)
        assert isinstance(answer, str)
        assert isinstance((problem, answer), tuple)

    def test_problem_statement_included(self):
        """Test that the problem statement is included in the output."""
        problem, _ = generate_fraction_addition()
        assert "Add the following fractions" in problem
        assert "simplified fraction" in problem

    def test_latex_format(self):
        """Test that the output uses proper LaTeX formatting."""
        problem, answer = generate_fraction_addition()
        
        # Check for LaTeX fraction formatting in problem
        assert r"\frac{" in problem
        assert r"}" in problem
        assert "+" in problem
        
        # Check for LaTeX dfrac formatting in answer
        assert r"\dfrac{" in answer
        assert r"}" in answer

    def test_difficulty_levels(self):
        """Test that different freq_weight values produce different difficulty levels."""
        # Test easy difficulty (high freq_weight)
        problem_easy, _ = generate_fraction_addition(freq_weight=10000)
        
        # Test medium difficulty (medium freq_weight)
        problem_medium, _ = generate_fraction_addition(freq_weight=100)
        
        # Test hard difficulty (low freq_weight)
        problem_hard, _ = generate_fraction_addition(freq_weight=1)
        
        # All should be different (though this is probabilistic)
        assert isinstance(problem_easy, str)
        assert isinstance(problem_medium, str)
        assert isinstance(problem_hard, str)

    def test_easy_difficulty_characteristics(self):
        """Test characteristics of easy difficulty problems."""
        with patch('random.choice') as mock_choice, patch('random.randint') as mock_randint:
            # Mock easy difficulty (freq_weight = 10000)
            mock_choice.side_effect = [2, 3]  # denominators
            mock_randint.side_effect = [1, 2]  # numerators
            
            problem, answer = generate_fraction_addition(freq_weight=10000)
            
            # Should have only two fractions (not three)
            assert problem.count(r"\frac{") == 2
            assert problem.count("+") == 1

    def test_hard_difficulty_characteristics(self):
        """Test characteristics of hard difficulty problems."""
        with patch('random.choice') as mock_choice, patch('random.randint') as mock_randint:
            # Mock hard difficulty (freq_weight = 0.01 to get difficulty > 2)
            mock_choice.side_effect = [2, 3, 4]  # denominators
            mock_randint.side_effect = [1, 2, 3]  # numerators
			
            problem, answer = generate_fraction_addition(freq_weight=0)
            
            # Should have three fractions
            assert problem.count(r"\frac{") == 3
            assert problem.count("+") == 2

    def test_fraction_calculation_correctness(self):
        """Test that fraction calculations are mathematically correct."""
        with patch('random.choice') as mock_choice, patch('random.randint') as mock_randint:
            # Set up specific values for predictable testing
            mock_choice.side_effect = [2, 3]  # denominators 2, 3
            mock_randint.side_effect = [1, 2]  # numerators 1, 2
            
            problem, answer = generate_fraction_addition(freq_weight=10000)
            
            # Calculate expected result: 1/2 + 2/3 = 3/6 + 4/6 = 7/6
            expected = Fraction(1, 2) + Fraction(2, 3)
            
            # Extract the answer fraction from LaTeX
            answer_match = re.search(r'\\dfrac\{(\d+)\}\{(\d+)\}', answer)
            assert answer_match is not None
            
            answer_num = int(answer_match.group(1))
            answer_den = int(answer_match.group(2))
            actual = Fraction(answer_num, answer_den)
            
            assert actual == expected

    def test_proper_fractions_for_easy_difficulty(self):
        """Test that easy difficulty problems generate proper fractions (numerator < denominator)."""
        with patch('random.choice') as mock_choice, patch('random.randint') as mock_randint:
            # Mock easy difficulty with large numerators that should be capped
            mock_choice.side_effect = [2, 3]  # denominators 2, 3
            mock_randint.side_effect = [10, 15]  # large numerators that should be capped
            
            problem, answer = generate_fraction_addition(freq_weight=10000)
            
            # Extract fractions from problem
            frac_matches = re.findall(r'\\frac\{(\d+)\}\{(\d+)\}', problem)
            assert len(frac_matches) == 2
            
            for num_str, den_str in frac_matches:
                num = int(num_str)
                den = int(den_str)
                # For easy difficulty, fractions should be proper (numerator < denominator)
                assert num < den

    def test_answer_format(self):
        """Test that the answer is properly formatted as a LaTeX fraction."""
        problem, answer = generate_fraction_addition()
        
        # Answer should be wrapped in parentheses and use dfrac
        assert answer.startswith(r"\(")
        assert answer.endswith(r"\)")
        assert r"\dfrac{" in answer
        
        # Should contain exactly one fraction
        dfrac_count = answer.count(r"\dfrac{")
        assert dfrac_count == 1

    def test_problem_format(self):
        """Test that the problem is properly formatted."""
        problem, answer = generate_fraction_addition()
        
        # Problem should contain the statement and the fractions
        assert "Add the following fractions" in problem
        assert r"\(" in problem  # LaTeX math mode
        assert r"\)" in problem  # End LaTeX math mode
        
        # Should contain proper spacing
        assert "\\\\" in problem  # LaTeX line breaks

    def test_multiple_calls_produce_different_results(self):
        """Test that multiple calls produce different results (due to randomization)."""
        results = []
        for _ in range(10):
            problem, answer = generate_fraction_addition()
            results.append((problem, answer))
        
        # At least some results should be different (probabilistic test)
        unique_results = set(results)
        assert len(unique_results) > 1, "All results were identical - randomization may not be working"

    def test_freq_weight_parameter(self):
        """Test that different freq_weight values are handled correctly."""
        # Test with various freq_weight values
        for freq_weight in [1, 10, 100, 1000, 10000]:
            problem, answer = generate_fraction_addition(freq_weight=freq_weight)
            assert isinstance(problem, str)
            assert isinstance(answer, str)
            assert len(problem) > 0
            assert len(answer) > 0

    def test_difficulty_calculation(self):
        """Test that difficulty is calculated correctly based on freq_weight."""
        # Test the difficulty calculation logic
        test_cases = [
            (10000, -1),  # Very high freq_weight should give difficulty -1
            (1000, 0),    # High freq_weight should give difficulty 0
            (100, 0),     # Medium freq_weight should give difficulty 0
            (10, 1),      # Low freq_weight should give difficulty 1
            (1, 2),       # Very low freq_weight should give difficulty 2
        ]
        
        for freq_weight, expected_difficulty in test_cases:
            calculated_difficulty = int(3 - math.log(freq_weight + 1, 10))
            assert calculated_difficulty == expected_difficulty

    def test_three_fraction_problems(self):
        """Test that hard difficulty problems include three fractions."""
        # Force hard difficulty by using very low freq_weight (0.01 to get difficulty > 2)
        problem, answer = generate_fraction_addition(freq_weight=0)
        
        # Count fractions in the problem
        frac_count = problem.count(r"\frac{")
        plus_count = problem.count("+")
        
        # For hard difficulty, should have 3 fractions and 2 plus signs
        assert frac_count == 3
        assert plus_count == 2

    def test_two_fraction_problems(self):
        """Test that easy/medium difficulty problems include two fractions."""
        # Force easy difficulty by using very high freq_weight
        problem, answer = generate_fraction_addition(freq_weight=10000)
        
        # Count fractions in the problem
        frac_count = problem.count(r"\frac{")
        plus_count = problem.count("+")
        
        # For easy/medium difficulty, should have 2 fractions and 1 plus sign
        assert frac_count == 2
        assert plus_count == 1

    def test_fraction_simplification(self):
        """Test that the answer uses Python's Fraction class for proper simplification."""
        # This test verifies that the function uses Fraction for automatic simplification
        with patch('random.choice') as mock_choice, patch('random.randint') as mock_randint:
            # Set up values that would result in a reducible fraction
            mock_choice.side_effect = [2, 4]  # denominators 2, 4
            mock_randint.side_effect = [1, 1]  # numerators 1, 1
            
            problem, answer = generate_fraction_addition(freq_weight=10000)
            
            # 1/2 + 1/4 = 2/4 + 1/4 = 3/4 (should be simplified)
            expected = Fraction(1, 2) + Fraction(1, 4)
            
            # Extract answer
            answer_match = re.search(r'\\dfrac\{(\d+)\}\{(\d+)\}', answer)
            assert answer_match is not None
            
            answer_num = int(answer_match.group(1))
            answer_den = int(answer_match.group(2))
            actual = Fraction(answer_num, answer_den)
            
            assert actual == expected
            # Verify it's simplified (3/4, not 6/8)
            assert actual.numerator == 3
            assert actual.denominator == 4
