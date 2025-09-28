from pathlib import Path
import json
import shutil

from utils.vscode import get_ws_uuid, update_state_db_paths
from utils.path_utils import windows_path_to_posix_uri, delete_workspace


def migrate_ws_storage(
    old_ws_folder: Path,
    old_ws_uuid: str,
    find_path: str,
    replace_path: str,
    *,
    dry_run: bool = False,
):
    _old_ws_folder = Path(old_ws_folder)
    _new_ws_folder = Path(str(_old_ws_folder).replace(str(Path(find_path)), str(Path(replace_path))))

    if _old_ws_folder == _new_ws_folder:
        print(
            f"Workspace folder {_old_ws_folder} is already in the new location {_new_ws_folder}"
        )
        return

    # Verify that old folder have been renamed and does not exist
    if _old_ws_folder.exists():
        raise FileExistsError(
            f"Workspace folder {_old_ws_folder} exists when we expected it to be renamed"
        )
    if not _new_ws_folder.exists():
        raise FileExistsError(
            f"Workspace folder {_new_ws_folder} does not exist when we expected it to be created"
        )

    # Verify that the UUID is correct
    if get_ws_uuid(_new_ws_folder, _old_ws_folder) != old_ws_uuid:
        raise ValueError(
            f"Workspace folder {_new_ws_folder} has an incorrect UUID, possibly wrong creation timestamp, please do migration manually"
        )

    # Start migration
    _new_ws_uuid = get_ws_uuid(_new_ws_folder)

    if _new_ws_uuid == old_ws_uuid:
        print(
            f"Unexpected: Workspace folder {_new_ws_folder} has the same UUID as the old workspace folder {_old_ws_folder}"
        )
        return

    _old_ws_storage_folder = Path(f"./{old_ws_uuid}")
    _new_ws_storage_folder = Path(f"./{_new_ws_uuid}")

    # Verify that the new workspace folder does not exist
    if _new_ws_storage_folder.exists():
        raise FileExistsError(
            f"Workspace folder {_new_ws_storage_folder} exists when we expected it to be created"
        )
    _new_ws_storage_folder.mkdir(parents=True)

    # 1. Copy all files in the old folder to the new folder (except for the `state.vscdb.backup` file)
    _count_objs = 0
    for file_obj in _old_ws_storage_folder.rglob("*"):
        if file_obj.name != "state.vscdb.backup":
            if not dry_run:
                if file_obj.is_dir():
                    shutil.copytree(file_obj, _new_ws_storage_folder / file_obj.name)
                else:
                    shutil.copy(file_obj, _new_ws_storage_folder / file_obj.name)
            _count_objs += 1
    print(
        f"Copied {_count_objs} files/directories from {_old_ws_storage_folder} to {_new_ws_storage_folder}"
    )

    # 2. Update path in the workspace.json file
    if not dry_run:
        with (_new_ws_storage_folder / "workspace.json").open() as fp:
            ws_json = json.load(fp)
        ws_json["folder"] = windows_path_to_posix_uri(_new_ws_folder)
        with (_new_ws_storage_folder / "workspace.json").open("w") as fp:
            json.dump(ws_json, fp)
    print(f"Updated path in the workspace.json file to {_new_ws_folder}")

    # 3. Update path in the state.vscdb file
    if not dry_run:
        update_state_db_paths(_new_ws_storage_folder / "state.vscdb", find_path, replace_path)
    print(f"Updated path in the state.vscdb file to {_new_ws_folder}")

    # 4. Delete the old workspace folder
    print(f"Deleting old workspace folder {_old_ws_storage_folder}")
    if not dry_run:
        delete_workspace(old_ws_uuid)
