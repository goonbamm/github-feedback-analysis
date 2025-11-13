#!/usr/bin/env python3
"""간단한 개선사항 통합 테스트"""

def test_constants_import():
    """Test that constants module imports successfully"""
    try:
        from github_feedback import constants
        assert hasattr(constants, 'HEURISTIC_THRESHOLDS')
        assert 'pr_very_large' in constants.HEURISTIC_THRESHOLDS
        assert 'llm_temperature' in constants.HEURISTIC_THRESHOLDS
        print("✓ Constants module: HEURISTIC_THRESHOLDS 추가 확인")
        return True
    except Exception as e:
        print(f"✗ Constants module failed: {e}")
        return False


def test_heuristic_thresholds():
    """Test that HEURISTIC_THRESHOLDS has expected values"""
    try:
        from github_feedback.constants import HEURISTIC_THRESHOLDS

        # Check key thresholds exist
        required_keys = [
            'pr_very_large', 'pr_small', 'pr_body_min_quality_length',
            'commit_min_length', 'commit_max_length', 'llm_temperature'
        ]

        for key in required_keys:
            assert key in HEURISTIC_THRESHOLDS, f"Missing key: {key}"

        # Check values are reasonable
        assert HEURISTIC_THRESHOLDS['pr_very_large'] == 1000
        assert HEURISTIC_THRESHOLDS['pr_small'] == 100
        assert HEURISTIC_THRESHOLDS['llm_temperature'] == 0.3

        print("✓ HEURISTIC_THRESHOLDS: 모든 필수 키와 값 확인")
        return True
    except Exception as e:
        print(f"✗ HEURISTIC_THRESHOLDS failed: {e}")
        return False


def test_llm_syntax():
    """Test that llm.py has no syntax errors"""
    try:
        import ast
        with open('github_feedback/llm.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("✓ llm.py: 문법 에러 없음")
        return True
    except SyntaxError as e:
        print(f"✗ llm.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ llm.py failed: {e}")
        return False


def test_reviewer_syntax():
    """Test that reviewer.py has no syntax errors"""
    try:
        import ast
        with open('github_feedback/reviewer.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("✓ reviewer.py: 문법 에러 없음")
        return True
    except SyntaxError as e:
        print(f"✗ reviewer.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ reviewer.py failed: {e}")
        return False


def test_collector_syntax():
    """Test that collector.py has no syntax errors"""
    try:
        import ast
        with open('github_feedback/collector.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("✓ collector.py: 문법 에러 없음")
        return True
    except SyntaxError as e:
        print(f"✗ collector.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ collector.py failed: {e}")
        return False


def test_type_hints():
    """Test that type hints are consistent"""
    try:
        import ast

        # Check llm.py for consistent type hints
        with open('github_feedback/llm.py', 'r') as f:
            llm_code = f.read()

        # Check that Optional is used instead of | None in some places
        assert 'last_error: Optional[Exception]' in llm_code
        assert 'temperature: Optional[float]' in llm_code

        # Check reviewer.py
        with open('github_feedback/reviewer.py', 'r') as f:
            reviewer_code = f.read()

        assert 'llm: Optional[LLMClient]' in reviewer_code

        print("✓ Type hints: Optional 타입 힌트 일관성 확인")
        return True
    except Exception as e:
        print(f"✗ Type hints failed: {e}")
        return False


def test_magic_numbers_removed():
    """Test that magic numbers are replaced with constants"""
    try:
        with open('github_feedback/llm.py', 'r') as f:
            llm_code = f.read()

        # Check that HEURISTIC_THRESHOLDS is imported
        assert 'from .constants import HEURISTIC_THRESHOLDS' in llm_code

        # Check that it's used in key places
        assert "HEURISTIC_THRESHOLDS['llm_temperature']" in llm_code
        assert "HEURISTIC_THRESHOLDS['commit_min_length']" in llm_code

        with open('github_feedback/reviewer.py', 'r') as f:
            reviewer_code = f.read()

        assert 'from .constants import HEURISTIC_THRESHOLDS' in reviewer_code
        assert "HEURISTIC_THRESHOLDS['pr_very_large']" in reviewer_code

        print("✓ Magic numbers: 하드코딩 제거 및 상수 사용 확인")
        return True
    except Exception as e:
        print(f"✗ Magic numbers test failed: {e}")
        return False


def test_error_handling_improvements():
    """Test that error handling has been improved"""
    try:
        with open('github_feedback/reviewer.py', 'r') as f:
            reviewer_code = f.read()

        # Check for more specific exception handling
        assert 'except requests.ConnectionError' in reviewer_code
        assert 'except requests.Timeout' in reviewer_code
        assert 'except json.JSONDecodeError' in reviewer_code
        assert 'except ValueError' in reviewer_code
        assert 'except KeyError' in reviewer_code

        print("✓ Error handling: 예외 타입별 세분화된 처리 확인")
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_timeout_improvements():
    """Test that timeout handling has been improved"""
    try:
        with open('github_feedback/collector.py', 'r') as f:
            collector_code = f.read()

        # Check for improved logging and error messages
        assert 'logger.warning' in collector_code
        assert 'data may be incomplete' in collector_code

        print("✓ Timeout handling: 개선된 로깅 및 에러 메시지 확인")
        return True
    except Exception as e:
        print(f"✗ Timeout improvements test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("GFA Feedback 개선사항 통합 테스트")
    print("=" * 60)
    print()

    tests = [
        test_constants_import,
        test_heuristic_thresholds,
        test_llm_syntax,
        test_reviewer_syntax,
        test_collector_syntax,
        test_type_hints,
        test_magic_numbers_removed,
        test_error_handling_improvements,
        test_timeout_improvements,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"테스트 결과: {passed}/{total} 통과")

    if passed == total:
        print("✓ 모든 테스트 통과!")
        return 0
    else:
        print(f"✗ {total - passed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
