from hashlib import md5
from pathlib import Path
import sqlite3
import json


STATE_DB_TABLE_NAME: str = "ItemTable"
STATE_DB_COLUMN_NAME: str = "value"


def get_ws_uuid(ws_folder: Path, alt_path: Path | None = None) -> str:
    """Get the VSCode UUID of a workspace folder.
    Reference: https://stackoverflow.com/questions/74155386/how-does-vscode-determine-the-workspacestorage-folder-for-a-given-workspace

    Args:
        ws_folder: The workspace folder.
        alt_path: The alternative path to use for the workspace folder. This is used to migrate workspaces to a new location.

    Returns:
        The VSCode UUID of the workspace folder.
    """
    ct_timestamp = int(ws_folder.stat().st_ctime * 1000)

    _ws_folder = alt_path or ws_folder
    home_str = (
        _ws_folder.home().drive.lower()
    )  # In hash function, this drives gets converted to lower case
    p_str = str(_ws_folder)
    p_str = home_str + p_str[len(home_str) :]

    # Hash formula: MD5(p_str + ct_timestamp)
    hash_obj = md5(p_str.encode() + str(ct_timestamp).encode())

    return hash_obj.hexdigest()


def update_state_db_paths(
    state_db_path: Path,
    find_path: str,
    replace_path: str,
):
    """
    Connects to an SQLite database and updates a specific column by replacing
    a substring in its value, handling different path separators.

    Args:
        state_db_path (Path): The path to the state.vscdb file.
        find_path (str): The substring to find.
        replace_path (str): The string to replace the found substring with.
    """
    connection = sqlite3.connect(state_db_path)

    try:
        # --- 2. Connect to the SQLite database ---
        cursor = connection.cursor()

        # --- 3. Verify that the table and column exist ---
        cursor.execute(f"PRAGMA table_info('{STATE_DB_TABLE_NAME}');")
        columns = [info[1] for info in cursor.fetchall()]
        if not columns:
            print(f"Error: Table '{STATE_DB_TABLE_NAME}' not found in the database.")
            return
        if STATE_DB_COLUMN_NAME not in columns:
            print(
                f"Error: Column '{STATE_DB_COLUMN_NAME}' not found in table '{STATE_DB_TABLE_NAME}'."
            )
            print(f"Available columns are: {', '.join(columns)}")
            return

        # --- 4. Construct and execute the UPDATE query ---
        # We will chain REPLACE functions to handle different path separators.
        # Using parameters (?) is crucial to prevent SQL injection.

        # Normalize find_path for different separators
        find_double_forward_slash = find_path.replace("/", "\\")
        replace_double_forward_slash = replace_path.replace("/", "\\")

        find_quad_forward_slash = find_path.replace("/", "\\\\")
        replace_quad_forward_slash = replace_path.replace("/", "\\\\")

        # This query is more robust. It replaces the forward-slash version first,
        # then takes the result of that and replaces the back-slash version.
        # This handles cases where paths might have mixed separators.
        query = f"""
        UPDATE `{STATE_DB_TABLE_NAME}`
        SET `{STATE_DB_COLUMN_NAME}` = REPLACE(
            REPLACE(
                REPLACE(
                    `{STATE_DB_COLUMN_NAME}`,
                    ?,
                    ?
                ),
                ?,
                ?
            ),
            ?,
            ?
        );
        """

        # Parameters for the query
        params = (
            find_path,
            replace_path,
            find_double_forward_slash,
            replace_double_forward_slash,
            find_quad_forward_slash,
            replace_quad_forward_slash,
        )

        print("\nExecuting the following operation:")
        print(f"  Table:    {STATE_DB_TABLE_NAME}")
        print(f"  Column:   {STATE_DB_COLUMN_NAME}")
        print(f"  Finding:  '{find_path}' (and variants)")
        print(f"  Replacing with: '{replace_path}' (and variants)")

        cursor.execute(query, params)

        # --- 5. Commit the changes and report results ---
        # To save the changes, we need to commit the transaction.
        connection.commit()

        # cursor.rowcount will tell us how many rows were affected.
        print(f"\nSuccess! Update complete. {cursor.rowcount} row(s) were affected.")

    except sqlite3.DatabaseError as e:
        print(f"Database Error: An error occurred. Details: {e}")
        if connection:
            connection.rollback()  # Roll back changes if an error occurs
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


def load_vscode_workspace_storage(ws_storage_dir: Path) -> tuple[list[str], list[dict]]:
    list_workspaces = list(ws_storage_dir.rglob("*/workspace.json"))
    list_ws_ids = [f.parent.name for f in list_workspaces]
    list_ws_json = []
    for file in list_workspaces:
        with file.open() as fp:
            obj = json.load(fp)

            if len(set(obj.keys()) - {"folder", "workspace"}) > 0:
                print(f"Warning: Workspace file {file} has unexpected keys: {set(obj.keys())}")

            list_ws_json.append(obj)

    return list_ws_ids, list_ws_json
