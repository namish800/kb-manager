"""File validation constants and type definitions."""

from typing import Dict, Set

# File size limit in bytes (25MB)
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Supported MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    # PDF
    "application/pdf",
    
    # PowerPoint
    "application/vnd.ms-powerpoint",  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    
    # Word Documents
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    
    # Markdown
    "text/markdown",
    "text/x-markdown",
    "text/plain",  # Often used for .md files
}

# File extension to MIME type mapping
EXTENSION_TO_MIME: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}

# Supported file extensions
ALLOWED_EXTENSIONS: Set[str] = set(EXTENSION_TO_MIME.keys())

# Human-readable file type descriptions
FILE_TYPE_DESCRIPTIONS: Dict[str, str] = {
    ".pdf": "PDF Document",
    ".ppt": "PowerPoint Presentation (Legacy)",
    ".pptx": "PowerPoint Presentation",
    ".doc": "Word Document (Legacy)",
    ".docx": "Word Document",
    ".md": "Markdown Document",
    ".markdown": "Markdown Document",
}


def get_extension_from_filename(filename: str) -> str:
    """Extract file extension from filename (lowercase)."""
    if "." not in filename:
        return ""
    return filename.lower().split(".")[-1] if "." in filename else ""


def get_full_extension_from_filename(filename: str) -> str:
    """Extract full file extension including the dot (lowercase)."""
    if "." not in filename:
        return ""
    extension = "." + get_extension_from_filename(filename)
    return extension


def is_supported_file_type(filename: str) -> bool:
    """Check if filename has a supported extension."""
    extension = get_full_extension_from_filename(filename)
    return extension in ALLOWED_EXTENSIONS


def get_expected_mime_type(filename: str) -> str:
    """Get expected MIME type for a filename."""
    extension = get_full_extension_from_filename(filename)
    return EXTENSION_TO_MIME.get(extension, "application/octet-stream")


def is_valid_mime_type(mime_type: str) -> bool:
    """Check if MIME type is supported."""
    return mime_type in ALLOWED_MIME_TYPES


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_file_type_description(filename: str) -> str:
    """Get human-readable description of file type."""
    extension = get_full_extension_from_filename(filename)
    return FILE_TYPE_DESCRIPTIONS.get(extension, "Unknown file type") 