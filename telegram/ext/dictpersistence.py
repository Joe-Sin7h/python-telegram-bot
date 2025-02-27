#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2021
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module contains the DictPersistence class."""

from typing import DefaultDict, Dict, Optional, Tuple, cast
from collections import defaultdict

from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext.utils.types import ConversationDict, CDCData
from telegram.utils.types import JSONDict

try:
    import ujson as json
except ImportError:
    import json  # type: ignore[no-redef]


class DictPersistence(BasePersistence):
    """Using Python's :obj:`dict` and ``json`` for making your bot persistent.

    Note:
        This class does *not* implement a :meth:`flush` method, meaning that data managed by
        ``DictPersistence`` is in-memory only and will be lost when the bot shuts down. This is,
        because ``DictPersistence`` is mainly intended as starting point for custom persistence
        classes that need to JSON-serialize the stored data before writing them to file/database.

    Warning:
        :class:`DictPersistence` will try to replace :class:`telegram.Bot` instances by
        :attr:`REPLACED_BOT` and insert the bot set with
        :meth:`telegram.ext.BasePersistence.set_bot` upon loading of the data. This is to ensure
        that changes to the bot apply to the saved objects, too. If you change the bots token, this
        may lead to e.g. ``Chat not found`` errors. For the limitations on replacing bots see
        :meth:`telegram.ext.BasePersistence.replace_bot` and
        :meth:`telegram.ext.BasePersistence.insert_bot`.

    .. versionchanged:: 14.0
        The parameters and attributes ``store_*_data`` were replaced by :attr:`store_data`.

    Args:
        store_data (:class:`PersistenceInput`, optional): Specifies which kinds of data will be
            saved by this persistence instance. By default, all available kinds of data will be
            saved.
        user_data_json (:obj:`str`, optional): JSON string that will be used to reconstruct
            user_data on creating this persistence. Default is ``""``.
        chat_data_json (:obj:`str`, optional): JSON string that will be used to reconstruct
            chat_data on creating this persistence. Default is ``""``.
        bot_data_json (:obj:`str`, optional): JSON string that will be used to reconstruct
            bot_data on creating this persistence. Default is ``""``.
        callback_data_json (:obj:`str`, optional): Json string that will be used to reconstruct
            callback_data on creating this persistence. Default is ``""``.

            .. versionadded:: 13.6
        conversations_json (:obj:`str`, optional): JSON string that will be used to reconstruct
            conversation on creating this persistence. Default is ``""``.

    Attributes:
        store_data (:class:`PersistenceInput`): Specifies which kinds of data will be saved by this
            persistence instance.
    """

    __slots__ = (
        '_user_data',
        '_chat_data',
        '_bot_data',
        '_callback_data',
        '_conversations',
        '_user_data_json',
        '_chat_data_json',
        '_bot_data_json',
        '_callback_data_json',
        '_conversations_json',
    )

    def __init__(
        self,
        store_data: PersistenceInput = None,
        user_data_json: str = '',
        chat_data_json: str = '',
        bot_data_json: str = '',
        conversations_json: str = '',
        callback_data_json: str = '',
    ):
        super().__init__(store_data=store_data)
        self._user_data = None
        self._chat_data = None
        self._bot_data = None
        self._callback_data = None
        self._conversations = None
        self._user_data_json = None
        self._chat_data_json = None
        self._bot_data_json = None
        self._callback_data_json = None
        self._conversations_json = None
        if user_data_json:
            try:
                self._user_data = self._decode_user_chat_data_from_json(user_data_json)
                self._user_data_json = user_data_json
            except (ValueError, AttributeError) as exc:
                raise TypeError("Unable to deserialize user_data_json. Not valid JSON") from exc
        if chat_data_json:
            try:
                self._chat_data = self._decode_user_chat_data_from_json(chat_data_json)
                self._chat_data_json = chat_data_json
            except (ValueError, AttributeError) as exc:
                raise TypeError("Unable to deserialize chat_data_json. Not valid JSON") from exc
        if bot_data_json:
            try:
                self._bot_data = json.loads(bot_data_json)
                self._bot_data_json = bot_data_json
            except (ValueError, AttributeError) as exc:
                raise TypeError("Unable to deserialize bot_data_json. Not valid JSON") from exc
            if not isinstance(self._bot_data, dict):
                raise TypeError("bot_data_json must be serialized dict")
        if callback_data_json:
            try:
                data = json.loads(callback_data_json)
            except (ValueError, AttributeError) as exc:
                raise TypeError(
                    "Unable to deserialize callback_data_json. Not valid JSON"
                ) from exc
            # We are a bit more thorough with the checking of the format here, because it's
            # more complicated than for the other things
            try:
                if data is None:
                    self._callback_data = None
                else:
                    self._callback_data = cast(
                        CDCData,
                        ([(one, float(two), three) for one, two, three in data[0]], data[1]),
                    )
                self._callback_data_json = callback_data_json
            except (ValueError, IndexError) as exc:
                raise TypeError("callback_data_json is not in the required format") from exc
            if self._callback_data is not None and (
                not all(
                    isinstance(entry[2], dict) and isinstance(entry[0], str)
                    for entry in self._callback_data[0]
                )
                or not isinstance(self._callback_data[1], dict)
            ):
                raise TypeError("callback_data_json is not in the required format")

        if conversations_json:
            try:
                self._conversations = self._decode_conversations_from_json(conversations_json)
                self._conversations_json = conversations_json
            except (ValueError, AttributeError) as exc:
                raise TypeError(
                    "Unable to deserialize conversations_json. Not valid JSON"
                ) from exc

    @property
    def user_data(self) -> Optional[DefaultDict[int, Dict]]:
        """:obj:`dict`: The user_data as a dict."""
        return self._user_data

    @property
    def user_data_json(self) -> str:
        """:obj:`str`: The user_data serialized as a JSON-string."""
        if self._user_data_json:
            return self._user_data_json
        return json.dumps(self.user_data)

    @property
    def chat_data(self) -> Optional[DefaultDict[int, Dict]]:
        """:obj:`dict`: The chat_data as a dict."""
        return self._chat_data

    @property
    def chat_data_json(self) -> str:
        """:obj:`str`: The chat_data serialized as a JSON-string."""
        if self._chat_data_json:
            return self._chat_data_json
        return json.dumps(self.chat_data)

    @property
    def bot_data(self) -> Optional[Dict]:
        """:obj:`dict`: The bot_data as a dict."""
        return self._bot_data

    @property
    def bot_data_json(self) -> str:
        """:obj:`str`: The bot_data serialized as a JSON-string."""
        if self._bot_data_json:
            return self._bot_data_json
        return json.dumps(self.bot_data)

    @property
    def callback_data(self) -> Optional[CDCData]:
        """:class:`telegram.ext.utils.types.CDCData`: The meta data on the stored callback data.

        .. versionadded:: 13.6
        """
        return self._callback_data

    @property
    def callback_data_json(self) -> str:
        """:obj:`str`: The meta data on the stored callback data as a JSON-string.

        .. versionadded:: 13.6
        """
        if self._callback_data_json:
            return self._callback_data_json
        return json.dumps(self.callback_data)

    @property
    def conversations(self) -> Optional[Dict[str, ConversationDict]]:
        """:obj:`dict`: The conversations as a dict."""
        return self._conversations

    @property
    def conversations_json(self) -> str:
        """:obj:`str`: The conversations serialized as a JSON-string."""
        if self._conversations_json:
            return self._conversations_json
        return self._encode_conversations_to_json(self.conversations)  # type: ignore[arg-type]

    def get_user_data(self) -> DefaultDict[int, Dict[object, object]]:
        """Returns the user_data created from the ``user_data_json`` or an empty
        :obj:`defaultdict`.

        Returns:
            :obj:`defaultdict`: The restored user data.
        """
        if self.user_data is None:
            self._user_data = defaultdict(dict)
        return self.user_data  # type: ignore[return-value]

    def get_chat_data(self) -> DefaultDict[int, Dict[object, object]]:
        """Returns the chat_data created from the ``chat_data_json`` or an empty
        :obj:`defaultdict`.

        Returns:
            :obj:`defaultdict`: The restored chat data.
        """
        if self.chat_data is None:
            self._chat_data = defaultdict(dict)
        return self.chat_data  # type: ignore[return-value]

    def get_bot_data(self) -> Dict[object, object]:
        """Returns the bot_data created from the ``bot_data_json`` or an empty :obj:`dict`.

        Returns:
            :obj:`dict`: The restored bot data.
        """
        if self.bot_data is None:
            self._bot_data = {}
        return self.bot_data  # type: ignore[return-value]

    def get_callback_data(self) -> Optional[CDCData]:
        """Returns the callback_data created from the ``callback_data_json`` or :obj:`None`.

        .. versionadded:: 13.6

        Returns:
            Optional[:class:`telegram.ext.utils.types.CDCData`]: The restored meta data or
            :obj:`None`, if no data was stored.
        """
        if self.callback_data is None:
            self._callback_data = None
            return None
        return self.callback_data[0], self.callback_data[1].copy()

    def get_conversations(self, name: str) -> ConversationDict:
        """Returns the conversations created from the ``conversations_json`` or an empty
        :obj:`dict`.

        Returns:
            :obj:`dict`: The restored conversations data.
        """
        if self.conversations is None:
            self._conversations = {}
        return self.conversations.get(name, {}).copy()  # type: ignore[union-attr]

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.

        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """
        if not self._conversations:
            self._conversations = {}
        if self._conversations.setdefault(name, {}).get(key) == new_state:
            return
        self._conversations[name][key] = new_state
        self._conversations_json = None

    def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will update the user_data (if changed).

        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.user_data` ``[user_id]``.
        """
        if self._user_data is None:
            self._user_data = defaultdict(dict)
        if self._user_data.get(user_id) == data:
            return
        self._user_data[user_id] = data
        self._user_data_json = None

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will update the chat_data (if changed).

        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.chat_data` ``[chat_id]``.
        """
        if self._chat_data is None:
            self._chat_data = defaultdict(dict)
        if self._chat_data.get(chat_id) == data:
            return
        self._chat_data[chat_id] = data
        self._chat_data_json = None

    def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).

        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.bot_data`.
        """
        if self._bot_data == data:
            return
        self._bot_data = data
        self._bot_data_json = None

    def update_callback_data(self, data: CDCData) -> None:
        """Will update the callback_data (if changed).

        .. versionadded:: 13.6

        Args:
            data (:class:`telegram.ext.utils.types.CDCData`): The relevant data to restore
                :class:`telegram.ext.CallbackDataCache`.
        """
        if self._callback_data == data:
            return
        self._callback_data = (data[0], data[1].copy())
        self._callback_data_json = None

    def refresh_user_data(self, user_id: int, user_data: Dict) -> None:
        """Does nothing.

        .. versionadded:: 13.6
        .. seealso:: :meth:`telegram.ext.BasePersistence.refresh_user_data`
        """

    def refresh_chat_data(self, chat_id: int, chat_data: Dict) -> None:
        """Does nothing.

        .. versionadded:: 13.6
        .. seealso:: :meth:`telegram.ext.BasePersistence.refresh_chat_data`
        """

    def refresh_bot_data(self, bot_data: Dict) -> None:
        """Does nothing.

        .. versionadded:: 13.6
        .. seealso:: :meth:`telegram.ext.BasePersistence.refresh_bot_data`
        """

    def flush(self) -> None:
        """Does nothing.

        .. versionadded:: 14.0
        .. seealso:: :meth:`telegram.ext.BasePersistence.flush`
        """

    @staticmethod
    def _encode_conversations_to_json(conversations: Dict[str, Dict[Tuple, object]]) -> str:
        """Helper method to encode a conversations dict (that uses tuples as keys) to a
        JSON-serializable way. Use :meth:`self._decode_conversations_from_json` to decode.

        Args:
            conversations (:obj:`dict`): The conversations dict to transform to JSON.

        Returns:
            :obj:`str`: The JSON-serialized conversations dict
        """
        tmp: Dict[str, JSONDict] = {}
        for handler, states in conversations.items():
            tmp[handler] = {}
            for key, state in states.items():
                tmp[handler][json.dumps(key)] = state
        return json.dumps(tmp)

    @staticmethod
    def _decode_conversations_from_json(json_string: str) -> Dict[str, Dict[Tuple, object]]:
        """Helper method to decode a conversations dict (that uses tuples as keys) from a
        JSON-string created with :meth:`self._encode_conversations_to_json`.

        Args:
            json_string (:obj:`str`): The conversations dict as JSON string.

        Returns:
            :obj:`dict`: The conversations dict after decoding
        """
        tmp = json.loads(json_string)
        conversations: Dict[str, Dict[Tuple, object]] = {}
        for handler, states in tmp.items():
            conversations[handler] = {}
            for key, state in states.items():
                conversations[handler][tuple(json.loads(key))] = state
        return conversations

    @staticmethod
    def _decode_user_chat_data_from_json(data: str) -> DefaultDict[int, Dict[object, object]]:
        """Helper method to decode chat or user data (that uses ints as keys) from a
        JSON-string.

        Args:
            data (:obj:`str`): The user/chat_data dict as JSON string.

        Returns:
            :obj:`dict`: The user/chat_data defaultdict after decoding
        """
        tmp: DefaultDict[int, Dict[object, object]] = defaultdict(dict)
        decoded_data = json.loads(data)
        for user, user_data in decoded_data.items():
            user = int(user)
            tmp[user] = {}
            for key, value in user_data.items():
                try:
                    key = int(key)
                except ValueError:
                    pass
                tmp[user][key] = value
        return tmp
