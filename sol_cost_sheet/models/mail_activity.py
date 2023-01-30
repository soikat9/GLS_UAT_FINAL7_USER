from odoo import _, api, fields, models

class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'
    
    create_rab = fields.Boolean('Create RAB')

class MailActivity(models.Model):
    _inherit = 'mail.activity'
    _description = 'Mail Activity'
    
    def action_close_dialog(self):
        res = super(MailActivity, self).action_close_dialog()
        if self.activity_type_id.create_rab and self.res_model == 'crm.lead':
            crm_id = self.env["crm.lead"].search([("id", "=",self.res_id)])
            create_rab = self.env["cost.sheet"].create({"crm_id": self.res_id,'partner_id':crm_id.partner_id.id})
        return res