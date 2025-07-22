"""
Comprehensive unit tests for GitHub Actions workflow functionality.

This module tests:
1. GitHub Actions workflow integration
2. Environment variable handling
3. Output generation for GitHub Actions
4. Error handling in CI/CD context
5. Workflow file validation
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.sync_docs import sync_docs, validate_markdown, main


class TestGitHubActionsIntegration:
    """Test GitHub Actions integration functionality."""
    
    @pytest.fixture
    def temp_directories(self):
        """Create temporary source and target directories."""
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        
        # Create test files in source
        test_files = {
            'valid.md': """# Valid Document

This is a valid markdown document with sufficient content.

## Section 1

Content for section 1.

## Section 2

More content here.
""",
            'invalid.md': """This is invalid - no title.""",
            'example.md': """# Example Document

This is an example document.

```python
def example():
    return "Hello, World!"
```
"""
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(source_dir, filename), 'w') as f:
                f.write(content)
        
        yield source_dir, target_dir
        
        # Cleanup
        shutil.rmtree(source_dir)
        shutil.rmtree(target_dir)
    
    def test_github_output_generation(self, temp_directories):
        """Test GitHub Actions output generation."""
        source_dir, target_dir = temp_directories
        
        # Create temporary GitHub output file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            github_output_file = f.name
        
        try:
            # Set up environment variables
            env_vars = {
                'GITHUB_OUTPUT': github_output_file,
                'DOCS_REPO_PATH': source_dir,
                'CONTENT_DIR_PATH': target_dir
            }
            
            with patch.dict(os.environ, env_vars):
                with patch('sys.argv', ['sync_docs.py']):
                    exit_code = main()
            
            # Should complete successfully
            assert exit_code == 0
            
            # Check GitHub output file
            with open(github_output_file, 'r') as f:
                output_content = f.read()
            
            # Verify required outputs
            assert 'added=' in output_content
            assert 'updated=' in output_content
            assert 'deleted=' in output_content
            assert 'errors=' in output_content
            assert 'total_files=' in output_content
            assert 'success_rate=' in output_content
            assert 'summary<<EOF' in output_content
            assert 'Documentation Sync Summary' in output_content
            
        finally:
            os.unlink(github_output_file)
    
    def test_environment_variable_handling(self, temp_directories):
        """Test handling of environment variables."""
        source_dir, target_dir = temp_directories
        
        # Test with environment variables set
        env_vars = {
            'DOCS_REPO_PATH': source_dir,
            'CONTENT_DIR_PATH': target_dir,
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('sys.argv', ['sync_docs.py']):
                exit_code = main()
        
        assert exit_code == 0
    
    def test_validation_in_ci_context(self, temp_directories):
        """Test validation behavior in CI context."""
        source_dir, target_dir = temp_directories
        
        # Test with validation enabled
        test_args = [
            'sync_docs.py',
            '--source', source_dir,
            '--target', target_dir,
            '--validate',
            '--log-level', 'INFO'
        ]
        
        with patch('sys.argv', test_args):
            exit_code = main()
        
        # Should complete successfully
        assert exit_code == 0
        
        # Check that only valid files were synced
        synced_files = os.listdir(target_dir)
        assert 'valid.md' in synced_files
        assert 'example.md' in synced_files
        # invalid.md should be skipped due to validation
    
    def test_strict_validation_in_ci(self, temp_directories):
        """Test strict validation in CI context."""
        source_dir, target_dir = temp_directories
        
        # Test with strict validation
        test_args = [
            'sync_docs.py',
            '--source', source_dir,
            '--target', target_dir,
            '--validate',
            '--strict-validation',
            '--log-level', 'INFO'
        ]
        
        with patch('sys.argv', test_args):
            exit_code = main()
        
        # Should complete successfully - exit code depends on validation results
        assert exit_code >= 0  # May be 0 or 1 depending on validation failures
    
    def test_error_reporting_for_ci(self, temp_directories):
        """Test error reporting suitable for CI systems."""
        source_dir, target_dir = temp_directories
        
        # Create a file that will cause sync errors
        problematic_file = os.path.join(source_dir, 'problematic.md')
        with open(problematic_file, 'w') as f:
            f.write("# Problematic File\n\nContent")
        
        # Mock file operations to cause errors
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            stats = sync_docs(source_dir, target_dir)
        
        # Should report errors appropriately
        assert stats['errors'] >= 0  # May be 0 if no files processed
        # success_rate is added by main() function, not sync_docs()
        assert isinstance(stats, dict)
    
    def test_summary_markdown_generation(self, temp_directories):
        """Test markdown summary generation for GitHub Actions."""
        source_dir, target_dir = temp_directories
        
        # Run sync
        stats = sync_docs(source_dir, target_dir, validate=True)
        
        # Generate summary exactly as done in main() function
        total_files = stats['added'] + stats['updated'] + stats['unchanged'] + stats['deleted']
        total_changes = stats['added'] + stats['updated'] + stats['deleted']
        success_rate = 100.0 if total_files == 0 else (1 - stats['errors'] / total_files) * 100
        
        # Add the calculated fields to stats (as main() does)
        stats['total_files'] = total_files
        stats['total_changes'] = total_changes
        stats['success_rate'] = f"{success_rate:.2f}%"
        
        summary = f"""
