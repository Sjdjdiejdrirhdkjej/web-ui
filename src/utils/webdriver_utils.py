import os
import shutil
import stat
from typing import Optional # Added Optional import

def find_chromedriver_executable() -> Optional[str]:
    """
    Finds the ChromeDriver executable by checking various locations.

    Search Order:
    1. Environment variable CHROMEDRIVER_PATH.
    2. shutil.which('chromedriver') (checks system PATH).
    3. Common known locations:
        - ./chromedriver (current working directory)
        - ./.pythonlibs/bin/chromedriver (common in Replit environments)
        - /usr/local/bin/chromedriver
        - /usr/bin/chromedriver
    """
    # 1. Environment variable
    env_path = os.environ.get('CHROMEDRIVER_PATH')
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # 2. shutil.which (system PATH)
    shutil_path = shutil.which('chromedriver')
    if shutil_path and os.path.isfile(shutil_path) and os.access(shutil_path, os.X_OK):
        return shutil_path

    # 3. Common known locations
    common_paths = [
        os.path.join(os.getcwd(), 'chromedriver'),  # Local CWD
        os.path.expanduser('~/.local/bin/chromedriver'), # User local bin
        os.path.join(os.getcwd(), '.pythonlibs', 'bin', 'chromedriver'), # Replit
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
    ]

    # Check for Nix-specific paths if NIX_PROFILES is set
    nix_profiles = os.environ.get('NIX_PROFILES')
    if nix_profiles:
        for profile_path_str in nix_profiles.split(' '):
            potential_nix_path = os.path.join(profile_path_str, 'bin', 'chromedriver')
            common_paths.append(potential_nix_path)

    for p_path in common_paths:
        abs_path = os.path.abspath(p_path)
        if os.path.isfile(abs_path) and os.access(abs_path, os.X_OK):
            return abs_path
            
    # Placeholder for recursive search if needed later
    # project_chromedriver = find_file_recursively('chromedriver', os.getcwd(), 2)
    # if project_chromedriver:
    #    return project_chromedriver

    return None

def is_executable(path: str) -> bool:
    """Check if a path is an executable file."""
    return os.path.isfile(path) and os.access(path, os.X_OK)

def find_file_recursively(filename: str, search_root: str, max_depth: int = 3) -> Optional[str]:
    """
    Recursively search for a file within a directory up to max_depth.
    Returns the first match found.
    """
    abs_search_root = os.path.abspath(search_root)
    for current_depth, (root, dirs, files) in enumerate(os.walk(abs_search_root)):
        if current_depth >= max_depth:
            dirs[:] = [] 
            continue

        if filename in files:
            potential_path = os.path.join(root, filename)
            if is_executable(potential_path):
                return potential_path
    return None
