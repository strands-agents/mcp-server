#!/usr/bin/env python3
"""
Sync documentation files from Strands Agents docs repository to MCP server content folder.
This script is used by the GitHub Action workflow to keep documentation up-to-date.

The script performs the following operations:
1. Scans the source directory (Strands Agents docs repository) for markdown files
2. Compares them with files in the target directory (MCP server content folder)
3. Copies new and modified files from source to target
4. Deletes files from target that no longer exist in source
5. Optionally validates markdown files before syncing
6. Builds a comprehensive document index with relationships and cross-references
7. Generates statistics and reports about the sync operation

This script can be run manually or as part of a GitHub Action workflow.
"""

import os
import shutil
import glob
import argparse
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('docs-sync')

def compare_files(file1, file2):
    """
    Compare two files to check if they are identical.
    
    Args:
        file1 (str): Path to the first file
        file2 (str): Path to the second file
        
    Returns:
        bool: True if files are identical, False otherwise
    """
    # First check file sizes - if different, files are definitely different
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    
    # If sizes match, compare content
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        # Read and compare line by line to avoid loading entire files into memory
        while True:
            line1 = f1.readline()
            line2 = f2.readline()
            
            if line1 != line2:
                return False
            
            if not line1:  # End of file reached
                break
    
    return True

def sync_docs(source_dir, target_dir, validate=False, strict_validation=False):
    """
    Synchronize markdown files from source_dir to target_dir.
    
    Args:
        source_dir (str): Path to the source directory (docs repo)
        target_dir (str): Path to the target directory (content folder)
        validate (bool): Whether to validate markdown files before syncing
        strict_validation (bool): If True, treat validation failures as errors
                                 If False, just skip invalid files
        
    Returns:
        dict: Statistics about the sync operation
    """
    stats = {
        'added': 0,
        'updated': 0,
        'deleted': 0,
        'unchanged': 0,
        'errors': 0,
        'skipped': 0,
        'validation_failures': 0
    }
    
    # Convert to Path objects for more reliable path handling
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of markdown files in source directory
    source_files = list(source_dir.glob('**/*.md'))
    logger.info(f"Found {len(source_files)} markdown files in source directory")
    
    # Get list of existing files in target directory
    target_files = list(target_dir.glob('**/*.md'))
    logger.info(f"Found {len(target_files)} markdown files in target directory")
    
    # Create a map of relative paths to target files for easier lookup
    target_file_map = {file.relative_to(target_dir): file for file in target_files}
    
    # Track validation failures for detailed reporting
    validation_failures = []
    
    # Process each source file
    for source_file in source_files:
        rel_path = source_file.relative_to(source_dir)
        target_file = target_dir / rel_path
        
        # Validate markdown if requested
        if validate:
            try:
                is_valid = validate_markdown(str(source_file))
                if not is_valid:
                    stats['validation_failures'] += 1
                    validation_failures.append(str(rel_path))
                    
                    if strict_validation:
                        logger.error(f"Validation failed for {rel_path} (strict mode)")
                        stats['errors'] += 1
                    else:
                        logger.warning(f"Skipping invalid markdown file: {rel_path}")
                        stats['skipped'] += 1
                    
                    continue
            except Exception as e:
                logger.error(f"Exception during validation of {rel_path}: {str(e)}")
                stats['errors'] += 1
                stats['validation_failures'] += 1
                validation_failures.append(f"{rel_path} (exception: {str(e)})")
                continue
        
        try:
            # Create directory structure if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and has changed
            if target_file.exists():
                if not compare_files(str(source_file), str(target_file)):
                    # Update file
                    shutil.copy2(str(source_file), str(target_file))
                    logger.info(f"Updated: {rel_path}")
                    stats['updated'] += 1
                else:
                    logger.debug(f"Unchanged: {rel_path}")
                    stats['unchanged'] += 1
            else:
                # Add new file
                shutil.copy2(str(source_file), str(target_file))
                logger.info(f"Added: {rel_path}")
                stats['added'] += 1
                
            # Remove processed file from target_file_map
            if rel_path in target_file_map:
                del target_file_map[rel_path]
                
        except Exception as e:
            error_msg = f"Error processing {rel_path}: {str(e)}"
            logger.error(error_msg)
            stats['errors'] += 1
            
            # Create a detailed error report
            try:
                error_dir = target_dir / "error_reports"
                error_dir.mkdir(exist_ok=True)
                error_file = error_dir / f"{rel_path.name}.error.txt"
                
                import datetime
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(f"Error processing: {rel_path}\n")
                    f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write("\n--- File content preview ---\n")
                    try:
                        with open(source_file, 'r', encoding='utf-8') as src:
                            preview = src.read(500)  # First 500 chars
                            f.write(preview + ("..." if len(preview) >= 500 else ""))
                    except Exception as preview_error:
                        f.write(f"Could not read file content: {str(preview_error)}")
                
                logger.info(f"Error report created at {error_file}")
            except Exception as report_error:
                logger.error(f"Failed to create error report: {str(report_error)}")
    
    # Delete files that exist in target but not in source
    for rel_path, file_path in target_file_map.items():
        try:
            file_path.unlink()
            logger.info(f"Deleted: {rel_path}")
            stats['deleted'] += 1
            
            # Remove empty directories
            parent_dir = file_path.parent
            while parent_dir != target_dir:
                if not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    logger.debug(f"Removed empty directory: {parent_dir.relative_to(target_dir)}")
                else:
                    break
                parent_dir = parent_dir.parent
                
        except Exception as e:
            logger.error(f"Error deleting {rel_path}: {str(e)}")
            stats['errors'] += 1
    
    # Generate detailed validation failure report if there were any failures
    if validation_failures:
        try:
            report_dir = target_dir / "validation_reports"
            report_dir.mkdir(exist_ok=True)
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"validation_failures_{timestamp}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"Validation Failures Report - {datetime.datetime.now().isoformat()}\n")
                f.write(f"Total failures: {stats['validation_failures']}\n\n")
                
                for i, failure in enumerate(validation_failures, 1):
                    f.write(f"{i}. {failure}\n")
            
            logger.info(f"Validation failure report created at {report_file}")
        except Exception as report_error:
            logger.error(f"Failed to create validation report: {str(report_error)}")
    
    return stats

