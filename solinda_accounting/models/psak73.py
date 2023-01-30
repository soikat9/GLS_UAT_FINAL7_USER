from odoo import api, fields, models, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import ValidationError

_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Confirmed')
    ]

class Psak73(models.Model):
    _name = 'psak73.psak'
    _description = 'PSAK 73'

    name = fields.Char(string='Reference')
    state = fields.Selection(_STATES, string='Status', default='draft')
    location = fields.Many2one('stock.location', string='Location')
    start_contract = fields.Date('Start of Contract')
    end_contract = fields.Date('End of Contract')
    selling_price_ids = fields.One2many('selling.price', 'psak_id', string='Selling Price')
    addendum_ids = fields.One2many('addendum.addendum', 'psak_id', string='Addendum')
    min_year = fields.Float(string='Min Consumption (year)')
    min_month = fields.Float(string='Min Consumption (month)')
    addition_construction = fields.Float(string='Addition Construction')
    # start_adendum = fields.Date(string='Date from Adendum')
    # finish_adendum = fields.Date(string='Date to Adendum')
    # adendum = fields.Float(string='Adendum')
    eir_year = fields.Float(string='EIR (year)', help='Effective Interest Rate per year')
    eir_month = fields.Float(string='EIR (month)', help='Effective Interest Rate per month')
    pvmlp_lease_asset = fields.Float(string='PVMLP Lease Asset', help='Present Value Of Minimum Lease Payments')
    amortisation_ids = fields.One2many('amortisation.amortisation', 'psak_id', string='Amortisation')
    lease_receivable_account = fields.Many2one('account.account', string='Lease Receivable Account')
    revenue_account = fields.Many2one('account.account', string='Revenue Account')
    interest_income_account = fields.Many2one('account.account', string='Interest Income Account')
    analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account')
    is_addendum = fields.Boolean(string='Is Addendum', default=False)
    

    def confirm(self):
        return self.write({"state":"confirm"})
    
    def generate(self):
        years = self.end_contract.year - self.start_contract.year
        if self.start_contract.month == self.end_contract.month:
            months = years * 12
        elif self.start_contract.month < self.end_contract.month:
            months = years * 12 + (self.end_contract.month - self.start_contract.month)
        elif self.start_contract.month > self.end_contract.month:
            months = years * 12 - (self.start_contract.month - self.end_contract.month)

        for i in range(0,months + 1):
            period = self.start_contract + relativedelta(months =+ i)
            year = period.year
            month = period.month
            mdays = calendar.monthrange(year,month)[1]

            last_date = date(year,month,mdays)
            last_date_int = year * 100 + month

            if self.is_addendum:
                pass


            else:
                if i == 0:
                    self.env['amortisation.amortisation'].create({
                        'psak_id': self.id,
                        'period': last_date,
                        'period_int': last_date_int,
                        'period_n': i+1,
                        'interest_income': self.eir_month * self.addition_construction,
                        'deduction_inflow': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[i].price,
                        'balance': self.addition_construction + self.eir_month * self.addition_construction - self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[i].price,
                        'pv_lease_asset': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[i].price / (1+self.eir_month) ** (i+1),
                        'mlp_asset_service': self.selling_price_ids[i].price * self.min_month,
                        'pvmlp_asset_service': self.selling_price_ids[i].price * self.min_month /  (1+self.eir_month) ** (i+1),
                        'diff_receive_interest': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[i].price - self.eir_month * self.addition_construction,
                    })
                else:
                    self.env['amortisation.amortisation'].create({
                        'psak_id': self.id,
                        'period': last_date,
                        'period_int': last_date_int,
                        'period_n': i+1,
                        'interest_income': self.eir_month * self.amortisation_ids[i-1].balance,
                        'deduction_inflow': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[period.year - self.start_contract.year].price,
                        'balance': self.amortisation_ids[i-1].balance + self.eir_month * self.amortisation_ids[i-1].balance - self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[period.year - self.start_contract.year].price,
                        'pv_lease_asset': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[period.year - self.start_contract.year].price / (1+self.eir_month) ** (i+1),
                        'mlp_asset_service': self.selling_price_ids[period.year - self.start_contract.year].price * self.min_month,
                        'pvmlp_asset_service': self.selling_price_ids[period.year - self.start_contract.year].price * self.min_month / (1 + self.eir_month) ** (i+1),
                        'diff_receive_interest': self.pvmlp_lease_asset * self.min_month * self.selling_price_ids[period.year - self.start_contract.year].price - self.eir_month * self.amortisation_ids[i-1].balance,
                    })

    @api.onchange('min_year')
    def onchange_minimum_consumption_per_month(self):
        if self.min_year:
            minimum_consumption_per_month = self.min_year / 12
            self.write({'min_month': minimum_consumption_per_month})
        else:
            self.write({'min_month': 0.00})

    @api.onchange('eir_year')
    def onchange_eir_month(self):
        if self.eir_year:
            eir_month = self.eir_year / 12
            self.write({'eir_month': eir_month})
        else:
            self.write({'eir_month': 0.00})

    @api.onchange('start_contract', 'end_contract')
    def generate_selling_price(self):
        if self.start_contract and self.end_contract:
            if self.selling_price_ids:
                self.selling_price_ids = [(5, 0)]
            year = self.end_contract.year - self.start_contract.year
            start_contract_year = self.start_contract.year
            for i in range(1, year+2):
                self.selling_price_ids = [(0, 0, {'no_sequence': i, 'no_year': start_contract_year})]
                start_contract_year += 1
    
    @api.onchange('addendum_ids')
    def onchange_addendum(self):
        for line in self:
            if len(line.addendum_ids) > 0:
                line.is_addendum = True
            else:
                line.is_addendum = False

