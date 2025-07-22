"""
Test the sync_docs.py script functionality.

This test verifies that:
1. The sync script correctly synchronizes files between repositories
2. The validation logic works correctly
3. The script handles errors gracefully
4. The script generates correct GitHub Action outputs
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

# Add the project root to the Python path to import the sync_docs module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.sync_docs import sync_docs, validate_markdown, main


class TestSyncDocs(unittest.TestCase):
    """Test the sync_docs.py script functionality."""

    def setUp(self):
        """Set up test environment with mock repositories."""
        # Create temporary directories for source and target
        self.source_dir = tempfile.mkdtemp()
        self.target_dir = tempfile.mkdtemp()
        
        # Create some test markdown files in the source directory
        self.create_test_files()

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.target_dir)

    def create_test_files(self):
        """Create test markdown files in the source directory."""
        # Create a valid markdown file
        with open(os.path.join(self.source_dir, 'valid.md'), 'w') as f:
            f.write("# Valid Document\n\nThis is a valid markdown document with sufficient content to pass validation.\n\n" + 
                   "## Section 1\n\nThis section contains important information about the feature.\n\n" +
                   "## Section 2\n\n- List item 1\n- List item 2\n- List item 3\n\n" +
                   "### Subsection\n\nMore detailed information goes here.\n\n" +
                   "```python\ndef example():\n    return 'This is an example'\n```\n\n" +
                   "The end of the document.")
        
        # Create an invalid markdown file (missing title)
        with open(os.path.join(self.source_dir, 'invalid.md'), 'w') as f:
            f.write("This is an invalid markdown file without a proper title.")
        
        # Create a markdown file with malformed code blocks
        with open(os.path.join(self.source_dir, 'malformed.md'), 'w') as f:
            f.write("# Malformed Document\n\nThis document has a malformed code block.\n\n```python\ndef hello():\n    print('Hello, world!')\n")

    def test_validate_markdown(self):
        """Test the validate_markdown function."""
        # Test valid markdown
        valid_file = os.path.join(self.source_dir, 'valid.md')
        self.assertTrue(validate_markdown(valid_file))
        
        # Test invalid markdown (missing title)
        invalid_file = os.path.join(self.source_dir, 'invalid.md')
        self.assertFalse(validate_markdown(invalid_file))
        
        # Test malformed code blocks
        malformed_file = os.path.join(self.source_dir, 'malformed.md')
        self.assertFalse(validate_markdown(malformed_file))

    def test_sync_docs_basic(self):
        """Test basic functionality of sync_docs."""
        # Run the sync operation
        stats = sync_docs(self.source_dir, self.target_dir)
        
        # Verify that files were added
        self.assertEqual(stats['added'], 3)
        self.assertEqual(stats['errors'], 0)
        
        # Verify that files exist in the target directory
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'valid.md')))
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'invalid.md')))
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_sync_docs_with_validation(self):
        """Test sync_docs with validation."""
        # Run the sync operation with validation
        stats = sync_docs(self.source_dir, self.target_dir, validate=True)
        
        # Verify that invalid files were detected
        self.assertEqual(stats['validation_failures'], 2)  # invalid.md and malformed.md
        self.assertEqual(stats['added'], 1)  # Only valid.md should be added
        
        # Verify that only valid files were synced
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'valid.md')))
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'invalid.md')))
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_sync_docs_with_strict_validation(self):
        """Test sync_docs with strict validation."""
        # Run the sync operation with strict validation
        stats = sync_docs(self.source_dir, self.target_dir, validate=True, strict_validation=True)
        
        # Verify that invalid files were treated as errors
        self.assertEqual(stats['validation_failures'], 2)
        self.assertEqual(stats['errors'], 2)
        
        # Verify that only valid files were synced
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'valid.md')))
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'invalid.md')))
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_sync_docs_file_operations(self):
        """Test file operations in sync_docs."""
        # First sync
        sync_docs(self.source_dir, self.target_dir)
        
        # Modify a file in the source directory
        with open(os.path.join(self.source_dir, 'valid.md'), 'w') as f:
            f.write("# Valid Document (Updated)\n\nThis is an updated valid markdown document.")
        
        # Add a new file
        with open(os.path.join(self.source_dir, 'new.md'), 'w') as f:
            f.write("# New Document\n\nThis is a new document added after the first sync.")
        
        # Delete a file
        os.remove(os.path.join(self.source_dir, 'malformed.md'))
        
        # Run the sync again
        stats = sync_docs(self.source_dir, self.target_dir)
        
        # Verify that files were updated correctly
        self.assertEqual(stats['added'], 1)  # new.md
        self.assertEqual(stats['updated'], 1)  # valid.md
        self.assertEqual(stats['deleted'], 1)  # malformed.md
        
        # Verify file content was updated
        with open(os.path.join(self.target_dir, 'valid.md'), 'r') as f:
            content = f.read()
            self.assertIn('(Updated)', content)
        
        # Verify new file was added
        self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'new.md')))
        
        # Verify deleted file was removed
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_main_function(self):
        """Test the main function with command-line arguments."""
        # Set up command-line arguments
        test_args = [
            'sync_docs.py',
            '--source', self.source_dir,
            '--target', self.target_dir,
            '--log-level', 'INFO'
        ]
        
        # Run the main function
        with patch('sys.argv', test_args):
            exit_code = main()
            
            # Verify that the script exited successfully
            self.assertEqual(exit_code, 0)
            
            # Verify that files were synced
            self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'valid.md')))
            self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'invalid.md')))
            self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_main_function_with_validation(self):
        """Test the main function with validation."""
        # Set up command-line arguments
        test_args = [
            'sync_docs.py',
            '--source', self.source_dir,
            '--target', self.target_dir,
            '--validate'
        ]
        
        # Run the main function
        with patch('sys.argv', test_args):
            exit_code = main()
            
            # Verify that the script exited successfully
            self.assertEqual(exit_code, 0)
            
            # Verify that only valid files were synced
            self.assertTrue(os.path.exists(os.path.join(self.target_dir, 'valid.md')))
            self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'invalid.md')))
            self.assertFalse(os.path.exists(os.path.join(self.target_dir, 'malformed.md')))

    def test_main_function_with_github_output(self):
        """Test the main function with GitHub output."""
        # Create a temporary file for GitHub output
        github_output_file = tempfile.mktemp()
        
        try:
            # Set up environment variables
            env_vars = {
                'GITHUB_OUTPUT': github_output_file,
                'DOCS_REPO_PATH': self.source_dir,
                'CONTENT_DIR_PATH': self.target_dir
            }
            
            # Run the main function
            with patch.dict(os.environ, env_vars), patch('sys.argv', ['sync_docs.py']):
                exit_code = main()
                
                # Verify that the script exited successfully
                self.assertEqual(exit_code, 0)
                
                # Verify that GitHub Action outputs were set
                with open(github_output_file, 'r') as f:
                    output_content = f.read()
                    
                    # Check that the required outputs are present
                    self.assertIn('added=3', output_content)
                    self.assertIn('total_files=3', output_content)
                    self.assertIn('success_rate=100.00%', output_content)
                    self.assertIn('summary<<EOF', output_content)
                    self.assertIn('## Documentation Sync Summary', output_content)
        
        finally:
            # Clean up
            if os.path.exists(github_output_file):
                os.remove(github_output_file)


if __name__ == '__main__':
    unittest.main()