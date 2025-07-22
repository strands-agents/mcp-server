#!/usr/bin/env python3
"""
Test runner script for the MCP server project.

This script provides various options for running tests:
- All tests
- Unit tests only
- Integration tests only
- Performance tests
- Coverage reports
- Specific test files or functions
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for the MCP server project")
    
    # Test selection options
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--slow', action='store_true', help='Include slow tests')
    parser.add_argument('--file', type=str, help='Run specific test file')
    parser.add_argument('--function', type=str, help='Run specific test function')
    
    # Coverage options
    parser.add_argument('--no-cov', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--cov-html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--cov-xml', action='store_true', help='Generate XML coverage report')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    parser.add_argument('--tb', choices=['short', 'long', 'line', 'no'], default='short',
                       help='Traceback format')
    
    # Parallel execution
    parser.add_argument('--parallel', '-n', type=int, help='Run tests in parallel (requires pytest-xdist)')
    
    # Other options
    parser.add_argument('--failfast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--lf', action='store_true', help='Run last failed tests only')
    parser.add_argument('--ff', action='store_true', help='Run failed tests first')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test selection
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.performance:
        cmd.extend(['-m', 'performance'])
    
    # Add slow tests if requested
    if not args.slow:
        if args.unit or args.integration or args.performance:
            cmd.extend(['and', 'not', 'slow'])
        else:
            cmd.extend(['-m', 'not slow'])
    
    # Add specific file or function
    if args.file:
        cmd.append(args.file)
        if args.function:
            cmd[-1] += f'::{args.function}'
    elif args.function:
        cmd.extend(['-k', args.function])
    
    # Add coverage options
    if not args.no_cov:
        cmd.extend(['--cov=src/strands_mcp_server', '--cov=scripts'])
        cmd.append('--cov-report=term-missing')
        
        if args.cov_html:
            cmd.append('--cov-report=html:htmlcov')
        if args.cov_xml:
            cmd.append('--cov-report=xml')
    
    # Add output options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    cmd.extend(['--tb', args.tb])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', str(args.parallel)])
    
    # Add other options
    if args.failfast:
        cmd.append('-x')
    if args.lf:
        cmd.append('--lf')
    if args.ff:
        cmd.append('--ff')
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run the tests
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n✅ All tests passed!")
        
        # Show coverage report location if generated
        if not args.no_cov and args.cov_html:
            print(f"📊 HTML coverage report: {project_root}/htmlcov/index.html")
        
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


def run_quick_tests():
    """Run a quick subset of tests for development."""
    cmd = [
        'python', '-m', 'pytest',
        '-x',  # Stop on first failure
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-m', 'not slow',  # Skip slow tests
        '--cov=src/strands_mcp_server',
        '--cov-report=term-missing'
    ]
    
    return run_command(cmd, "Running quick tests")


def run_full_test_suite():
    """Run the complete test suite with coverage."""
    cmd = [
        'python', '-m', 'pytest',
        '-v',
        '--cov=src/strands_mcp_server',
        '--cov=scripts',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov',
        '--cov-report=xml',
        '--cov-fail-under=80'
    ]
    
    return run_command(cmd, "Running full test suite")


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("Checking test environment...")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} is installed")
    except ImportError:
        print("❌ pytest is not installed")
        return False
    
    # Check if coverage is available
    try:
        import coverage
        print(f"✅ coverage {coverage.__version__} is installed")
    except ImportError:
        print("⚠️  coverage is not installed (optional)")
    
    # Check if test files exist
    test_dir = Path(__file__).parent.parent / 'tests'
    if test_dir.exists():
        test_files = list(test_dir.glob('**/test_*.py'))
        print(f"✅ Found {len(test_files)} test files")
        for test_file in test_files:
            print(f"   - {test_file.relative_to(test_dir.parent)}")
    else:
        print("❌ Tests directory not found")
        return False
    
    # Check if source code exists
    src_dir = Path(__file__).parent.parent / 'src'
    if src_dir.exists():
        print("✅ Source directory found")
    else:
        print("❌ Source directory not found")
        return False
    
    return True


if __name__ == '__main__':
    # Special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            sys.exit(0 if run_quick_tests() else 1)
        elif sys.argv[1] == 'full':
            sys.exit(0 if run_full_test_suite() else 1)
        elif sys.argv[1] == 'check':
            sys.exit(0 if check_test_environment() else 1)
    
    # Regular argument parsing
    sys.exit(main())
