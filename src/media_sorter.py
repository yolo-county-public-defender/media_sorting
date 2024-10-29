import os
import shutil
import mimetypes
import zipfile
import tempfile
from pathlib import Path
from typing import Set, Dict, List
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
import json

class MediaSorter:
    def __init__(self, source_dir: str, backup_dir: str):
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.console = Console()
        self.operations_log: List[Dict] = []
        
        # Define media file extensions
        self.media_extensions: Set[str] = {
            # Video
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
            # Audio
            '.mp3', '.wav', '.flac', '.m4a', '.aac',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'
        }

        # Add zip to non-media types we want to process specially
        self.zip_extensions = {'.zip', '.ZIP'}

    def is_media_file(self, file_path: Path) -> bool:
        """Check if file is a media file based on extension and mime type."""
        if file_path.suffix.lower() in self.media_extensions:
            return True
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type and mime_type.startswith(('video/', 'audio/', 'image/'))

    def calculate_total_size(self, path: Path) -> int:
        """Calculate total size of non-media files."""
        total = 0
        self.console.print("[yellow]Calculating total size...[/yellow]")
        for item in path.rglob('*'):
            if item.is_file():
                if item.suffix in self.zip_extensions:
                    self.console.print(f"Found zip: {item}")
                    total += item.stat().st_size * 2  # Account for extracted contents
                elif not self.is_media_file(item):
                    total += item.stat().st_size
        self.console.print(f"[green]Total size to process: {total / 1024 / 1024:.2f} MB[/green]")
        return total

    def dry_run(self) -> List[Dict]:
        """Simulate the operation and return planned actions."""
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

    def process_zip_file(self, zip_path: Path, relative_path: Path) -> List[Dict]:
        """Process a zip file and any nested zip files within it."""
        operations = []
        
        # Add debug output
        self.console.print(f"[yellow]Processing zip: {zip_path}[/yellow]")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract zip file
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Show zip contents before extraction
                    self.console.print(f"[blue]Zip contains {len(zip_ref.namelist())} files[/blue]")
                    zip_ref.extractall(temp_path)
            except Exception as e:
                self.console.print(f"[red]Error extracting {zip_path}: {e}[/red]")
                return operations
            
            # Process extracted files
            for item in temp_path.rglob('*'):
                if item.is_file():
                    self.console.print(f"[cyan]Processing extracted file: {item.name}[/cyan]")
                    if item.suffix in self.zip_extensions:
                        # Found a nested zip file
                        self.console.print(f"[yellow]Found nested zip: {item.name}[/yellow]")
                        nested_rel_path = item.relative_to(temp_path)
                        nested_ops = self.process_zip_file(
                            item, 
                            relative_path.parent / 'unzipped' / zip_path.stem / nested_rel_path
                        )
                        operations.extend(nested_ops)
                    elif not self.is_media_file(item):
                        # Handle non-media files
                        rel_path = item.relative_to(temp_path)
                        new_path = self.backup_dir / relative_path.parent / 'unzipped' / zip_path.stem / rel_path
                        
                        # Create parent directories
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file
                        try:
                            shutil.copy2(item, new_path)
                            operations.append({
                                'timestamp': datetime.now().isoformat(),
                                'action': 'extract_and_copy',
                                'source': f"{zip_path}::{rel_path}",
                                'destination': str(new_path),
                                'status': 'success'
                            })
                        except Exception as e:
                            self.console.print(f"[red]Error copying {item}: {e}[/red]")
                            operations.append({
                                'timestamp': datetime.now().isoformat(),
                                'action': 'error',
                                'source': f"{zip_path}::{rel_path}",
                                'error': str(e)
                            })
        
        return operations

    def process_directory(self, dry_run: bool = False) -> None:
        try:
            """Main processing function."""
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # First, do a dry run and show planned operations
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
                    if item.is_file():
                        rel_path = item.relative_to(self.source_dir)
                        
                        # Check if it's a zip file
                        if item.suffix in self.zip_extensions:
                            try:
                                # Process zip file contents
                                zip_ops = self.process_zip_file(item, rel_path)
                                self.operations_log.extend(zip_ops)
                                
                                # Update progress
                                file_size = item.stat().st_size
                                processed_size += file_size
                                progress.update(task, completed=processed_size)
                                
                                # Delete original zip after processing
                                item.unlink()
                                
                                # Log the operation
                                self.operations_log.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'action': 'process_zip',
                                    'source': str(item),
                                    'status': 'success'
                                })
                                
                            except Exception as e:
                                self.operations_log.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'action': 'error_zip',
                                    'source': str(item),
                                    'error': str(e)
                                })
                                self.console.print(f"[red]Error processing zip file {item}: {e}[/red]")
                                
                        elif not self.is_media_file(item):
                            try:
                                # Handle non-media files
                                dest_path = self.backup_dir / rel_path
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Copy the file
                                shutil.copy2(item, dest_path)
                                
                                # Update progress
                                file_size = item.stat().st_size
                                processed_size += file_size
                                progress.update(task, completed=processed_size)
                                
                                # Log the operation
                                self.operations_log.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'action': 'move',
                                    'source': str(item),
                                    'destination': str(dest_path),
                                    'status': 'success'
                                })
                                
                                # Delete original file after successful copy
                                item.unlink()
                                
                            except Exception as e:
                                self.operations_log.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'action': 'error',
                                    'source': str(item),
                                    'error': str(e)
                                })
                                self.console.print(f"[red]Error processing file {item}: {e}[/red]")

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
            # Force exit
            import sys
            sys.exit(1)

if __name__ == "__main__":
    # Example usage
    source_directory = "/Volumes/Extreme SSD"
    backup_directory = "/Volumes/Extreme SSD/NonMedia"
    
    sorter = MediaSorter(source_directory, backup_directory)
    
    # Run dry-run first
    sorter.process_directory(dry_run=True)
    
    # If everything looks good, run the actual process
    if input("\nRun actual process? (y/n): ").lower().startswith('y'):
        sorter.process_directory(dry_run=False)
