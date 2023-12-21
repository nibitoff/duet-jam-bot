import random
import re
from bot import keyboards, states, playlist_handler
from database import model as db_model
from user_interaction import texts
from logs import logged_execution
from io import StringIO, BytesIO
import os
import boto3


session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=os.environ.get("OBJECT_STORAGE_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("OBJECT_STORAGE_SECRET_KEY")
)

def handle_start(message, bot, pool):
    bot.send_message(message.chat.id, texts.START, reply_markup=keyboards.EMPTY)

@logged_execution
def handle_register(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)

    if current_data:
        bot.send_message(
            message.chat.id,
            texts.ALREADY_REGISTERED.format(
                current_data["first_name"],
                current_data["last_name"]
            ),
            reply_markup=keyboards.EMPTY,
        )
        return

    bot.send_message(
        message.chat.id,
        texts.FIRST_NAME,
        reply_markup=keyboards.get_reply_keyboard(["/cancel"]),
    )
    bot.set_state(
        message.from_user.id, states.RegisterState.first_name, message.chat.id
    )


@logged_execution
def handle_cancel_registration(message, bot, pool):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(
        message.chat.id,
        texts.CANCEL_REGISTER,
        reply_markup=keyboards.EMPTY,
    )

@logged_execution
def handle_get_first_name(message, bot, pool):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["first_name"] = message.text
    bot.set_state(message.from_user.id, states.RegisterState.last_name, message.chat.id)
    bot.send_message(
        message.chat.id,
        texts.LAST_NAME,
        reply_markup=keyboards.get_reply_keyboard(["/cancel"]),
    )

@logged_execution
def handle_get_last_name(message, bot, pool):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["last_name"] = message.text
    # bot.set_state(message.from_user.id, states.RegisterState.last_name, message.chat.id)
    bot.send_message(
        message.chat.id,
        texts.REGISTRATION_ENDED,
        reply_markup=keyboards.get_reply_keyboard(["/cancel"]),
    )

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        first_name = data["first_name"]
        last_name = data["last_name"]

    bot.delete_state(message.from_user.id, message.chat.id)
    db_model.add_user_info(pool, message.from_user.id, first_name, last_name)

    bot.send_message(
        message.chat.id,
        texts.DATA_IS_SAVED.format(first_name, last_name),
        reply_markup=keyboards.EMPTY,
    )

@logged_execution
def handle_show_data(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)

    if not current_data:
        bot.send_message(
            message.chat.id, texts.NOT_REGISTERED, reply_markup=keyboards.EMPTY
        )
        return

    bot.send_message(
        message.chat.id,
        texts.SHOW_DATA_WITH_PREFIX.format(
            current_data["first_name"], current_data["last_name"]
        ),
        reply_markup=keyboards.EMPTY,
    )

@logged_execution
def handle_delete_account(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)
    if not current_data:
        bot.send_message(
            message.chat.id, texts.NOT_REGISTERED, reply_markup=keyboards.EMPTY
        )
        return

    bot.send_message(
        message.chat.id,
        texts.DELETE_ACCOUNT,
        reply_markup=keyboards.get_reply_keyboard(texts.DELETE_ACCOUNT_OPTIONS),
    )
    bot.set_state(
        message.from_user.id, states.DeleteAccountState.are_you_sure, message.chat.id
    )

@logged_execution
def handle_finish_delete_account(message, bot, pool):
    bot.delete_state(message.from_user.id, message.chat.id)

    if message.text not in texts.DELETE_ACCOUNT_OPTIONS:
        bot.send_message(
            message.chat.id,
            texts.DELETE_ACCOUNT_UNKNOWN,
            reply_markup=keyboards.EMPTY,
        )
        return

    if texts.DELETE_ACCOUNT_OPTIONS[message.text]:
        db_model.delete_user_info(pool, message.from_user.id)
        bot.send_message(
            message.chat.id,
            texts.DELETE_ACCOUNT_DONE,
            reply_markup=keyboards.EMPTY,
        )
    else:
        bot.send_message(
            message.chat.id,
            texts.DELETE_ACCOUNT_CANCEL,
            reply_markup=keyboards.EMPTY,
        )