class SellingPrice(models.Model):
    _name = 'selling.price'
    _description = 'Selling Price PSAK 73'

    psak_id = fields.Many2one('psak73.psak', string='PSAK 73')
    no_sequence = fields.Integer(string='Year')
    no_year = fields.Integer(string='No Year')
    price = fields.Float(string='Price')

class Addendum(models.Model):
    _name = 'addendum.addendum'
    _description = 'Addendum'

    psak_id = fields.Many2one('psak73.psak', string='PSAK 73')
    start_addendum = fields.Date(string='Start Date')
    finish_addendum = fields.Date(string='End Date')
    addendum = fields.Float(string='Addendum', default=0)
    months = fields.Integer(string='Month(s)', compute="_compute_months_addendum")
    periods_ids = fields.Many2many('period.addendum', string='Periods')

    @api.constrains('start_addendum', 'finish_addendum')
    def date_constrains(self):
        for ad in self:
            if ad.finish_addendum < ad.start_addendum:
                raise ValidationError(_('End Date Must be greater Than Start Date.'))
            if ad.start_addendum < ad.psak_id.start_contract or ad.start_addendum > ad.psak_id.end_contract:
                raise ValidationError(_('Start Addendum is out of range of Contract Date.'))
            if ad.finish_addendum < ad.psak_id.start_contract or ad.finish_addendum > ad.psak_id.end_contract:
                raise ValidationError(_('End Addendum is out of range of Contract Date.'))

        '''
        Check interleaving between fiscal years.
        There are 3 cases to consider:
        s1   s2   e1   e2
        (    [----)----]
        s2   s1   e2   e1
        [----(----]    )
        s1   s2   e2   e1
        (    [----]    )
        '''
        for fy in self:
            # Starting date must be prior to the ending date
            domain = [
                ('id', '!=', fy.id),
                ('psak_id', '=', fy.psak_id.id),
                '|', '|',
                '&', ('start_addendum', '<', fy.start_addendum), ('finish_addendum', '>', fy.start_addendum),
                '&', ('start_addendum', '<', fy.finish_addendum), ('finish_addendum', '>', fy.finish_addendum),
                '&', ('start_addendum', '<=', fy.start_addendum), ('finish_addendum', '>=', fy.finish_addendum),
            ]

            if self.search_count(domain) > 0:
                raise ValidationError(_('You can not have an overlap between two addendum dates, please correct the start and/or end dates of your addendum dates.'))

    @api.depends('start_addendum','finish_addendum')
    def _compute_months_addendum(self):
        year_addendum = self.finish_addendum.year - self.start_addendum.year
        if self.start_addendum.month == self.finish_addendum.month:
            self.months = year_addendum * 12
        elif self.start_addendum.month < self.finish_addendum.month:
            self.months = year_addendum * 12 + (self.finish_addendum.month - self.start_addendum.month)
        elif self.start_addendum.month > self.finish_addendum.month:
            self.months = year_addendum * 12 - (self.start_addendum.month - self.finish_addendum.month)
        else:
            self.months = False
    
    @api.onchange('psak_id.start_contract', 'start_addendum', 'finish_addendum', 'months')
    def _onchange_periods_addendum(self):
        for line in self:
            first_year = line.start_addendum.year - line.psak_id.start_contract.year
            if line.start_addendum.month == line.psak_id.start_contract.month:
                first_months = first_year * 12
            elif line.start_addendum.month < line.psak_id.start_contract.month:
                first_months = first_year * 12 + (line.psak_id.start_contract.month - line.start_addendum.month)
            elif line.start_addendum.month > line.psak_id.start_contract.month:
                first_months = first_year * 12 - (line.start_addendum.month - line.psak_id.start_contract.month)

            for i in range(first_months,line.months):
                line.periods_ids = [(0, 0, {'period': i})]

class PeriodAddendum(models.Model):
    _name = 'period.addendum'
    _description = 'Period Addendum'

    period = fields.Integer(string='Period')

class Amortisation(models.Model):
    _name = 'amortisation.amortisation'
    _description = 'Amortisation'
    
    state = fields.Selection([('unposted', 'Unposted'), ('posted', 'Posted')])
    psak_id = fields.Many2one('psak73.psak', string='PSAK 73')
    period = fields.Date(string='Period')
    period_int = fields.Integer(string='Period Integer')
    interest_income = fields.Float(string='Interest Income')
    deduction_inflow = fields.Float(string='Deduction Cash Inflow')
    balance = fields.Float(string='Balance')
    period_n = fields.Integer(string='Period (n)')
    pv_lease_asset = fields.Float(string='PV Lease Asset')
    mlp_asset_service = fields.Float(string='MLP Asset + Service')
    pvmlp_asset_service = fields.Float(string='PVMLP Asset + Service')
    diff_receive_interest = fields.Float(string='Difference Cash Receive and Interest')
    journal_ref = fields.Char(strng='Journal Reference')
    current_time = fields.Date(string='Current time', default=datetime.today())
    current_date_int = fields.Integer(string="Date Integer", compute='_compute_current_date_to_int', store=True)
    show_button = fields.Boolean(string='Show Button', default=True, compute='_compute_comparing_date')


    # def _get_current_time(self):
    #     for li in self:
    #         li.current_time = datetime.today()

    @api.depends('current_time')
    def _compute_current_date_to_int(self):
        for line in self:
            year = line.current_time.year
            month = line.current_time.month
            line.current_date_int = year * 100 + month

    @api.depends('current_date_int', 'period_int')
    def _compute_comparing_date(self):
        for line in self:
            if line.current_date_int > line.period_int:
                line.show_button = False
            else:
                line.show_button = True


    def transfer_to_journal(self):
        return self.write({"state":"posted"})