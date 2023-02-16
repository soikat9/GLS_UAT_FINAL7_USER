from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountBankStatement(models.Model):
  _inherit = 'account.bank.statement'

  name = fields.Char(compute="_compute_name_by_sequence",
                     string='Reference',
                     states={'open': [('readonly', False)]},
                     copy=False,
                     readonly=True)

  @api.depends("state", "journal_id", "date")
  def _compute_name_by_sequence(self):
      for line in self:
          name = line.name or "/"
          if (
                    line.state == "posted"
                    and (not line.name or line.name == "/")
                    and line.journal_id
                    and line.journal_id.sequence_id
            ):
                if line.cash_type == "receipt":
                    seq = line.journal_id.sequence_id
                elif (
                    line.cash_type == "disbursment"
                    and line.journal_id.out_sequence_id
                    ):
                    seq = line.journal_id.out_sequence_id
                name = seq.next_by_id(sequence_date=line.date)
          line.name = name

  def _constrains_date_sequence(self):
     return True