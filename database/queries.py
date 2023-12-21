USERS_INFO_TABLE = "user_personal_info"
STATES_TABLE = "states"
PLAYLISTS_TABLE = "playlists"

add_playlist = f"""
    DECLARE $name AS Utf8;
    DECLARE $file_name AS Utf8;
    DECLARE $user_id AS Uint64;
    DECLARE $playlist_id AS Uint64;

    INSERT INTO `{PLAYLISTS_TABLE}` (playlist_id, user_id, name, file_name)
    VALUES ($playlist_id, $user_id, $name, $file_name);
"""

get_playlists = f"""
    DECLARE $user_id AS Uint64;
    
    SELECT
        playlist_id,
        name,
        file_name
    FROM `{PLAYLISTS_TABLE}`
    WHERE user_id == $user_id;
"""

delete_playlist = f"""
    DECLARE $playlist_id AS Uint64;
    DECLARE $user_id AS Uint64;

    DELETE FROM `{PLAYLISTS_TABLE}`
        WHERE playlist_id == $playlist_id 
        AND user_id == $user_id;
"""


get_user_state = f"""
    DECLARE $user_id AS Uint64;

    SELECT state
    FROM `{STATES_TABLE}`
    WHERE user_id == $user_id;
"""

set_user_state = f"""
    DECLARE $user_id AS Uint64;
    DECLARE $state AS Utf8?;

    UPSERT INTO `{STATES_TABLE}` (`user_id`, `state`)
    VALUES ($user_id, $state);
"""

get_user_info = f"""
    DECLARE $user_id AS Int64;
    
    SELECT
        user_id,
        first_name,
        last_name
    FROM `{USERS_INFO_TABLE}`
    WHERE user_id == $user_id;
"""

add_user_info = f"""
    DECLARE $user_id AS Uint64;
    DECLARE $first_name AS Utf8;
    DECLARE $last_name AS Utf8;

    INSERT INTO `{USERS_INFO_TABLE}` (user_id, first_name, last_name)
    VALUES ($user_id, $first_name, $last_name);
"""

delete_user_info = f"""
    DECLARE $user_id AS Uint64;

    DELETE FROM `{USERS_INFO_TABLE}`
    WHERE user_id == $user_id;

    DELETE FROM `{STATES_TABLE}`
    WHERE user_id == $user_id;
"""
