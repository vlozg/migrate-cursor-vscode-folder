from pathlib import Path, PurePosixPath
import urllib.parse
import send2trash


def windows_path_to_posix_uri(path: Path) -> str:
    """Convert a Windows path to a POSIX URI stored in the workspace.json file."""
    return PurePosixPath("/", path).as_uri()


def posix_uri_to_windows_path(uri: str) -> Path:
    """Convert a POSIX URI stored in the workspace.json file to a Windows path."""
    _parsed_uri = urllib.parse.urlparse(uri)

    if _parsed_uri.scheme != "file":
        raise ValueError(f"URI {uri} is not a file URI")

    # Strip of the root slash os Posix path
    if _parsed_uri.path[0] == "/":
        _parsed_uri = _parsed_uri._replace(path=_parsed_uri.path[1:])

    return Path(urllib.parse.unquote(_parsed_uri.path))


def delete_workspace(ws_id: str):
    """Delete a workspace from the filesystem. This will move the workspace to the trash to prevent data loss."""
    ws_storage_folder = Path(f"./{ws_id}")
    if ws_storage_folder.exists():
        send2trash.send2trash(ws_storage_folder)
    print(f"Deleted workspace {ws_id} to trash")
