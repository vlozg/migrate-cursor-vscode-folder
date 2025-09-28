from pathlib import Path
import json
import sys

import duckdb
import pyarrow as pa
from tqdm import tqdm

from utils.vscode import load_vscode_workspace_storage
from utils.path_utils import windows_path_to_posix_uri, posix_uri_to_windows_path
from migrate_ws_storage import migrate_ws_storage

CURSOR_WORKSPACES_DIR = Path("./")
USER_NAME = "vulon"


def main():
    if sys.platform != "win32":
        raise NotImplementedError("This script is only supported on Windows")

    list_ws_ids, list_ws_json = load_vscode_workspace_storage(CURSOR_WORKSPACES_DIR)

    ds = pa.table({"ws_uuid": list_ws_ids, "ws_metadata": list_ws_json})

    ds_2 = duckdb.sql("select ws_uuid, unnest(ws_metadata) from ds")

    assert set(ds_2.columns) == {"ws_uuid", "folder", "workspace"}

    # Ensure only OneDrive/Desktop is ever opened with Cursor
    assert duckdb.sql(f"""
    select count(*)
    from ds_2
    where folder LIKE '%Users/{USER_NAME}/OneDrive%' AND folder NOT LIKE '%Users/{USER_NAME}/OneDrive/Desktop%' AND folder NOT LIKE 'vscode-remote://%'
    """).fetchone() == (0,)

    migrate_list = duckdb.sql(f"""
    select ws_uuid, folder
    from ds_2 where folder LIKE '%Users/{USER_NAME}/OneDrive%' AND folder NOT LIKE 'vscode-remote://%'
    """).fetchall()


    for ws_uuid, folder in tqdm(migrate_list):
        try:
            migrate_ws_storage(
                posix_uri_to_windows_path(folder),
                ws_uuid,
                f"Users/{USER_NAME}/OneDrive/Desktop",
                f"Users/{USER_NAME}/Desktop",
                # dry_run=True,
            )
        except Exception as e:
            print(f"Error migrating workspace {ws_uuid}: {e}")


def main_2():
    """Adhoc fix for the workspace.json file."""
    for ws_uuid, ws_json in zip(*load_vscode_workspace_storage(CURSOR_WORKSPACES_DIR)):
        new_obj = ws_json.copy()
        num_changes = 0
        if "folder" in ws_json and not (ws_json["folder"].startswith("file:///") or ws_json["folder"].startswith("vscode-remote://")):
            new_obj["folder"] = windows_path_to_posix_uri(ws_json["folder"])
            num_changes += 1
        if "workspace" in ws_json and not (ws_json["workspace"].startswith("file:///") or ws_json["workspace"].startswith("vscode-remote://")):
            new_obj["workspace"] = windows_path_to_posix_uri(ws_json["workspace"])
            num_changes += 1
        if "workspace" in new_obj and "%5C" in new_obj["workspace"]:
            new_obj["workspace"] = new_obj["workspace"].replace("%5C", "/")
            num_changes += 1
        if "folder" in new_obj and "%5C" in new_obj["folder"]:
            new_obj["folder"] = new_obj["folder"].replace("%5C", "/")
            num_changes += 1
        if num_changes > 0:
            print(ws_uuid, num_changes)
            with open(f"./{ws_uuid}/workspace.json", "w") as fp:
                json.dump(new_obj, fp)
    

if __name__ == "__main__":
    main()