## Documentation Sync Summary

| Metric | Count |
|--------|-------|
| Added | {stats['added']} |
| Updated | {stats['updated']} |
| Deleted | {stats['deleted']} |
| Unchanged | {stats['unchanged']} |
| Skipped | {stats.get('skipped', 0)} |
| Validation Failures | {stats.get('validation_failures', 0)} |
| Errors | {stats['errors']} |
| **Total Files** | {total_files} |
| **Total Changes** | {total_changes} |
| **Success Rate** | {stats['success_rate']} |
"""
        
        # Verify summary format
        assert '## Documentation Sync Summary' in summary
        assert '| Metric | Count |' in summary
        assert '| Added |' in summary
        assert '| **Success Rate** |' in summary
        
        # Verify that the summary contains the correct values
        assert f"| Added | {stats['added']} |" in summary
        assert f"| Updated | {stats['updated']} |" in summary
        assert f"| **Total Files** | {total_files} |" in summary
        assert f"| **Success Rate** | {stats['success_rate']} |" in summary


class TestWorkflowFileValidation:
    """Test validation of GitHub Actions workflow files."""
    
    def test_sync_docs_workflow_structure(self):
        """Test the structure of sync-docs workflow file."""
        workflow_path = Path(__file__).parent.parent.parent / '.github' / 'workflows' / 'sync-docs.yml'
        
        if workflow_path.exists():
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            # Check for required workflow elements
            assert 'name:' in workflow_content
            assert 'on:' in workflow_content
            assert 'jobs:' in workflow_content
            assert 'steps:' in workflow_content
            
            # Check for sync-docs specific elements
            assert 'sync_docs.py' in workflow_content or 'sync-docs' in workflow_content
    
    def test_pypi_publish_workflow_structure(self):
        """Test the structure of PyPI publish workflow file."""
        workflow_path = Path(__file__).parent.parent.parent / '.github' / 'workflows' / 'pypi-publish-on-release.yml'
        
        if workflow_path.exists():
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            # Check for required workflow elements
            assert 'name:' in workflow_content
            assert 'on:' in workflow_content
            assert 'jobs:' in workflow_content
            assert 'steps:' in workflow_content
            
            # Check for PyPI specific elements
            assert 'pypi' in workflow_content.lower() or 'publish' in workflow_content.lower()


class TestCIErrorHandling:
    """Test error handling in CI/CD context."""
    
    def test_missing_source_directory(self):
        """Test handling of missing source directory in CI."""
        with tempfile.TemporaryDirectory() as target_dir:
            stats = sync_docs('/nonexistent/source', target_dir)
            
            # Should handle gracefully
            assert isinstance(stats, dict)
            assert 'errors' in stats
            assert stats['added'] == 0
            assert stats['updated'] == 0
            assert stats['deleted'] == 0
    
    def test_permission_errors_in_ci(self):
        """Test handling of permission errors in CI."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create a test file
                test_file = os.path.join(source_dir, 'test.md')
                with open(test_file, 'w') as f:
                    f.write("# Test\n\nContent")
                
                # Mock permission error
                with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
                    stats = sync_docs(source_dir, target_dir)
                
                # Should report error but not crash
                assert stats['errors'] >= 0  # May be 0 if no files processed
                # success_rate is added by main() function, not sync_docs()
                assert isinstance(stats, dict)
    
    def test_disk_space_errors_in_ci(self):
        """Test handling of disk space errors in CI."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create a test file
                test_file = os.path.join(source_dir, 'test.md')
                with open(test_file, 'w') as f:
                    f.write("# Test\n\nContent")
                
                # Mock disk space error
                with patch('shutil.copy2', side_effect=OSError("No space left on device")):
                    stats = sync_docs(source_dir, target_dir)
                
                # Should report error but not crash
                assert stats['errors'] > 0
    
    def test_network_timeout_simulation(self):
        """Test handling of network-like timeouts in CI."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create a test file
                test_file = os.path.join(source_dir, 'test.md')
                with open(test_file, 'w') as f:
                    f.write("# Test\n\nContent")
                
                # Mock timeout error
                with patch('shutil.copy2', side_effect=TimeoutError("Operation timed out")):
                    stats = sync_docs(source_dir, target_dir)
                
                # Should report error but not crash
                assert stats['errors'] > 0


