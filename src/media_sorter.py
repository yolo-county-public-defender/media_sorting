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

    def unzip_directory(self) -> None:
        """First pass: Unzip all zip files in the directory."""
        self.console.print("[yellow]Starting unzip phase...[/yellow]")
        
        zip_files = list(self.source_dir.rglob('*.zip')) + list(self.source_dir.rglob('*.ZIP'))
        
        if not zip_files:
            self.console.print("[green]No zip files found.[/green]")
            return

        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
        ) as progress:
            unzip_task = progress.add_task("[cyan]Unzipping files...", total=len(zip_files))
            
            for zip_path in zip_files:
                try:
                    rel_path = zip_path.relative_to(self.source_dir)
                    extract_dir = zip_path.parent / zip_path.stem
                    
                    self.console.print(f"[yellow]Unzipping: {zip_path}[/yellow]")
                    
                    # Extract the zip file
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # Delete the original zip file after successful extraction
                    zip_path.unlink()
                    
                    self.operations_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'unzip',
                        'source': str(zip_path),
                        'destination': str(extract_dir),
                        'status': 'success'
                    })
                    
                except Exception as e:
                    self.console.print(f"[red]Error unzipping {zip_path}: {e}[/red]")
                    self.operations_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'unzip_error',
                        'source': str(zip_path),
                        'error': str(e)
                    })
                
                progress.update(unzip_task, advance=1)

        self.console.print("[green]Unzip phase complete![/green]")

    def calculate_total_size(self, path: Path) -> int:
        """Calculate total size of non-media files."""
        total = 0
        self.console.print("[yellow]Calculating total size...[/yellow]")
        for item in path.rglob('*'):
            if item.is_file() and not self.is_media_file(item):
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

    def process_directory(self, dry_run: bool = False) -> None:
        """Main processing function."""
        try:
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # First, handle all zip files
            if not dry_run:
                self.unzip_directory()

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
                    if item.is_file() and not self.is_media_file(item):
                        try:
                            rel_path = item.relative_to(self.source_dir)
                            dest_path = self.backup_dir / rel_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Move the file instead of copy+delete
                            shutil.move(str(item), str(dest_path))
                            
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
            # Exit the entire Python process
            os._exit(1)  # Using os._exit() instead of sys.exit()

if __name__ == "__main__":
    try:
        # Example usage
        source_directory = "/Volumes/Extreme SSD"
        backup_directory = "/Volumes/Extreme SSD/NonMedia"
        
        sorter = MediaSorter(source_directory, backup_directory)
        
        # Run dry-run first
        sorter.process_directory(dry_run=True)
        
        # If everything looks good, run the actual process
        if input("\nRun actual process? (y/n): ").lower().startswith('y'):
            sorter.process_directory(dry_run=False)
    
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        os._exit(1)
