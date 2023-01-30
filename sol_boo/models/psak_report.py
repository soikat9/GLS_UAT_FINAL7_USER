from odoo import _, api, fields, models
from datetime import datetime, date
import io
import base64
from odoo.exceptions import UserError, ValidationError
from dateutil import relativedelta
from calendar import month_abbr

class SellingPricePsak(models.Model):
    _name = 'selling.price.psak'
    _description = 'Selling Price PSAK'

    no_sequence = fields.Integer(string='Year')
    no_year = fields.Integer(string='No Year')
    price = fields.Float(string='Price')
    psak_report_id = fields.Many2one('psak.report', string='PSAK Report', ondelete='cascade')

class PsakReport(models.Model):
    _name = 'psak.report'
    _description = 'PSAK 73 Report'

    warehouse_id = fields.Many2one('stock.location', string='Nama BOO',domain=[("usage", "=", "internal")])
    date_from = fields.Date('Start Of Contract')
    date_to = fields.Date('End Of Contract')
    minimum_consumption_per_year = fields.Float(string='Min Consum Year')
    minimum_consumption_per_month = fields.Float(string='Min Consum Month')
    adendum = fields.Float(string='Adendum')
    date_from_adendum = fields.Date(string='Date From Adendum')
    date_to_adendum = fields.Date(string='Date To Adendum')
    addition_construction = fields.Float(string='Addition Construction')
    eir_year = fields.Float(string='EIR Year (%)')
    eir_month = fields.Float(string='EIR Month (%)')
    pvmlp_lease_asset = fields.Float(string='PVMLP Lease Asset (%)')
    selling_price_ids = fields.One2many('selling.price.psak', 'psak_report_id', string='Selling Price')  

    @api.onchange('minimum_consumption_per_year')
    def onchange_minimum_consumption_per_month(self):
        if self.minimum_consumption_per_year:
            minimum_consumption_per_month = self.minimum_consumption_per_year / 12
            self.write({'minimum_consumption_per_month': minimum_consumption_per_month})
        else:
            self.write({'minimum_consumption_per_month': 0.00})

    @api.onchange('eir_year')
    def onchange_eir_month(self):
        if self.eir_year:
            eir_month = self.eir_year / 12
            self.write({'eir_month': eir_month})
        else:
            self.write({'eir_month': 0.00})

    @api.onchange('date_from', 'date_to')
    def generate_selling_price(self):
        if self.date_from and self.date_to:
            if self.selling_price_ids:
                self.selling_price_ids = [(5, 0)]
            year = self.date_to.year - self.date_from.year
            date_from_year = self.date_from.year
            for i in range(1, year+2):
                self.selling_price_ids = [(0, 0, {'no_sequence': i, 'no_year': date_from_year})]
                date_from_year += 1

    def download_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'psak.report'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        start_month = self.date_from.month
        start_year = self.date_from.year
        end_month = self.date_to.month
        end_year = self.date_to.year

        adendum_start_month = self.date_from_adendum.month
        adendum_start_year = self.date_from_adendum.year
        adendum_end_month = self.date_to_adendum.month
        adendum_end_year = self.date_to_adendum.year

        list_data = []
        while True:
            is_adendum = False
            if adendum_start_month <= start_month <= adendum_end_month and adendum_start_year <= start_year <= adendum_end_year:
                is_adendum = True
            elif start_month <= adendum_start_month and adendum_start_year < start_year <= adendum_end_year:
                is_adendum = True
            elif start_month >= adendum_end_month and adendum_start_year <= start_year < adendum_end_year:
                is_adendum = True
            else:
                is_adendum = False
            dict_data = {}
            dict_data['month'] = start_month
            dict_data['year'] = start_year
            dict_data['is_adendum'] = is_adendum
            list_data.append(dict_data)
            if start_month == 12:
                start_month = 0
                start_year += 1
            if start_month == end_month and start_year == end_year:
                break
            start_month += 1
        datas['list_of_month_year'] = list_data
        datas['sum_column'] = ((self.date_to.year - self.date_from.year) * 12) + (self.date_to.month - self.date_from.month) + 1
        return self.env.ref('sol_boo.psak_report_xlsx').report_action(self, data=datas)