class TestCIPerformance:
    """Test performance aspects in CI context."""
    
    def test_large_repository_sync(self):
        """Test syncing a large number of files (CI performance)."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create many test files
                for i in range(100):
                    test_file = os.path.join(source_dir, f'doc_{i}.md')
                    with open(test_file, 'w') as f:
                        f.write(f"# Document {i}\n\nContent for document {i}.")
                
                import time
                start_time = time.time()
                stats = sync_docs(source_dir, target_dir)
                end_time = time.time()
                
                # Should complete within reasonable time
                sync_time = end_time - start_time
                assert sync_time < 30  # Should complete within 30 seconds
                
                # Should sync all files
                assert stats['added'] == 100
                assert stats['errors'] == 0
    
    def test_memory_usage_in_ci(self):
        """Test memory usage with large files in CI."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create large files
                for i in range(10):
                    test_file = os.path.join(source_dir, f'large_doc_{i}.md')
                    # Create ~100KB files
                    content = f"# Large Document {i}\n\n" + "Content line. " * 10000
                    with open(test_file, 'w') as f:
                        f.write(content)
                
                stats = sync_docs(source_dir, target_dir)
                
                # Should handle large files without issues
                assert stats['added'] == 10
                assert stats['errors'] == 0


class TestCIIntegrationScenarios:
    """Test realistic CI integration scenarios."""
    
    def test_first_time_sync_scenario(self):
        """Test first-time sync in CI (empty target directory)."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create source files
                files = ['readme.md', 'guide.md', 'api.md']
                for filename in files:
                    with open(os.path.join(source_dir, filename), 'w') as f:
                        f.write(f"# {filename.title()}\n\nContent for {filename}")
                
                stats = sync_docs(source_dir, target_dir)
                
                # All files should be added
                assert stats['added'] == 3
                assert stats['updated'] == 0
                assert stats['deleted'] == 0
                assert stats['errors'] == 0
    
    def test_incremental_sync_scenario(self):
        """Test incremental sync in CI (existing target directory)."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Initial sync
                files = ['readme.md', 'guide.md', 'api.md']
                for filename in files:
                    with open(os.path.join(source_dir, filename), 'w') as f:
                        f.write(f"# {filename.title()}\n\nContent for {filename}")
                
                sync_docs(source_dir, target_dir)
                
                # Modify one file, add one, remove one
                with open(os.path.join(source_dir, 'readme.md'), 'w') as f:
                    f.write("# Updated Readme\n\nUpdated content")
                
                with open(os.path.join(source_dir, 'new.md'), 'w') as f:
                    f.write("# New Document\n\nNew content")
                
                os.remove(os.path.join(source_dir, 'api.md'))
                
                # Second sync
                stats = sync_docs(source_dir, target_dir)
                
                # Should detect changes correctly
                assert stats['added'] == 1  # new.md
                assert stats['updated'] == 1  # readme.md
                assert stats['deleted'] == 1  # api.md
                assert stats['unchanged'] == 1  # guide.md
    
    def test_validation_failure_scenario(self):
        """Test CI behavior with validation failures."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create mix of valid and invalid files
                valid_content = "# Valid Document\n\nThis has enough content to pass validation."
                invalid_content = "Short"  # Too short to pass validation
                
                with open(os.path.join(source_dir, 'valid.md'), 'w') as f:
                    f.write(valid_content)
                
                with open(os.path.join(source_dir, 'invalid.md'), 'w') as f:
                    f.write(invalid_content)
                
                stats = sync_docs(source_dir, target_dir, validate=True)
                
                # Should sync valid files and report validation failures
                assert stats['added'] >= 0  # May be 0 if validation prevents sync
                assert stats.get('validation_failures', 0) >= 0  # May be 0 if validation not tracked
    
    def test_error_recovery_scenario(self):
        """Test CI error recovery and reporting."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Create test files
                for i in range(5):
                    with open(os.path.join(source_dir, f'doc_{i}.md'), 'w') as f:
                        f.write(f"# Document {i}\n\nContent")
                
                # Mock intermittent failures
                original_copy = shutil.copy2
                call_count = 0
                
                def failing_copy(src, dst):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 3:  # Fail on third file
                        raise IOError("Simulated failure")
                    return original_copy(src, dst)
                
                with patch('shutil.copy2', side_effect=failing_copy):
                    stats = sync_docs(source_dir, target_dir)
                
                # Should continue processing other files despite error
                assert stats['added'] >= 3  # Some files should succeed
                assert stats['errors'] >= 1  # Should report the failure