@logged_execution
def handle_create_playlist(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)
    if not current_data:
        bot.send_message(
            message.chat.id,
            texts.NOT_REGISTERED,
            reply_markup=keyboards.EMPTY,
        )
        return

    bot.send_message(
        message.chat.id,
        "Enter the link to the first playlist:",
        reply_markup=keyboards.EMPTY,
    )
    bot.set_state(message.from_user.id, states.PlaylistState.playlist_1, message.chat.id)

@logged_execution
def handle_first_playlist(message, bot, pool):
    if not (match := re.match(r"https://open.spotify.com/playlist/(.*)\?", message.text)):
        bot.send_message(
            message.chat.id,
            "Expected format: https://open.spotify.com/playlist/...",
            reply_markup=keyboards.EMPTY,
        )
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["playlist_1"] = message.text
    bot.set_state(message.from_user.id, states.PlaylistState.playlist_2, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Enter the link to the second playlist:",
        reply_markup=keyboards.EMPTY,
    )

@logged_execution
def handle_second_playlist(message, bot, pool):
    if not (match := re.match(r"https://open.spotify.com/playlist/(.*)\?", message.text)):
        bot.send_message(
            message.chat.id,
            "Expected format: https://open.spotify.com/playlist/...",
            reply_markup=keyboards.EMPTY,
        )
        return
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["playlist_2"] = message.text

    bot.set_state(message.from_user.id, states.PlaylistState.name, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Enter the name of new playlist:",
        reply_markup=keyboards.EMPTY,
    )

@logged_execution
def handle_name_generated_playlist(message, bot, pool):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        playlist_1 = data["playlist_1"]
        playlist_2 = data["playlist_2"]
        name = message.text

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Generating playlist...Please wait",
        reply_markup=keyboards.EMPTY,
    )
    buffer = StringIO()
    generated_playlist_name = name.replace(" ", "_") + '.csv'
    playlist_handler.get_generated_playlist(buffer, playlist_1, playlist_2)
    playlist_id = random.randint(0,10000000)
    object_name = None

    if object_name is None:
        object_name = os.path.basename(generated_playlist_name)

    bucket_name = 'duet-jam-bucket'
    file_path = f'{message.chat.id}/{object_name}'
    s3.put_object(Body=buffer.getvalue(), Bucket=bucket_name, Key=file_path)
    buffer.close()
    link_to_playlist = f'https://storage.yandexcloud.net/{bucket_name}/{file_path}'
    bot.send_message(
        message.chat.id,
        "Generated playlist: " + link_to_playlist,
        reply_markup=keyboards.EMPTY,
        )

    db_model.add_playlist(pool, playlist_id, message.from_user.id, name, link_to_playlist)


@logged_execution
def handle_show_playlists(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)
    if not current_data:
        bot.send_message(
            message.chat.id, texts.NOT_REGISTERED, reply_markup=keyboards.EMPTY
        )
        return
    playlists = db_model.get_playlists(pool, message.from_user.id)
    if not playlists:
        bot.send_message(
            message.chat.id, "You didn't create any playlists!", reply_markup=keyboards.EMPTY
        )
        return
    bot.send_message(
        message.chat.id,
        "Your playlists:",
        reply_markup=keyboards.EMPTY,
    )
    for playlist in playlists:
        bot.send_message(
            message.chat.id,
            "id =" + str(playlist["playlist_id"]) + ";" + " link= " + playlist["file_name"],
            reply_markup=keyboards.EMPTY,
            )
    # answer_buf.close()




@logged_execution
def handle_start_delete_playlist(message, bot, pool):
    current_data = db_model.get_user_info(pool, message.from_user.id)
    if not current_data:
        bot.send_message(
            message.chat.id,
            texts.NOT_REGISTERED,
            reply_markup=keyboards.EMPTY,
        )
        return
    bot.set_state(message.from_user.id, states.PlaylistDelete.playlist_id, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Enter playlist's ID that you want to delete:",
        reply_markup=keyboards.EMPTY,
        )


@logged_execution
def handle_finish_delete_playlist(message, bot, pool):
    bot.send_message(
        message.chat.id,
        "Deleting...",
        reply_markup=keyboards.EMPTY,
    )
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        playlist_id = message.text
    bot.delete_state(message.from_user.id, message.chat.id)
    db_model.delete_playlist(pool, int(playlist_id), message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Playlist was successfully deleted!",
        reply_markup=keyboards.EMPTY,
    )