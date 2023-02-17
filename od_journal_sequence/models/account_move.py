# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        for move in self:
            name = move.name or "/"
            if (
                    move.state == "posted"
                    and (not move.name or move.name == "/")
                    and move.journal_id
                    and move.journal_id.sequence_id
            ):
                if (
                        move.move_type in ("out_refund", "in_refund")
                        and move.journal_id.type in ("sale", "purchase")
                        and move.journal_id.refund_sequence
                        and move.journal_id.refund_sequence_id
                ):
                    seq = move.journal_id.refund_sequence_id
                elif (
                        move.journal_id.type in ("bank", "cash")
                        and move.journal_id.out_sequence_id
                ):
                    if move.statement_id.cash_type == 'receipt':
                        seq = move.journal_id.sequence_id
                    elif move.statement_id.cash_type == 'disbursment':
                        seq = move.journal_id.out_sequence_id
                    else:
                        if move.move_type == "out_invoice":
                            raise ValidationError("Customer Invoice")
                            seq = move.journal_id.sequence_id
                        elif move.move_type == "in_invoice":
                            seq = move.journal_id.out_sequence_id
                else:
                    seq = move.journal_id.sequence_id
            name = seq.next_by_id(sequence_date=move.date)
            move.name = name

    def _constrains_date_sequence(self):
        return True

