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
import pytest

from telegram import Update, User, PreCheckoutQuery, OrderInfo, Bot
from tests.conftest import check_shortcut_call, check_shortcut_signature, check_defaults_handling


@pytest.fixture(scope='class')
def pre_checkout_query(bot):
    return PreCheckoutQuery(
        TestPreCheckoutQuery.id_,
        TestPreCheckoutQuery.from_user,
        TestPreCheckoutQuery.currency,
        TestPreCheckoutQuery.total_amount,
        TestPreCheckoutQuery.invoice_payload,
        shipping_option_id=TestPreCheckoutQuery.shipping_option_id,
        order_info=TestPreCheckoutQuery.order_info,
        bot=bot,
    )


class TestPreCheckoutQuery:
    id_ = 5
    invoice_payload = 'invoice_payload'
    shipping_option_id = 'shipping_option_id'
    currency = 'EUR'
    total_amount = 100
    from_user = User(0, '', False)
    order_info = OrderInfo()

    def test_slot_behaviour(self, pre_checkout_query, mro_slots):
        inst = pre_checkout_query
        for attr in inst.__slots__:
            assert getattr(inst, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert len(mro_slots(inst)) == len(set(mro_slots(inst))), "duplicate slot"

    def test_de_json(self, bot):
        json_dict = {
            'id': self.id_,
            'invoice_payload': self.invoice_payload,
            'shipping_option_id': self.shipping_option_id,
            'currency': self.currency,
            'total_amount': self.total_amount,
            'from': self.from_user.to_dict(),
            'order_info': self.order_info.to_dict(),
        }
        pre_checkout_query = PreCheckoutQuery.de_json(json_dict, bot)

        assert pre_checkout_query.bot is bot
        assert pre_checkout_query.id == self.id_
        assert pre_checkout_query.invoice_payload == self.invoice_payload
        assert pre_checkout_query.shipping_option_id == self.shipping_option_id
        assert pre_checkout_query.currency == self.currency
        assert pre_checkout_query.from_user == self.from_user
        assert pre_checkout_query.order_info == self.order_info

    def test_to_dict(self, pre_checkout_query):
        pre_checkout_query_dict = pre_checkout_query.to_dict()

        assert isinstance(pre_checkout_query_dict, dict)
        assert pre_checkout_query_dict['id'] == pre_checkout_query.id
        assert pre_checkout_query_dict['invoice_payload'] == pre_checkout_query.invoice_payload
        assert (
            pre_checkout_query_dict['shipping_option_id'] == pre_checkout_query.shipping_option_id
        )
        assert pre_checkout_query_dict['currency'] == pre_checkout_query.currency
        assert pre_checkout_query_dict['from'] == pre_checkout_query.from_user.to_dict()
        assert pre_checkout_query_dict['order_info'] == pre_checkout_query.order_info.to_dict()

    def test_answer(self, monkeypatch, pre_checkout_query):
        def make_assertion(*_, **kwargs):
            return kwargs['pre_checkout_query_id'] == pre_checkout_query.id

        assert check_shortcut_signature(
            PreCheckoutQuery.answer, Bot.answer_pre_checkout_query, ['pre_checkout_query_id'], []
        )
        assert check_shortcut_call(
            pre_checkout_query.answer,
            pre_checkout_query.bot,
            'answer_pre_checkout_query',
        )
        assert check_defaults_handling(pre_checkout_query.answer, pre_checkout_query.bot)

        monkeypatch.setattr(pre_checkout_query.bot, 'answer_pre_checkout_query', make_assertion)
        assert pre_checkout_query.answer(ok=True)

    def test_equality(self):
        a = PreCheckoutQuery(
            self.id_, self.from_user, self.currency, self.total_amount, self.invoice_payload
        )
        b = PreCheckoutQuery(
            self.id_, self.from_user, self.currency, self.total_amount, self.invoice_payload
        )
        c = PreCheckoutQuery(self.id_, None, '', 0, '')
        d = PreCheckoutQuery(
            0, self.from_user, self.currency, self.total_amount, self.invoice_payload
        )
        e = Update(self.id_)

        assert a == b
        assert hash(a) == hash(b)
        assert a is not b

        assert a == c
        assert hash(a) == hash(c)

        assert a != d
        assert hash(a) != hash(d)

        assert a != e
        assert hash(a) != hash(e)
