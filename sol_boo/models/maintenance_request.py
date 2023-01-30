from datetime import datetime
from odoo import _, api, fields, models
from dateutil import relativedelta

class SparePartList(models.Model):
    _name = 'spare.part.list'
    _description = 'Spare Part List'
    
    name = fields.Char('Part Number',related='product_id.part_no',readonly=False)
    product_id = fields.Many2one('product.product', string='Spare Part')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    
    def open_product(self):
        return {
                'name': 'Product',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'product.product',
                'res_id':self.product_id.id
            }

class HistoryEquipmentUsage(models.Model):
    _name = 'history.equipment.usage'
    _description = 'History Equipment Usage'
    
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    from_time = fields.Datetime('From')
    to_time = fields.Datetime('To')
    notes = fields.Text('Notes')
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance')

class EquipmentType(models.Model):
    _name = 'equipment.type'
    _description = 'Equipment Type'
    
    name = fields.Char('Name')
    # no_type = fields.Char('No Type')
    # capacity = fields.Char('Capacity')
    # head = fields.Char('Head')
    # power = fields.Char('Power')

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    location_id = fields.Many2one('stock.location', string='Location')   
    spare_part_ids = fields.One2many('spare.part.list', 'equipment_id', string='Spare Part')
    equipment_type_id = fields.Many2one('equipment.type', string='Equipment Type')
    no_type = fields.Char('No Type')
    capacity = fields.Char('Capacity')
    head = fields.Char('Head')
    power = fields.Char('Power')
    # no_type = fields.Char('No Type',related="equipment_type_id.no_type",readonly=False)
    # capacity = fields.Char('Capacity',related="equipment_type_id.capacity",readonly=False)
    # head = fields.Char('Head',related="equipment_type_id.head",readonly=False)
    # power = fields.Char('Power',related="equipment_type_id.power",readonly=False)

class ActionPlanMaintenance(models.Model):
    _name = 'action.plan.maintenance'
    _description = 'Action Plan Maintenance'
    
    name = fields.Char('Plan')
    due_date = fields.Datetime('Due Date')
    status = fields.Selection([
        ('open', 'Open'),
        ('op', 'On Progress'),
        ('done', 'Done'),
    ], string='status',default="open")
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance')

class ProgresHistoryMaintenance(models.Model):
    _name = 'progres.history.maintenance'
    _description = 'Progres History Maintenance'
    
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    stage_from = fields.Char('Stage From')
    stage_to = fields.Char('Stage To')
    duration = fields.Char(compute='_compute_duration', string='Duration')
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance')
    
    @api.depends('start_date','end_date')
    def _compute_duration(self):
        for i in self:
            if i.start_date and i.end_date:
                diff = relativedelta.relativedelta(i.end_date, i.start_date)
                years = diff.years
                months = diff.months
                days = diff.days
                hours = diff.hours
                minutes = diff.minutes
                if years > 0:
                    i.duration = str(years) + " Year " + str(months) + " month " + str(days) + " day" + str(hours) + " jam " + str(minutes) + " menit"
                elif months > 0:
                    i.duration = str(months) + " Month " + str(days) + " day " + str(hours) + " hour " + str(minutes) + " menit"
                elif days > 0:
                    i.duration = str(days) + " Days " + str(hours) + " hours " + str(minutes) + " minutes"
                elif hours > 0:
                    i.duration = str(hours) + " hours " + str(minutes) + " minutes"
                else:
                    i.duration =str(minutes) + " minutes " + str(diff.seconds) + " seconds"
            else:
                i.duration = False

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Maintenance Request'
    
    equipment_history_line = fields.One2many('history.equipment.usage', 'maintenance_id', string='Equipment History')
    progres_history_line = fields.One2many('progres.history.maintenance', 'maintenance_id', string='Progress History')
    action_plan_line = fields.One2many('action.plan.maintenance', 'maintenance_id', string='Action Plan')
    shutdown_id = fields.Many2one('shutdown.system', string='Shutdown')
    job_order_id = fields.Many2one('job.order.request', string='Job Order') 
    location_id = fields.Many2one('stock.location', string='Location')
    mr_ids = fields.One2many('stock.picking', 'maintenance_id', string='MR')
    mr_count = fields.Integer(compute='_compute_mr_count', string='MR')

    change_stage_time = fields.Datetime('Change Stage Time')
    duration_change_stage = fields.Char(compute='_compute_duration_change_stage', string='Duration')
    
    def write(self, vals):
        phl = None
        if 'stage_id' in vals:
            phl = self.env['progres.history.maintenance'].sudo().create({
                "maintenance_id" : self.id,
                "start_date" : self.change_stage_time,
                "stage_from" : self.stage_id.name
            })
        res = super(MaintenanceRequest, self).write(vals)
        if 'stage_id' in vals and phl:
            phl.write({
                "end_date" : fields.datetime.now(),
                "stage_to" : self.stage_id.name
            })
            self.change_stage_time = fields.datetime.now()
        return res


    # @api.depends('change_stage_time')
    def _compute_duration_change_stage(self):
        now = fields.datetime.now()
        for i in self:
            if i.change_stage_time:
                diff = relativedelta.relativedelta(i.change_stage_time, now)
                years = abs(diff.years)
                months = abs(diff.months)
                days = abs(diff.days)
                hours = abs(diff.hours)
                minutes = abs(diff.minutes)
                if years > 0:
                    i.duration_change_stage = str(years) + " Year " + str(months) + " Month " + str(days) + " Day" + str(hours) + " Hours "
                elif months > 0:
                    i.duration_change_stage = str(months) + " Month " + str(days) + " Day " + str(hours) + " Hour "
                elif days > 0:
                    i.duration_change_stage = str(days) + " Day " + str(hours) + " Hour "
                else:
                    i.duration_change_stage = str(hours) + " Hour "
            else:
                i.duration_change_stage = 'The changes stage time is not defined!'

    @api.onchange('stage_id')
    def _onchange_stages_id(self):
        for i in self:
            i.change_stage_time = fields.datetime.now()

    @api.depends('mr_ids')
    def _compute_mr_count(self):
        for i in self:
            i.mr_count = len(i.mr_ids)

    def create_open_mr(self):
         return {
                'name': 'Material Request',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,kanban,form,calendar,map',
                'res_model': 'stock.picking',
                'context': {'default_company_id': self.env.company.id,'default_maintenance_id':self.id},
                'domain': [('maintenance_id','=',self.id)],
            }