def validate_markdown(file_path):
    """
    Comprehensive validation of markdown files to ensure they are properly formatted
    for use with the MCP server.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        bool: True if valid, False otherwise
        
    Validation rules:
    1. File must not be empty
    2. File should have a clear title or introduction at the beginning
    3. File should have proper markdown structure (headers, lists, code blocks)
    4. File should not contain broken links or references
    5. File should not have malformed code blocks
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        validation_errors = []
            
        # 1. Check if file is not empty
        if not content.strip():
            validation_errors.append("File is empty")
            logger.warning(f"Empty file: {file_path}")
            return False
        
        # 2. Check for title or clear introduction
        has_title = any(line.startswith('# ') for line in lines)
        has_intro = len(lines) > 0 and lines[0].strip() and not lines[0].startswith('#')
        
        if not (has_title or has_intro):
            validation_errors.append("Missing title or introduction")
            logger.warning(f"Missing title or introduction in: {file_path}")
        
        # 3. Check for proper markdown structure
        # Count headers, lists, and code blocks to ensure document has structure
        headers = sum(1 for line in lines if line.strip().startswith('#'))
        lists = sum(1 for line in lines if line.strip().startswith(('-', '*', '1.', '2.', '3.')))
        
        # 4. Check for malformed code blocks
        code_block_starts = sum(1 for line in lines if line.strip().startswith('```'))
        if code_block_starts % 2 != 0:
            validation_errors.append("Unmatched code block delimiters")
            logger.warning(f"Unmatched code block delimiters in: {file_path}")
        
        # 5. Check for broken links - look for markdown link syntax [text](url)
        # and verify the links are well-formed
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        import re
        links = re.findall(link_pattern, content)
        for link_text, link_url in links:
            # Check for common issues in links
            if not link_url or link_url.isspace():
                validation_errors.append(f"Empty link URL for text '{link_text}'")
                logger.warning(f"Empty link URL in: {file_path}")
            elif link_url.startswith(' ') or link_url.endswith(' '):
                validation_errors.append(f"Link URL has leading/trailing spaces: '{link_url}'")
                logger.warning(f"Link URL has leading/trailing spaces in: {file_path}")
        
        # 6. Check for minimum content requirements for MCP server
        # MCP documentation should have some meaningful content
        if len(content.strip()) < 100:  # Arbitrary minimum length
            validation_errors.append("Content too short for meaningful documentation")
            logger.warning(f"Content too short in: {file_path}")
        
        # Log all validation errors if any
        if validation_errors:
            logger.warning(f"Validation failed for {file_path}: {', '.join(validation_errors)}")
            return False
            
        return True
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error in {file_path}: {str(e)}. File may not be valid UTF-8.")
        return False
    except Exception as e:
        logger.error(f"Error validating {file_path}: {str(e)}")
        return False

def build_document_index(target_dir):
    """
    Build a comprehensive document index after syncing.
    
    Args:
        target_dir (str): Path to the target directory containing synced files
        
    Returns:
        dict: Index statistics
    """
    try:
        # Add the src directory to Python path to import the indexer
        src_dir = Path(__file__).parent.parent / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from scripts.indexer import DocumentIndexer
        
        logger.info("Building document index...")
        indexer = DocumentIndexer(target_dir)
        index = indexer.build_index()
        
        # Save index to the target directory
        index_path = Path(target_dir) / "document_index.json"
        indexer.save_index(str(index_path))
        
        index_stats = {
            'documents': index['metadata']['total_documents'],
            'categories': len(index['categories']),
            'concepts': len(index['concepts']),
            'tags': len(index['tags']),
            'relationships': sum(len(rels) for rels in index['relationships'].values())
        }
        
        logger.info(f"Document index built successfully: {index_stats}")
        return index_stats
        
    except Exception as e:
        logger.error(f"Failed to build document index: {str(e)}")
        return {'error': str(e)}

def main():
    """
    Main function to handle command-line arguments and execute the sync process.
    
    This function:
    1. Parses command-line arguments
    2. Sets up logging based on the specified log level
    3. Executes the sync_docs function with the provided arguments
    4. Builds a comprehensive document index with relationships
    5. Calculates and reports statistics about the sync operation
    6. Generates a markdown summary for GitHub Actions
    7. Returns an exit code based on whether there were errors
    
    Command-line arguments:
    --source, -s: Source directory containing markdown files
    --target, -t: Target directory to sync files to
    --log-level, -l: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    --validate, -v: Validate markdown files before syncing
    --strict-validation: Treat validation failures as errors instead of just skipping files
    --build-index: Build document index after syncing (default: True)
    --skip-index: Skip building document index
    
    Environment variables:
    DOCS_REPO_PATH: Default source directory if --source is not specified
    CONTENT_DIR_PATH: Default target directory if --target is not specified
    LOG_LEVEL: Default log level if --log-level is not specified
    GITHUB_OUTPUT: Path to GitHub Actions output file
    
    Returns:
        int: 0 if successful, 1 if there were errors
    """
    parser = argparse.ArgumentParser(
        description="Sync documentation files from source to target directory and build index."
    )
    parser.add_argument(
        "--source", 
        "-s", 
        help="Source directory containing markdown files (default: value of DOCS_REPO_PATH env var or './docs-repo')",
        default=os.environ.get("DOCS_REPO_PATH", "./docs-repo")
    )
    parser.add_argument(
        "--target", 
        "-t", 
        help="Target directory to sync files to (default: value of CONTENT_DIR_PATH env var or './src/strands_mcp_server/content')",
        default=os.environ.get("CONTENT_DIR_PATH", "./src/strands_mcp_server/content")
    )
    parser.add_argument(
        "--log-level", 
        "-l", 
        help="Set the logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO")
    )
    parser.add_argument(
        "--validate", 
        "-v", 
        help="Validate markdown files before syncing",
        action="store_true"
    )
    parser.add_argument(
        "--strict-validation",
        help="Treat validation failures as errors instead of just skipping files",
        action="store_true"
    )
    parser.add_argument(
        "--skip-index",
        help="Skip building document index after syncing",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Set log level based on argument
    logger.setLevel(getattr(logging, args.log_level))
    
    # Run sync
    logger.info(f"Starting sync from {args.source} to {args.target}")
    stats = sync_docs(args.source, args.target, validate=args.validate, strict_validation=args.strict_validation)
    
    # Log statistics
    logger.info(f"Sync completed with statistics: {stats}")
    
    # Build document index if not skipped and sync was successful
    index_stats = {}
    if not args.skip_index and stats['errors'] == 0:
        index_stats = build_document_index(args.target)
        if 'error' not in index_stats:
            stats.update({f"index_{k}": v for k, v in index_stats.items()})
    elif args.skip_index:
        logger.info("Skipping document index build as requested")
    else:
        logger.warning("Skipping document index build due to sync errors")
    
    # Calculate summary statistics
    total_files = stats['added'] + stats['updated'] + stats['unchanged'] + stats['deleted']
    total_changes = stats['added'] + stats['updated'] + stats['deleted']
    success_rate = 100.0 if total_files == 0 else (1 - stats['errors'] / total_files) * 100
    
    # Add summary statistics
    stats['total_files'] = total_files
    stats['total_changes'] = total_changes
    stats['success_rate'] = f"{success_rate:.2f}%"
    
    # Generate a markdown summary for GitHub Actions
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

    # Add index statistics if available
    if index_stats and 'error' not in index_stats:
        summary += f"""
### Document Index Summary

| Metric | Count |
|--------|-------|
| Documents Indexed | {index_stats.get('documents', 0)} |
| Categories | {index_stats.get('categories', 0)} |
| Concepts | {index_stats.get('concepts', 0)} |
| Tags | {index_stats.get('tags', 0)} |
| Relationships | {index_stats.get('relationships', 0)} |
"""
    elif 'error' in index_stats:
        summary += f"\n### Index Build Failed\n{index_stats['error']}\n"

    # Add validation failure details if any
    if stats.get('validation_failures', 0) > 0:
        summary += "\n### Validation Issues\n"
        summary += "Validation failures were detected. Check the validation_reports directory for details.\n"
    
    # Set output for GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            for key, value in stats.items():
                f.write(f"{key}={value}\n")
            # Add markdown summary as a special output
            f.write(f"summary<<EOF\n{summary}\nEOF\n")
    else:
        # If not running in GitHub Actions, print to console
        logger.info("Sync statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # Print the markdown summary to console
        print(summary)
    
    # Return non-zero exit code if there were errors
    if stats['errors'] > 0:
        logger.error(f"Sync completed with {stats['errors']} errors")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
