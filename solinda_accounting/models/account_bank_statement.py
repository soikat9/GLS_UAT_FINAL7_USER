from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountBankStatement(models.Model):
  _inherit = 'account.bank.statement'

  balance_end_real = fields.Monetary('Ending Balance', states={'confirm': [('readonly', True)]}, compute='_compute_ending_balance', recursive=True, readonly=False, store=True, tracking=True)
  cash_type = fields.Selection([('disbursment', 'Disbursment'), ('receipt', 'Receipt')], string='Cash Type')

  @api.constrains('balance_end_real')
  def ending_balance_no_minus(self):
    for line in self:
      if line.balance_end_real < 0:
        raise ValidationError("Ending Balance can't be Negative")

  @api.onchange('balance_end')
  def _onchange_balance_end(self):
      for line in self:
          line.balance_end_real = line.balance_end

class AccountBankStatementLine(models.Model):
  _inherit = 'account.bank.statement.line'

  analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

  @api.onchange('amount')
  def negative_disbursment(self):
    for line in self:
      if line.statement_id.cash_type == 'disbursment':
        line.amount = -abs(line.amount)
      if line.statement_id.cash_type == 'receipt':
        line.amount = abs(line.amount)
