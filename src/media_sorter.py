# Standard library imports
import os
import shutil
import mimetypes
import zipfile
from pathlib import Path
from typing import Set, Dict, List
from datetime import datetime

# Third-party imports for console UI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
import json

class MediaSorter:
    """
    A class to sort and organize files by separating media and non-media content.
    Handles unzipping of archives and moving non-media files to a backup location.
    """
    
    def __init__(self, source_dir: str, backup_dir: str):
        """
        Initialize the MediaSorter with source and backup directories.
        
        Args:
            source_dir (str): Path to the source directory containing files to sort
            backup_dir (str): Path where non-media files will be moved
        """
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.console = Console()  # Rich console for prettier output
        self.operations_log: List[Dict] = []  # Track all operations performed
        
        # Define known media file extensions for quick lookup
        self.media_extensions: Set[str] = {
            # Video formats
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 
            # Audio formats
            '.mp3', '.wav', '.flac', '.m4a', '.aac',
            # Image formats
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'
        }

        # Zip files need special handling (extraction before processing)
        self.zip_extensions = {'.zip', '.ZIP'}

        # Add new attribute to track person-level directories
        self.person_dirs = {path for path in self.source_dir.iterdir() if path.is_dir()}

    def is_media_file(self, file_path: Path) -> bool:
        """
        Determine if a file is a media file based on extension and MIME type.
        
        Args:
            file_path (Path): Path to the file to check
            
        Returns:
            bool: True if file is a media file, False otherwise
        """
        # First check extension for quick determination
        if file_path.suffix.lower() in self.media_extensions:
            return True
        # If extension check fails, try MIME type for deeper inspection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type and mime_type.startswith(('video/', 'audio/', 'image/'))

    def unzip_directory(self) -> None:
        """
        First processing phase: Extract all zip files recursively until no more are found.
        Deletes original zip files after successful extraction.
        """
        self.console.print("[yellow]Starting unzip phase...[/yellow]")
        
        while True:
            # Find all zip files recursively in source directory
            zip_files = list(self.source_dir.rglob('*.zip')) + list(self.source_dir.rglob('*.ZIP'))
            
            if not zip_files:
                self.console.print("[green]No more zip files found.[/green]")
                break

            total_files = len(zip_files)
            self.console.print(f"[yellow]Found {total_files} zip files to process...[/yellow]")
            
            # Setup progress bar for current batch of zip files
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            ) as progress:
                unzip_task = progress.add_task(
                    f"[cyan]Unzipping {total_files} files...", 
                    total=total_files
                )
                
                # Process each zip file
                for index, zip_path in enumerate(zip_files, 1):
                    try:
                        # Skip if the zip file is in the backup directory
                        if str(zip_path).startswith(str(self.backup_dir)):
                            progress.advance(unzip_task)
                            continue
                        
                        # Update description to show current file
                        progress.update(
                            unzip_task,
                            description=f"[cyan]Unzipping ({index}/{total_files}): {zip_path.name}"
                        )
                        
                        # Create extraction directory next to zip file
                        extract_dir = zip_path.parent / zip_path.stem
                        
                        # Ensure extraction directory exists
                        extract_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Extract contents
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                        
                        # Remove original zip file to save space
                        zip_path.unlink()
                        
                        # Log successful operation
                        self.operations_log.append({
                            'timestamp': datetime.now().isoformat(),
                            'action': 'unzip',
                            'source': str(zip_path),
                            'destination': str(extract_dir),
                            'status': 'success'
                        })
                        
                        # Update progress
                        progress.advance(unzip_task)
                        
                    except Exception as e:
                        # Log failed operation
                        self.console.print(f"[red]Error unzipping {zip_path}: {e}[/red]")
                        self.operations_log.append({
                            'timestamp': datetime.now().isoformat(),
                            'action': 'unzip_error',
                            'source': str(zip_path),
                            'error': str(e)
                        })
                        
                        # Still advance progress even on error
                        progress.advance(unzip_task)

        self.console.print("[green]Unzip phase complete![/green]")

    def calculate_total_size(self, path: Path) -> int:
        """
        Calculate total size of all non-media files for progress tracking.
        
        Args:
            path (Path): Directory to scan
            
        Returns:
            int: Total size in bytes
        """
        total = 0
        self.console.print("[yellow]Calculating total size...[/yellow]")
        for item in path.rglob('*'):
            if item.is_file() and not self.is_media_file(item):
                total += item.stat().st_size
        self.console.print(f"[green]Total size to process: {total / 1024 / 1024:.2f} MB[/green]")
        return total

    def dry_run(self) -> List[Dict]:
        """
        Simulate the move operation without actually moving files.
        
        Returns:
            List[Dict]: List of planned file movements
        """
        planned_operations = []
        for item in self.source_dir.rglob('*'):
            if item.is_file() and not self.is_media_file(item):
                rel_path = item.relative_to(self.source_dir)
                planned_operations.append({
                    'action': 'move',
                    'source': str(item),
                    'destination': str(self.backup_dir / rel_path)
                })
        return planned_operations

    def process_file(self, item: Path) -> bool:
        """
        Process a single file, moving it if it's a non-media file.
        
        Args:
            item (Path): Path to the file to process
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            rel_path = item.relative_to(self.source_dir)
            dest_path = self.backup_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file instead of copy+delete
            shutil.move(str(item), str(dest_path))
            
            # Log successful operation
            self.log_operation('move', str(item), destination=str(dest_path))
            return True
            
        except FileNotFoundError:
            # Silently log FileNotFoundError without console output
            self.log_operation('error', str(item), 
                             error=f"[Errno 2] No such file or directory: '{item}'",
                             silent=True)
            return False
            
        except Exception as e:
            # Print and log other types of errors
            self.console.print(f"[red]Error processing file {item}: {e}[/red]")
            self.log_operation('error', str(item), error=str(e))
            return False

    def log_operation(self, action: str, source: str, error: str = None, 
                     destination: str = None, silent: bool = False) -> None:
        """
        Log an operation to the operations log.
        
        Args:
            action (str): Type of action performed
            source (str): Source file path
            error (str, optional): Error message if applicable
            destination (str, optional): Destination path for moves
            silent (bool, optional): Whether to skip logging FileNotFoundError
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'source': source
        }
        
        if error:
            log_entry['error'] = error
        if destination:
            log_entry['destination'] = destination
            log_entry['status'] = 'success'
        
        # Only add to operations log if it's not a silenced FileNotFoundError
        if not (silent and "No such file or directory" in str(error)):
            self.operations_log.append(log_entry)

    def flatten_media_files(self) -> None:
        """
        Flatten all media files into their respective person-level directories.
        Move all non-media files to backup directory.
        """
        self.console.print("[yellow]Starting media file flattening...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
        ) as progress:
            # First pass: Move all media files to person directory root
            media_moves = []
            nonmedia_moves = []
            
            self.console.print("[yellow]Scanning all files...[/yellow]")
            
            # Process each person directory
            for person_dir in self.person_dirs:
                # Recursively find ALL files first
                all_files = list(person_dir.rglob('*'))
                scan_task = progress.add_task(
                    f"[cyan]Scanning {person_dir.name}...",
                    total=len(all_files)
                )
                
                for item in all_files:
                    if item.is_file():
                        if self.is_media_file(item):
                            # Always move media files to person directory root
                            new_path = person_dir / item.name
                            # Handle duplicate filenames
                            counter = 1
                            while new_path.exists():
                                stem = item.stem
                                suffix = item.suffix
                                new_path = person_dir / f"{stem}_{counter}{suffix}"
                                counter += 1
                            media_moves.append((item, new_path))
                        else:
                            # Move non-media files to backup directory
                            rel_path = item.relative_to(self.source_dir)
                            backup_path = self.backup_dir / rel_path
                            nonmedia_moves.append((item, backup_path))
                    progress.advance(scan_task)

            # First move all media files to root
            if media_moves:
                self.console.print(f"[yellow]Moving {len(media_moves)} media files to root...[/yellow]")
                media_task = progress.add_task(
                    "[cyan]Moving media files...",
                    total=len(media_moves)
                )
                
                for old_path, new_path in media_moves:
                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old_path), str(new_path))
                        self.log_operation('flatten_media', str(old_path), destination=str(new_path))
                    except Exception as e:
                        self.console.print(f"[red]Error moving media file {old_path}: {e}[/red]")
                    progress.advance(media_task)

            # Then move all non-media files
            if nonmedia_moves:
                self.console.print(f"[yellow]Moving {len(nonmedia_moves)} non-media files...[/yellow]")
                nonmedia_task = progress.add_task(
                    "[cyan]Moving non-media files...",
                    total=len(nonmedia_moves)
                )
                
                for old_path, new_path in nonmedia_moves:
                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old_path), str(new_path))
                        self.log_operation('move_nonmedia', str(old_path), destination=str(new_path))
                    except Exception as e:
                        self.console.print(f"[red]Error moving non-media file {old_path}: {e}[/red]")
                    progress.advance(nonmedia_task)

            # Finally, clean up empty directories
            self.console.print("[yellow]Cleaning up empty directories...[/yellow]")
            
            # Get all subdirectories in person directories
            all_dirs = set()
            for person_dir in self.person_dirs:
                for dir_path in person_dir.rglob('*'):
                    if dir_path.is_dir():
                        all_dirs.add(dir_path)

            # Sort directories by depth (deepest first)
            sorted_dirs = sorted(all_dirs, 
                               key=lambda x: len(str(x).split(os.sep)), 
                               reverse=True)
            
            cleanup_task = progress.add_task(
                "[cyan]Removing empty directories...",
                total=len(sorted_dirs)
            )
            
            for directory in sorted_dirs:
                try:
                    if directory not in self.person_dirs:  # Don't remove person-level directories
                        # Check if directory contains any files (recursively)
                        has_files = False
                        for _, _, files in os.walk(directory):
                            if files:
                                has_files = True
                                break
                        
                        if not has_files:
                            shutil.rmtree(directory)
                            self.log_operation('remove_directory', str(directory))
                except Exception as e:
                    self.console.print(f"[red]Error removing directory {directory}: {e}[/red]")
                progress.advance(cleanup_task)

        self.console.print("[green]Media file flattening complete![/green]")

    def process_directory(self, dry_run: bool = False) -> None:
        """Main processing function."""
        try:
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Get absolute path of NonMedia directory
            nonmedia_abs_path = os.path.abspath(self.backup_dir)

            # First, handle all zip files
            if not dry_run:
                self.unzip_directory()
                # Add flattening step after unzipping
                self.flatten_media_files()

            # Then do a dry run and show planned operations
            planned_ops = self.dry_run()
            
            if dry_run:
                self.console.print("\n[yellow]Dry run results:[/yellow]")
                for op in planned_ops:
                    self.console.print(f"Would move: {op['source']} -> {op['destination']}")
                return

            # Calculate total size for progress bar
            total_size = self.calculate_total_size(self.source_dir)
            processed_size = 0

            # Confirm with user
            self.console.print(f"\n[yellow]Will process {len(planned_ops)} files.[/yellow]")
            if not input("Continue? (y/n): ").lower().startswith('y'):
                return

            # Process files with progress bar
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task("[cyan]Processing...", total=total_size)

                for item in self.source_dir.rglob('*'):
                    # Skip the NonMedia directory and its contents
                    if str(item).startswith(nonmedia_abs_path):
                        continue
                        
                    if item.is_file() and not self.is_media_file(item):
                        if self.process_file(item):
                            # Update progress only for successful operations
                            try:
                                file_size = item.stat().st_size
                                processed_size += file_size
                                progress.update(task, completed=processed_size)
                            except FileNotFoundError:
                                # Ignore files that disappeared during processing
                                pass

            # Save operations log
            log_file = self.backup_dir / 'operations_log.json'
            with open(log_file, 'w') as f:
                json.dump(self.operations_log, f, indent=2)

            self.console.print("[green]Processing complete![/green]")
            self.console.print(f"[blue]Operations log saved to: {log_file}[/blue]")
            
        except KeyboardInterrupt:
            self.console.print("\n[red]Process interrupted by user. Cleaning up...[/red]")
            # Save partial operations log
            log_file = self.backup_dir / 'operations_log_interrupted.json'
            with open(log_file, 'w') as f:
                json.dump(self.operations_log, f, indent=2)
            self.console.print("[yellow]Partial operations log saved.[/yellow]")
            # Exit the entire Python process
            os._exit(1)  # Using os._exit() instead of sys.exit()

if __name__ == "__main__":
    try:
        # Set up source directory
        source_directory = "/Volumes/Extreme SSD"
        backup_directory = os.path.join(source_directory, "NonMedia")
        
        # Create NonMedia directory if it doesn't exist
        os.makedirs(backup_directory, exist_ok=True)
        
        sorter = MediaSorter(source_directory, backup_directory)
        
        # Run dry-run first
        sorter.process_directory(dry_run=True)
        
        # If everything looks good, run the actual process
        if input("\nRun actual process? (y/n): ").lower().startswith('y'):
            sorter.process_directory(dry_run=False)
    
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        os._exit(1)
