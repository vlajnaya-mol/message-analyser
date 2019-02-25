import message_analyser.storage as storage
from dateutil.relativedelta import relativedelta
from telethon import TelegramClient  # , sync
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError, \
    SessionPasswordNeededError, PasswordHashInvalidError, FloodWaitError
from message_analyser.myMessage import MyMessage
from message_analyser.misc import log_line, time_offset


async def get_str_dialogs(client=None, loop=None):
    """Retrieves a list with all user-dialogs of a current client.

    Args:
        client (TelegramClient object, optional): A client.
        loop (asyncio.windows_events._WindowsSelectorEventLoop, optional): An event loop.

    Returns:
        A list of strings. An example:

        ["Alex (id=00001)", "Kate (id=99990)"]

        Where Alex and Kate are names, 00001 and 99990 are IDs of their dialogs.
    """
    return [f"{dialog.name} (id={dialog.id})" for dialog in await _get_dialogs(client, loop)]


async def get_sign_in_results(api_id, api_hash, code, phone_number, password, session_name, loop=None):
    """Tries to sign-in in Telegram with given parameters.

    Notes: Automatically creates .session file for further sign-ins.

    Args:
        api_id (str/int): Telegram API id.
        api_hash (str): Telegram API hash.
        code (str/int): A confirmation code.
        phone_number (str): A phone number connected to such id/hash pair.
        password (str): 2FA password (if needed).
        session_name (str): A name of the current session.
        loop (asyncio.windows_events._WindowsSelectorEventLoop, optional): An event loop.

    Returns:
        A string describing the results of sign-in.
    """
    try:
        client = TelegramClient(session_name, api_id, api_hash, loop=loop)
        await client.connect()
    except (ApiIdInvalidError, ValueError):
        log_line("Unsuccessful sign-in! Wrong API.")
        return "wrong api"
    except OSError:
        log_line("No Internet connection.")
        return "no internet"
    try:
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                await client.sign_in(phone_number, password=password)
        if not await client.is_user_authorized():
            raise PhoneCodeInvalidError(request=None)
    except ApiIdInvalidError:
        log_line("Unsuccessful sign-in! Wrong API.")
        return "wrong api"
    except PhoneCodeInvalidError:
        log_line("Unsuccessful sign-in! Need code.")
        return "need code"
    except PasswordHashInvalidError:
        log_line("Unsuccessful sign-in! Need password.")
        return "need password"
    except (PhoneNumberInvalidError, TypeError):
        log_line("Unsuccessful sign-in! Need phone.")
        return "need phone"
    except FloodWaitError as err:
        log_line(f'Unsuccessful sign-in! {err.message}')
        return f'need wait for {err.seconds}'
    finally:
        if client.is_connected():
            await client.disconnect()
    log_line("Successful sign-in.")
    return "success"


async def get_telegram_messages(your_name, target_name, loop=None, target_id=None, num=1000000):
    """Retrieves a list of messages from Telegram dialogue.

    Notes:
        Requires a ready-to-use Telegram secrets (id, hash etc).
        Asks for target's id in a case this parameter is None.
        Retrieves a photo album as distinct messages with photos.

    Args:
        your_name (str): Your name.
        target_name (str): Target's name.
        loop (asyncio.windows_events._WindowsSelectorEventLoop, optional): An event loop.
        target_id (int,optional):  Target's dialogue id.
        num (int,optional): No more than num NEWEST messages will be retrieved.

    Returns:
        A list of MyMessage objects (from older messages to newer).
    """
    async with (await _get_client(loop=loop)) as client:
        if target_id is None:
            target_id = await _get_target_dialog_id(client)
        target_entity = await client.get_entity(target_id)
        log_line("Receiving Telegram messages...")
        telethon_messages = await _retrieve_messages(client, target_entity, num)
        messages = [_telethon_msg_to_mymessage(msg, target_id, your_name, target_name) for msg in telethon_messages]
        log_line(f"{len(messages)} Telegram messages were received")
        return messages


async def _retrieve_messages(client, target_entity, num):
    """Retrieves messages from client's target_entity batch by batch and return them all."""
    batch_size = min(3000, num)
    msgs = []
    batch = await client.get_messages(target_entity, limit=batch_size)
    while len(batch) and len(msgs) < num:
        offset_id = batch[-1].id
        msgs.extend([msg for msg in batch if isinstance(msg, Message)])
        try:
            batch = await client.get_messages(target_entity, limit=min(batch_size, num - len(msgs)), offset_id=offset_id)
        except ConnectionError:
            log_line("Internet connection was lost.")
            raise
        if not len(batch):
            log_line(f"{len(msgs[:num])} (100%) messages received.")
        else:
            log_line(f"{len(msgs[:num])} ({len(msgs[:num])/batch.total*100:.2f}%) messages received.")
    return msgs[:num][::-1]


async def _get_dialogs(client=None, loop=None):
    if client is None:
        async with (await _get_client(loop)) as client:
            return [dialog for dialog in list(await client.get_dialogs()) if dialog.is_user]
    return [dialog for dialog in list(await client.get_dialogs()) if dialog.is_user]


async def _get_client(loop=None):
    """Creates a Telegram client based on current Telegram secrets.

    Returns:
        TelegramClient object.
    """
    api_id, api_hash, phone_number, session_name = storage.get_telegram_secrets()
    if loop:
        client = TelegramClient(session_name, api_id, api_hash, loop=loop)
    else:
        client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        await client.sign_in(phone_number, input("Please enter the code you received: "))
    return client


async def _get_target_dialog_id(client):
    """Interacts with user to get an id of the target's dialogue.

    Returns:
        Integer value of target's dialogue id.
    """
    print("Here is a list of all your dialogues. Please find an id of a dialogue you want to analyse messages from.")
    for dialog in await get_str_dialogs(client):
        print(dialog)
    target_id = int(input("Input target dialog ID :"))
    return target_id


def _telethon_msg_to_mymessage(msg, target_id, your_name, target_name):
    """Transforms telethon.tl.types.Message obj to MyMessage obj.

    Notes:
        An emoji representation of a sticker adds up to the message's text.

    Args:
        msg (telethon.tl.types.Message): A message.
        target_id (int): Target's dialogue id.
        your_name (str): Your name.
        target_name (str): Target's name.

    Returns:
        MyMessage obj.
    """
    return MyMessage(msg.message + (msg.sticker.attributes[1].alt if msg.sticker is not None else ''),
                     msg.date.replace(tzinfo=None) + relativedelta(hours=time_offset(msg.date)),
                     target_name if msg.from_id == target_id else your_name,
                     is_forwarded=msg.forward is not None,
                     document_id=msg.document.id if msg.document is not None else None,
                     has_sticker=msg.sticker is not None,
                     has_video=msg.video is not None,
                     has_voice=(msg.voice is not None and
                                msg.document.mime_type == "audio/ogg"),
                     has_audio=(msg.audio is not None and
                                msg.document.mime_type != "audio/ogg"),  # let audio != voice
                     has_photo=msg.photo is not None)
