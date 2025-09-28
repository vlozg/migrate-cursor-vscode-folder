# Simple script for migrating VS Code/Cursor state when moving folder location

Note:
1. This script **only supports Windows**. Though, it should be mostly the same for other platform with minor tweaking in path handling.
2. This code base might be a lil' bit messy because it supposed to be quick, not to be clean 😒 (sigh, it could be cleaner if I get paid for doing this).


## Overview
Have you ever found yourself staring at empty VS Code/Cursor window when opening it inside a folder that you have just renamed, moved,...? All of your notepads, your unsaved files, your last 100+ open tabs, your AI chat history,... are gone. This script is here to help you in that situation!

That happened because VS Code stores all of your window working state inside a SQLite DB, which is stored separately for each folder in the `User\workspaceStorage`. If you move your code repo, you will lose that work session because the SQLite file still points to the old location.

To fix this, this script will:
- Scan `User\workspaceStorage` folder (path must be provided by user) and list out all folders having state stored here, together with its UUID
- Filter out folders to update path based on path pattern provided by the user
- Automatically create workspace state folder correspondingly, without the need to manually open folder with VS Code/Cursor first (as mention in [1])
- Safely remove moved state folder to Recycle bin for restoration


## Requirements
- OS: Windows
- Python 3.13
- `uv` installed (it's a Python package management tool in case you don't know)


## How to use?
1. Look for `User\workspaceStorage` location
    - If you are using Cursor installed via Scoop, it is `%USERPROFILE%\scoop\persist\cursor\data\user-data\User\workspaceStorage`
    - If you are using VS Code installed via Scoop, it is `%USERPROFILE%\scoop\persist\code\data\user-data\User\workspaceStorage`
    - If you are using VS Code installed via EXE, it is `%APPDATA%\Code\User\workspaceStorage`
    - If you are using Cursor installed via EXE, you know the pattern 😊
2. Edit constant `CURSOR_WORKSPACES_DIR`, `SRC_PATH`, `DST_PATH` in the `main.py` file
3. Run it with `uv run main.py` (requires `uv` installed first)


## References
1. [https://stackoverflow.com/questions/52056826/how-to-move-a-visual-studio-code-workspace-to-a-new-location-painlessly/62087889#62087889](https://stackoverflow.com/questions/52056826/how-to-move-a-visual-studio-code-workspace-to-a-new-location-painlessly/62087889#62087889)
