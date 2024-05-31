import logging
import mimetypes
import re
from pathlib import Path

from google.generativeai import upload_file
from pyrogram import Client, enums, filters, types

from bot import Bot, db, gemini
from bot.helpers import limiter, mentioned

logger = logging.getLogger(__name__)

gfn = lambda x: f"{x.first_name} {x.last_name}" if x.last_name else ""

@Bot.on_message(filters.command("clearhistory") & filters.private)
@limiter(15)
async def clearhistory_cmd(_, message: types.Message):
    status = await message.reply(
        "<code>Please wait...</code>", parse_mode=enums.ParseMode.HTML
    )
    await db.clear_history(message.from_user.id if message.from_user else message.sender_chat.id)
    await status.edit_text("<b>Done</b>.", parse_mode=enums.ParseMode.HTML)
    


@Bot.on_message(filters.private | (mentioned & filters.group) & filters.incoming, group=2)
@limiter(3)
async def send_handler(c: Client, message: types.Message):
    text = None
    media = message.media or None
    mime_type = None
    url = None

    if message.text:
        text = re.sub(f"@{Bot.me.username}", "", message.text, flags=re.IGNORECASE).strip()
        if text.startswith("/"):
            return

    if media:
        media = getattr(message, media.value, None)
        if not media:
            return
        text = text or message.caption or getattr(media, "caption", None)
        if getattr(media, "file_size", 0) > 10_000_000:
            return await message.reply("File size is too large. Maximum file size is 10MB.", quote=True)
        path = await c.download_media(message=message)
        mime_type = mimetypes.guess_type(path)[0]
        file = upload_file(path)
        Path(path).unlink(missing_ok=True)
        url = file.uri
    else:
        if not text:
            return

    await message.reply_chat_action(enums.ChatAction.TYPING)
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    name = message.from_user.first_name if message.from_user else message.sender_chat.title
    resp = await gemini.get_reponse(database=db, user_id=user_id, name=gfn(message.from_user), message=text, mime_type=mime_type, url=url)
    
    if not resp:
        await message.reply("<i>*AI did not respond*</i>")
        return logger.info("No response to %s's message", name)
    
    try:
        await message.reply(resp.text, parse_mode=enums.ParseMode.MARKDOWN, disable_web_page_preview=True, quote=True)
    except Exception as e:
        logger.exception(e, stack_info=True)
        await message.reply(resp.text, disable_web_page_preview=True, quote=True)
