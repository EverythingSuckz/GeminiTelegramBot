import asyncio
from pathlib import Path
from typing import Dict, List, Optional

import logging

import google.generativeai as gemini
from google.generativeai.types.generation_types import StopCandidateException
from google.generativeai.types.content_types import to_content

from bot.database import DatabaseWrapper, Role


EXAMPLES = [
    {"role": "user", "parts": ["Hi there"]},    
    {"role": "model", "parts": ["Oh hi! Are you new here?"]},
    {"role": "user", "parts": ["Yeah"]},
    {"role": "model", "parts": ["Oh alright cool, hope you'll have a great time chatting with others!"]},
    {"role": "user", "parts": ["Yeah, Mind if I promote my channel here?"]},
    {"role": "model", "parts": ["Oh no, I'm afraid you can't as it's against out community rules."]},
    {"role": "user", "parts": ["Oh, Alright. Where do you live?"]},
    {"role": "model", "parts": ["I live in Tokyo."]},
    {"role": "user", "parts": ["Who are you?"]},
    {"role": "model", "parts": ["I'm Ai"]},
  ]

SYSTEM_PROMPT = Path("ai.prompt").read_text(encoding="utf-8")

GENERATION_CONFIG = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]


class GeminiChat:
    """
    A chat class that uses Gemini to generate responses.
    """
    def __init__(self, api_key: str) -> None:
        gemini.configure(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Gemini Chat Client")

    async def _generate_history(
        self,
        database: DatabaseWrapper,
        user_id: int
    ) -> List[Dict[str, str]]:
        """
        Helper function to generate history for Gemini.
        """
        histories = EXAMPLES.copy()
        raw_histories = await database.get_history(user_id)
        self.logger.debug(
            "Found total %d histories for user[%d]", len(list(raw_histories)), user_id
        )
        for history in raw_histories:
            if history.role == Role.USER:
                parts = []
                for part in history.parts:
                    if part.text:
                        parts.append(part.text)
                    elif part.file:
                        parts.append({"file_data": {"mime_type": part.file.mime_type, "file_uri": part.file.url}})
                histories.append({"role": "user", "parts": parts})
            elif history.role == Role.MODEL:
                parts = []
                for part in history.parts:
                    if part.text:
                        parts.append(part.text)
                    elif part.file:
                        print("REMOVE ME")
                        parts.append({"file_data": {"mime_type": part.file.mime_type, "file_uri": part.file.url}})
                histories.append({"role": "model", "parts": parts})
        return histories


    async def get_chat_session(self, database: DatabaseWrapper, user_id: int, name: str) -> gemini.ChatSession:
        model = gemini.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG,
            system_instruction=SYSTEM_PROMPT.format(name=name),
        )
        return gemini.ChatSession(
            model=model,
            history=await self._generate_history(database, user_id),
        )
        
    def _form_message(
        self, 
        message: Optional[str] = None,
        mime_type: Optional[str] = None,
        url: Optional[str] = None,
    ) -> list:
        """
        Form a message for Gemini.
        """
        parts = []
        if mime_type and url:
            parts.append({"file_data":{"mime_type": mime_type, "file_uri": url}})
        if message:
            parts.append({"text": message})
        raw_content = {"role": gemini.ChatSession._USER_ROLE, "parts": parts}
        content = to_content(raw_content)
        return content

    async def get_reponse(
        self,
        database: DatabaseWrapper,
        user_id: int,
        name: str,
        message: Optional[str] = None,
        mime_type: Optional[str] = None,
        url: Optional[str] = None,
        ) -> gemini.types.AsyncGenerateContentResponse:
        """
        Get a response from Gemini and save the history.
        """
        session = await self.get_chat_session(database, user_id, name)
        
        # Sending the message to the model before saving it to the database
        # Because, if the model fails to generate a response, we don't want to save
        # the user message to the database as it might cause further issues.
        # Check https://github.com/google/generative-ai-docs/issues/257
        
        try:
            content = self._form_message(message, mime_type, url)
            response = await session.send_message_async(content)
        except StopCandidateException as e:
            logging.exception(e)
            raise e
        
        await asyncio.gather(
            database.set_user_history(user_id, message, mime_type, url),
            database.set_response_history(user_id, response.text or "*ignores you*")
        )
        
        if not response.text:
            return response
        self.logger.debug("Generated response for user[%d]", user_id)
        self.logger.debug(response)
        return response
