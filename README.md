# Media Sorter

A Python utility that helps organize files by separating media and non-media content. It handles unzipping of archives and moves non-media files to a backup location while preserving the original directory structure.

## Features

- Automatically extracts ZIP files in their original locations
- Identifies media files based on extensions and MIME types
- Moves non-media files to a backup location
- Preserves original directory structure
- Provides progress tracking and logging
- Includes dry-run capability to preview operations

## Supported Media Formats

- **Video**: mp4, avi, mov, mkv, wmv, flv
- **Audio**: mp3, wav, flac, m4a, aac
- **Images**: jpg, jpeg, png, gif, bmp, tiff

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Steps

1. Clone this repository or download the script:

```bash
git clone <repository_url>
```

2. Create and activate a virtual environment (recommended):

#### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

If requirements.txt is not available, install the following packages:

```bash
pip install rich pathlib typing
```

Note: Some packages like `os`, `shutil`, `mimetypes`, `zipfile`, `tempfile`, `datetime`, and `json` are part of Python's standard library and don't need to be installed separately.

## Configuration

By default, the script is configured to:

- Source Directory: `/Volumes/Extreme SSD`
- Backup Directory: `/Volumes/Extreme SSD/NonMedia`

To change these locations, edit the following lines at the bottom of `media_sorter.py`:

```python
source_directory = "/Volumnes/Extreme SSD" # Change this to your source directory
backup_directory = "/Volumes/Extreme SSD/NonMedia" # Change this to your backup directory
```

### Path Examples

#### Windows:

```python
source_directory = "C:\\Users\\YourUsername\\Documents"
backup_directory = "D:\\Backup\\NonMedia"
```

#### macOS/Linux:

```python
source_directory = "/Users/yourusername/Documents"
backup_directory = "/Users/yourusername/Backup/NonMedia"
```

## Usage

1. Open a terminal/command prompt
2. Navigate to the src directory
3. Run the script:

```bash
python media_sorter.py
```

The script will:

1. Perform a dry run first, showing what files would be moved
2. Ask for confirmation before proceeding
3. Extract any ZIP files in their original locations
4. Move non-media files to the backup directory
5. Generate an operations log in the backup directory

## Operation Logs

The script generates two types of logs in the backup directory:

- `operations_log.json`: Complete log of all operations
- `operations_log_interrupted.json`: Created if the script is interrupted

## Safety Features

- Dry run preview before actual operations
- User confirmation required before processing
- Progress tracking with size calculations
- Error logging and handling
- Preservation of directory structure
- Original files are moved, not copied (saves space)

## Troubleshooting

### Common Issues

1. **Permission Errors**

   - Ensure you have read/write permissions for both source and backup directories
   - Try running with elevated privileges if necessary

2. **Path Too Long** (Windows)

   - Use shorter directory names
   - Move directories closer to root

3. **File in Use**
   - Close any applications that might be using the files
   - Try running the script again

### Error Logs

Check the operations log files in the backup directory for detailed error information.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

[Your License Here]

## Disclaimer

Always backup important data before running file organization scripts. While this script is designed to be safe, unforeseen circumstances can occur.