class PsakReportExcel(models.AbstractModel):
    _name = 'report.sol_boo.psak_report_excel.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        formatHeaderCompany = workbook.add_format({'font_size': 12, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#E3CAAF', 'text_wrap': True, 'border': 1})
        formatStringTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'text_wrap': True, 'border': 1})
        formatStringTableRight = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'right', 'text_wrap': True, 'border': 1})
        formatCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0_-;-"Rp"* #,##0_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})


        data_from = data['form']
        title = self.env['stock.location'].sudo().browse(data_from['warehouse_id']).display_name
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 13)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 18)
        sheet.set_column(8, 8, 18)
        sheet.set_column(9, 9, 18)
        sheet.set_column(10, 10, 18)

        header_title = 'FINANCE LEASE ASSESMENT (PSAK 73)'
        sheet.merge_range(1, 1, 1, 10, header_title, formatHeaderCompany)
        selling_price_ids = self.env['selling.price.psak'].sudo().search([('id', 'in', data_from['selling_price_ids'])])

        sheet.merge_range(3, 1, 3, 5, 'Amortisation Table', formatHeaderTable)
        sheet.write(3, 6, '', formatHeaderTable)
        sheet.write(3, 7, '', formatHeaderTable)
        sheet.write(3, 8, '', formatHeaderTable)
        sheet.write(3, 9, '', formatHeaderTable)
        sheet.write(3, 10, '', formatHeaderTable)
        sheet.write(4, 1, 'Period', formatHeaderTable)
        sheet.write(4, 2, 'Addition Construction', formatHeaderTable)
        sheet.write(4, 3, 'Interest Income', formatHeaderTable)
        sheet.write(4, 4, 'Deduction Cash Inflow', formatHeaderTable)
        sheet.write(4, 5, 'Balance', formatHeaderTable)
        sheet.write(4, 6, 'Period', formatHeaderTable)
        sheet.write(4, 7, 'PV Lease Asset', formatHeaderTable)
        sheet.write(4, 8, 'MLP Asset + Service', formatHeaderTable)
        sheet.write(4, 9, 'PVMLP Asset + Service', formatHeaderTable)
        sheet.write(4, 10, 'Difference Cash Receive and Interest', formatHeaderTable)

        balance = data_from['addition_construction']
        sheet.write(5, 1, '', formatStringTable)
        sheet.write(5, 2, balance, formatCurrencyTable)
        sheet.write(5, 3, '', formatStringTable)
        sheet.write(5, 4, '', formatStringTable)
        sheet.write(5, 5, balance, formatCurrencyTable)
        sheet.write(5, 6, '', formatStringTable)
        sheet.write(5, 7, '', formatStringTable)
        sheet.write(5, 8, '', formatStringTable)
        sheet.write(5, 9, '', formatStringTable)
        sheet.write(5, 10, '', formatStringTable)

        row = 6
        seq_period = 1
        for dt in data['list_of_month_year']:
            selling_price = selling_price_ids.filtered(lambda x: x.no_year == dt['year']).price
            pvmlp_lease_asset = data_from['pvmlp_lease_asset'] / 100
            eir_month = data_from['eir_year'] / 12 / 100
            min_consum_month = data_from['minimum_consumption_per_year'] / 12
            str_year = str(dt['year'])
            str_month = str(month_abbr[dt['month']])

            period = f'{str_month} - {str_year}'
            interest_income = eir_month * balance

            if dt['is_adendum']:
                ded_cash_inflow =  pvmlp_lease_asset * selling_price * data_from['adendum']
            elif dt['month'] == 1 and dt['year'] == 2022:
                ded_cash_inflow = pvmlp_lease_asset * 7500 * min_consum_month
            else :
                ded_cash_inflow = pvmlp_lease_asset * selling_price * min_consum_month

            balance = balance + interest_income - ded_cash_inflow

            if dt['is_adendum']:
                mlp_asset = selling_price * data_from['adendum'] 
            elif dt['month'] == 1 and dt['year'] == 2022:
                mlp_asset = 7500 * min_consum_month
            else :
                mlp_asset = selling_price * min_consum_month

            pvmlp_asset = mlp_asset / (1+ eir_month) ** seq_period
            diff_cash = ded_cash_inflow - interest_income

            sheet.write(row, 1, period, formatStringTableRight)
            sheet.write(row, 2, '', formatStringTable)
            sheet.write(row, 3, interest_income, formatCurrencyTable)
            sheet.write(row, 4, ded_cash_inflow, formatCurrencyTable)
            sheet.write(row, 5, balance, formatCurrencyTable)
            sheet.write(row, 6, seq_period, formatStringTable)
            sheet.write(row, 7, ded_cash_inflow, formatCurrencyTable)
            sheet.write(row, 8, mlp_asset, formatCurrencyTable)
            sheet.write(row, 9, pvmlp_asset, formatCurrencyTable)
            sheet.write(row, 10, diff_cash, formatCurrencyTable)
            seq_period += 1
            row += 1