# 📂 Media Sorter

A Python utility that helps organize files by separating media and non-media content. It handles unzipping of archives and moves non-media files to a backup location while flattening media files into their respective person-level directories.

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Quick Start

```bash
git clone <repository_url>
cd media-sorter
pip install -r requirements.txt
python src/media_sorter.py
```

## ✨ Features

- 📦 Automatically extracts all ZIP files recursively (including nested ZIPs)
- 📂 Flattens media files to their respective person-level directories
- 🖼️ Identifies media files based on extensions and MIME types
- 🗂️ Moves non-media files and folders to a backup location
- 🔄 Preserves directory structure for non-media content
- 📈 Provides progress tracking and logging
- 🧪 Includes dry-run capability to preview operations

## 🛠️ How It Works

1. **Initialization**

   - Creates a 'NonMedia' directory in the source location if it doesn't exist
   - Identifies person-level directories
   - Sets up logging and progress tracking

2. **Unzip Phase**

   - Recursively finds all ZIP files in source directory
   - Extracts them in their original location
   - Continues until no more ZIP files are found
   - Deletes original ZIP files to save space

3. **Media Flattening Phase**

   - Scans all files in person-level directories
   - Moves media files to the root of their respective person directory
   - Moves non-media files and folders to backup location

4. **Cleanup Phase**
   - Removes empty directories
   - Preserves person-level directory structure

## 📁 Example File Organization

**Before:**

```
/Source
├── Person1
│   ├── Documents.zip
│   ├── vacation
│   │   ├── photos
│   │   │   ├── beach.jpg
│   │   │   └── sunset.mp4
│   │   ├── info.txt
│   │   └── map.pdf
│   └── work
│       ├── report.docx
│       └── presentation.mp4
└── Person2
    └── ...
```

**After:**

```
/Source
├── Person1
│   ├── beach.jpg
│   ├── sunset.mp4
│   └── presentation.mp4
├── Person2
│   └── ...
└── NonMedia
    └── Person1
        ├── Documents/
        ├── vacation
        │   ├── info.txt
        │   └── map.pdf
        └── work
            └── report.docx
```

## 📥 Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Steps

1. Clone this repository or download the script:

```bash
git clone https://github.com/yolo-county-public-defender/media_sorting.git
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

If `requirements.txt` is not available, install the following packages:

```bash
pip install rich pathlib typing
```

Note: Some packages like `os`, `shutil`, `mimetypes`, `zipfile`, `tempfile`, `datetime`, and `json` are part of Python's standard library and don't need to be installed separately.

## ⚙️ Configuration

By default, the script is configured to:

- **Source Directory**: `/Volumes/Extreme SSD`
- **Backup Directory**: `/Volumes/Extreme SSD/NonMedia` (automatically created if it doesn't exist)

To change these locations, edit the following lines at the bottom of `media_sorter.py`:

```python
source_directory = "/Volumes/Extreme SSD" # Change this to your source directory
```

The backup directory will automatically be created as a 'NonMedia' subdirectory within your source directory.

### Path Examples

#### Windows:

```python
source_directory = "C:\\Users\\YourUsername\\Documents"
```

#### macOS/Linux:

```python
source_directory = "/Users/yourusername/Documents"
```

## 🏃 Usage

1. Open a terminal/command prompt
2. Navigate to the src directory
3. Run the script:

```bash
python media_sorter.py
```

The script will:

1. Create the NonMedia backup directory if it doesn't exist
2. Perform a dry run first, showing what files would be moved
3. Ask for confirmation before proceeding
4. Extract any ZIP files in their original locations
5. Move non-media files to the backup directory
6. Generate an operations log in the backup directory

## 📜 Operation Logs

The script generates two types of logs in the backup directory:

- `operations_log.json`: Complete log of all operations
- `operations_log_interrupted.json`: Created if the script is interrupted

## 🛡️ Safety Features

- Dry run preview before actual operations
- User confirmation required before processing
- Progress tracking with size calculations
- Error logging and handling
- Preservation of directory structure
- Original files are moved, not copied (saves space)

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Errors**

   - Ensure you have read/write permissions for the source directory
   - The script needs permissions to create the backup directory if it doesn't exist
   - Try running with elevated privileges if necessary

2. **Path Too Long** (Windows)

   - Use shorter directory names
   - Move directories closer to root

3. **File in Use**
   - Close any applications that might be using the files
   - Try running the script again

### Error Logs

Check the operations log files in the backup directory for detailed error information.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## ⚠️ Disclaimer

Always backup important data before running file organization scripts. While this script is designed to be safe, unforeseen circumstances can occur.