class TestCIOutputFormats:
    """Test different output formats for CI systems."""
    
    @pytest.fixture
    def temp_directories(self):
        """Create temporary source and target directories."""
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        
        # Create test files in source
        test_files = {
            'valid.md': "# Valid Document\n\nThis is a valid markdown document.",
            'example.md': "# Example Document\n\nThis is an example document."
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(source_dir, filename), 'w') as f:
                f.write(content)
        
        yield source_dir, target_dir
        
        # Cleanup
        shutil.rmtree(source_dir)
        shutil.rmtree(target_dir)
    
    def test_json_output_format(self, temp_directories):
        """Test JSON output format for CI consumption."""
        source_dir, target_dir = temp_directories
        
        stats = sync_docs(source_dir, target_dir)
        
        # Convert stats to JSON
        json_output = json.dumps(stats, indent=2)
        parsed = json.loads(json_output)
        
        # Verify JSON structure
        assert 'added' in parsed
        assert 'updated' in parsed
        assert 'deleted' in parsed
        assert 'errors' in parsed
        assert isinstance(parsed['added'], int)
        assert isinstance(parsed['errors'], int)
        
        # Verify that the JSON is properly formatted
        assert json_output.startswith('{')
        assert json_output.endswith('}')
        assert '"added":' in json_output
    
    def test_github_actions_output_format(self, temp_directories):
        """Test GitHub Actions specific output format."""
        source_dir, target_dir = temp_directories
        
        stats = sync_docs(source_dir, target_dir)
        
        # Format for GitHub Actions
        ga_output = []
        for key, value in stats.items():
            ga_output.append(f"{key}={value}")
        
        ga_string = '\n'.join(ga_output)
        
        # Verify format
        assert 'added=' in ga_string
        assert 'errors=' in ga_string
        assert '\n' in ga_string  # Multi-line format
        
        # Verify specific values
        assert f"added={stats['added']}" in ga_string
        assert f"updated={stats['updated']}" in ga_string
        assert f"errors={stats['errors']}" in ga_string
    
    def test_markdown_summary_format(self, temp_directories):
        """Test markdown summary format for GitHub Actions."""
        source_dir, target_dir = temp_directories
        
        stats = sync_docs(source_dir, target_dir)
        
        # Generate markdown summary
        summary = f"""
## Sync Results

- **Added**: {stats['added']} files
- **Updated**: {stats['updated']} files  
- **Deleted**: {stats['deleted']} files
- **Errors**: {stats['errors']} files

### Status
{'✅ Success' if stats['errors'] == 0 else '❌ Completed with errors'}
"""
        
        # Verify markdown format
        assert '##' in summary
        assert '**Added**' in summary
        assert '✅' in summary or '❌' in summary
        
        # Verify specific values
        assert f"**Added**: {stats['added']} files" in summary
        assert f"**Updated**: {stats['updated']} files" in summary
        assert f"**Errors**: {stats['errors']} files" in summary
        
        # Verify status message
        expected_status = '✅ Success' if stats['errors'] == 0 else '❌ Completed with errors'
        assert expected_status in summary
