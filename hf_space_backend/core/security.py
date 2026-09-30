"""
TRINETRA — Security & Input Hardening Engine
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Production-grade security validation:
1. Filename sanitization (path traversal, control characters, Windows reserved names)
2. Path validation (canonical root containment, symlink traversal prevention)
3. MIME / magic bytes verification (GeoTIFF, PNG, JPEG, HDF5, NetCDF, MAT, ZIP)
4. Decompression limits (zip bombs, ratio bombs, symlink archives)
5. File size limits
6. Safe subprocess execution (shell=False, binary whitelisting)
"""

import os
import re
import zipfile
import tarfile
import subprocess
from typing import List, Tuple, Dict, Any, Optional, Union

from core.exceptions import SecurityViolationError


class SecurityValidator:
    """Central security and input validation engine for TRINETRA."""

    # Whitelist of allowed extensions for remote sensing, imagery, and tabular data
    ALLOWED_EXTENSIONS = {
        ".tif", ".tiff", ".geotiff",
        ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".jp2",
        ".mat", ".h5", ".hdf5", ".nc", ".hdr", ".dat", ".img",
        ".npy", ".npz",
        ".json", ".csv",
        ".zip", ".tar", ".gz"
    }

    # Blacklist of dangerous executable / script extensions
    DANGEROUS_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".sh", ".bash", ".zsh",
        ".ps1", ".py", ".pyw", ".dll", ".so", ".dylib",
        ".vbs", ".js", ".jse", ".wsf", ".wsh", ".msi",
        ".scr", ".pif", ".com", ".hta", ".cpl", ".jar"
    }

    # Reserved Windows device names
    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }

    # Magic byte signatures
    MAGIC_SIGNATURES = {
        "tiff_le": b"II*\x00",
        "tiff_be": b"MM\x00*",
        "bigtiff_le": b"II+\x00",
        "bigtiff_be": b"MM\x00+",
        "png": b"\x89PNG\r\n\x1a\n",
        "jpeg": b"\xff\xd8\xff",
        "hdf5": b"\x89HDF\r\n\x1a\n",
        "netcdf_classic": b"CDF\x01",
        "netcdf_64bit": b"CDF\x02",
        "zip": b"PK\x03\x04",
        "zip_empty": b"PK\x05\x06",
        "zip_spanned": b"PK\x07\x08",
        "gzip": b"\x1f\x8b",
        "npy": b"\x93NUMPY"
    }

    # Whitelist of binaries permitted in safe_subprocess_run
    DEFAULT_ALLOWED_BINARIES = {"git", "python", "python3", "pytest"}

    # =========================================================================
    # 1. Filename Sanitization & Path Traversal Validation
    # =========================================================================

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitizes an untrusted filename, stripping directory traversal tokens,
        control characters, null bytes, and Windows reserved names.
        Raises SecurityViolationError if filename is malicious or empty.
        """
        if not filename or not isinstance(filename, str):
            raise SecurityViolationError("Filename must be a non-empty string.")

        # Check for null bytes
        if "\x00" in filename:
            raise SecurityViolationError("Null byte detected in filename.")

        # Strip directory separators and extract basename
        cleaned = os.path.basename(filename.replace("\\", "/"))

        # Check for traversal attempts
        if ".." in cleaned or cleaned.startswith("."):
            cleaned = re.sub(r"^\.+", "", cleaned)
            cleaned = cleaned.replace("..", "")

        # Remove control characters and problematic characters
        cleaned = re.sub(r"[\x00-\x1f\x7f<>:\"/\\|?*]", "_", cleaned).strip()

        if not cleaned:
            raise SecurityViolationError(f"Sanitization resulted in an empty filename from '{filename}'.")

        # Check Windows reserved names (e.g. CON.txt, NUL)
        base_stem = os.path.splitext(cleaned)[0].upper()
        if base_stem in cls.WINDOWS_RESERVED_NAMES:
            cleaned = f"safe_{cleaned}"

        return cleaned

    @classmethod
    def validate_file_path(cls, file_path: str, allowed_dirs: List[str]) -> str:
        """
        Ensures the canonical resolved path resides strictly inside one of the allowed directories.
        Raises SecurityViolationError if path traversal or directory escaping is detected.
        """
        if not file_path or not isinstance(file_path, str):
            raise SecurityViolationError("File path must be a non-empty string.")

        if "\x00" in file_path:
            raise SecurityViolationError("Null byte detected in file path.")

        canonical_path = os.path.realpath(os.path.abspath(file_path))
        canonical_allowed = [os.path.realpath(os.path.abspath(d)) for d in allowed_dirs]

        # Check containment
        is_contained = any(
            os.path.commonpath([canonical_path, d]) == d
            for d in canonical_allowed
        )

        if not is_contained:
            raise SecurityViolationError(
                f"Path traversal detected: '{file_path}' resolves outside allowed directories."
            )

        return canonical_path

    # =========================================================================
    # 2. File Type, Magic Byte & Size Validation
    # =========================================================================

    @classmethod
    def validate_file_type_and_size(
        cls,
        file_source: Union[str, bytes],
        filename: str,
        max_size_bytes: int = 500 * 1024 * 1024
    ) -> Tuple[bool, str]:
        """
        Validates file extension, inspects binary magic bytes, and enforces size bounds.
        Accepts a file path string or raw byte buffer.
        Raises SecurityViolationError on violation.
        """
        safe_name = cls.sanitize_filename(filename)
        _, ext = os.path.splitext(safe_name.lower())

        if ext in cls.DANGEROUS_EXTENSIONS:
            raise SecurityViolationError(f"Prohibited executable/script extension '{ext}' in file '{filename}'.")

        if ext not in cls.ALLOWED_EXTENSIONS:
            raise SecurityViolationError(f"Unsupported file extension '{ext}' for remote sensing data.")

        # Read header bytes and calculate size
        if isinstance(file_source, bytes):
            size = len(file_source)
            header = file_source[:16]
        elif isinstance(file_source, str):
            if not os.path.isfile(file_source):
                raise SecurityViolationError(f"Target file does not exist on disk: '{file_source}'.")
            size = os.path.getsize(file_source)
            with open(file_source, "rb") as f:
                header = f.read(16)
        else:
            raise SecurityViolationError("file_source must be a file path string or byte buffer.")

        # Size limit check
        if size > max_size_bytes:
            raise SecurityViolationError(
                f"File size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit ({max_size_bytes / (1024 * 1024):.2f} MB)."
            )

        # Magic bytes authentication for known binary formats
        if ext in [".tif", ".tiff", ".geotiff"]:
            valid_tiff = (
                header.startswith(cls.MAGIC_SIGNATURES["tiff_le"]) or
                header.startswith(cls.MAGIC_SIGNATURES["tiff_be"]) or
                header.startswith(cls.MAGIC_SIGNATURES["bigtiff_le"]) or
                header.startswith(cls.MAGIC_SIGNATURES["bigtiff_be"])
            )
            if not valid_tiff:
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in TIFF file '{filename}'.")
                raise SecurityViolationError(f"Invalid TIFF magic bytes in file '{filename}'.")

        elif ext == ".png":
            if not header.startswith(cls.MAGIC_SIGNATURES["png"]):
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in PNG file '{filename}'.")
                raise SecurityViolationError(f"Invalid PNG magic bytes in file '{filename}'.")

        elif ext in [".jpg", ".jpeg"]:
            if not header.startswith(cls.MAGIC_SIGNATURES["jpeg"]):
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in JPEG file '{filename}'.")
                raise SecurityViolationError(f"Invalid JPEG magic bytes in file '{filename}'.")

        elif ext == ".webp":
            if not header.startswith(b"RIFF"):
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in WebP file '{filename}'.")
                raise SecurityViolationError(f"Invalid WebP magic bytes in file '{filename}'.")

        elif ext == ".bmp":
            if not header.startswith(b"BM"):
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in BMP file '{filename}'.")
                raise SecurityViolationError(f"Invalid BMP magic bytes in file '{filename}'.")

        elif ext == ".gif":
            if not (header.startswith(b"GIF87a") or header.startswith(b"GIF89a")):
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in GIF file '{filename}'.")
                raise SecurityViolationError(f"Invalid GIF magic bytes in file '{filename}'.")

        elif ext == ".jp2":
            valid_jp2 = header.startswith(b"\x00\x00\x00\x0c") or header.startswith(b"\xff\x4f")
            if not valid_jp2:
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    raise SecurityViolationError(f"Disguised binary executable detected in JPEG 2000 file '{filename}'.")
                raise SecurityViolationError(f"Invalid JPEG 2000 magic bytes in file '{filename}'.")

        elif ext in [".h5", ".hdf5"]:
            if not header.startswith(cls.MAGIC_SIGNATURES["hdf5"]):
                raise SecurityViolationError(f"Invalid HDF5 magic bytes in file '{filename}'.")

        elif ext == ".nc":
            valid_nc = (
                header.startswith(cls.MAGIC_SIGNATURES["netcdf_classic"]) or
                header.startswith(cls.MAGIC_SIGNATURES["netcdf_64bit"]) or
                header.startswith(cls.MAGIC_SIGNATURES["hdf5"])
            )
            if not valid_nc:
                raise SecurityViolationError(f"Invalid NetCDF magic bytes in file '{filename}'.")

        elif ext == ".zip":
            valid_zip = (
                header.startswith(cls.MAGIC_SIGNATURES["zip"]) or
                header.startswith(cls.MAGIC_SIGNATURES["zip_empty"]) or
                header.startswith(cls.MAGIC_SIGNATURES["zip_spanned"])
            )
            if not valid_zip:
                raise SecurityViolationError(f"Invalid ZIP magic bytes in file '{filename}'.")

        elif ext == ".npy":
            if not header.startswith(cls.MAGIC_SIGNATURES["npy"]):
                raise SecurityViolationError(f"Invalid NumPy .npy magic bytes in file '{filename}'.")

        elif ext in [".json", ".csv"]:
            try:
                header.decode("utf-8")
            except UnicodeDecodeError:
                raise SecurityViolationError(f"Binary shellcode or non-text bytes detected in text file '{filename}'.")

        return True, safe_name

    # =========================================================================
    # 3. Archive Decompression & Zip Bomb Prevention
    # =========================================================================

    @classmethod
    def validate_archive_decompression(
        cls,
        archive_path: str,
        max_total_size: int = 1024 * 1024 * 1024,  # 1 GB
        max_ratio: float = 25.0,                   # Max 25:1 compression ratio
        max_file_count: int = 10000
    ) -> Dict[str, Any]:
        """
        Inspects archive headers before extraction.
        Blocks zip bombs, compression ratio bombs, path traversal in member names,
        absolute member paths, and symlink members.
        """
        if not os.path.isfile(archive_path):
            raise SecurityViolationError(f"Archive file '{archive_path}' does not exist.")

        archive_size = os.path.getsize(archive_path)
        if archive_size == 0:
            raise SecurityViolationError("Empty archive file.")

        total_uncompressed = 0
        file_count = 0
        members_summary = []

        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zf:
                infolist = zf.infolist()
                file_count = len(infolist)

                if file_count > max_file_count:
                    raise SecurityViolationError(
                        f"Archive member count ({file_count}) exceeds limit ({max_file_count})."
                    )

                for info in infolist:
                    name = info.filename
                    if ".." in name or name.startswith("/") or name.startswith("\\"):
                        raise SecurityViolationError(
                            f"Malicious member path traversal in archive: '{name}'."
                        )
                    if re.match(r"^[a-zA-Z]:", name):
                        raise SecurityViolationError(
                            f"Absolute drive letter path in archive member: '{name}'."
                        )

                    total_uncompressed += info.file_size
                    members_summary.append({"name": name, "size": info.file_size})

        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r") as tf:
                members = tf.getmembers()
                file_count = len(members)

                if file_count > max_file_count:
                    raise SecurityViolationError(
                        f"Archive member count ({file_count}) exceeds limit ({max_file_count})."
                    )

                for m in members:
                    if m.issym() or m.islnk():
                        raise SecurityViolationError(
                            f"Symlink or hardlink archive member rejected for security: '{m.name}'."
                        )
                    if ".." in m.name or m.name.startswith("/") or m.name.startswith("\\"):
                        raise SecurityViolationError(
                            f"Malicious member path traversal in archive: '{m.name}'."
                        )
                    total_uncompressed += m.size
                    members_summary.append({"name": m.name, "size": m.size})
        else:
            raise SecurityViolationError(f"Unsupported archive format for decompression: '{archive_path}'.")

        if total_uncompressed > max_total_size:
            raise SecurityViolationError(
                f"Uncompressed archive size ({total_uncompressed / (1024*1024):.1f} MB) exceeds safety threshold ({max_total_size / (1024*1024):.1f} MB)."
            )

        ratio = total_uncompressed / max(1, archive_size)
        if ratio > max_ratio and total_uncompressed > 50 * 1024 * 1024:
            raise SecurityViolationError(
                f"Suspicious compression ratio bomb detected: ratio {ratio:.1f}:1 exceeds safety limit {max_ratio}:1."
            )

        return {
            "archive_path": archive_path,
            "archive_size": archive_size,
            "total_uncompressed_bytes": total_uncompressed,
            "compression_ratio": round(ratio, 2),
            "file_count": file_count,
            "is_safe": True
        }

    # =========================================================================
    # 4. Safe Subprocess Execution (shell=False, Argument Whitelist)
    # =========================================================================

    @classmethod
    def safe_subprocess_run(
        cls,
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        allowed_binaries: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Executes a subprocess safely with shell=False and argument verification.
        """
        if not isinstance(cmd, (list, tuple)) or len(cmd) == 0:
            raise SecurityViolationError("Subprocess command must be a non-empty list of arguments.")

        for arg in cmd:
            if not isinstance(arg, str):
                raise SecurityViolationError(f"Subprocess argument must be string, got: {type(arg)}")
            if "\x00" in arg:
                raise SecurityViolationError("Null byte detected in subprocess argument.")

        binary_name = os.path.basename(cmd[0]).lower()
        if binary_name.endswith(".exe"):
            binary_name = binary_name[:-4]

        whitelist = set(allowed_binaries) if allowed_binaries else cls.DEFAULT_ALLOWED_BINARIES
        if binary_name not in whitelist:
            raise SecurityViolationError(
                f"Execution of binary '{binary_name}' is prohibited by TRINETRA security policy. Allowed: {sorted(whitelist)}."
            )

        try:
            return subprocess.run(
                cmd,
                cwd=cwd,
                timeout=timeout,
                shell=False,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
        except subprocess.TimeoutExpired as e:
            raise SecurityViolationError(
                f"Subprocess execution timed out after {timeout}s: '{' '.join(cmd)}'."
            ) from e
        except Exception as e:
            raise SecurityViolationError(f"Failed to safely execute subprocess: {e}") from e
