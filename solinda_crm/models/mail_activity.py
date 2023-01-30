# action_feedback
from odoo import _, api, fields, models
from odoo.tools.misc import clean_context
from odoo.exceptions import ValidationError

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_done_schedule_next(self):
        self = self.sudo()
        if self.res_model == 'crm.lead':
            crm_id = self.env["crm.lead"].search([("id", "=",self.res_id)])
            if crm_id.user_id.employee_id.parent_id.id != self.env.user.employee_id.id:
                raise ValidationError("Only sales manager can use this action!")
            # if crm_id.type == 'opportunity':
            case = ['PO Received','Contract Signed','Contract Signed / PO Received','11. Contract Signed / PO Received','11.Contract Signed / PO Received']
            if any(self.activity_type_id.name in n for n in case):
                crm_id.is_po_receive = True
            if self.activity_type_id.id not in crm_id.activity_type_done_ids.ids:
                crm_id.update({'activity_type_done_ids': [(4, self.activity_type_id.id)]})
                progress = self.activity_type_id.progress * 100
                prob_comp = crm_id.probability + progress
                crm_id.additional_prob = progress
                crm_id.automated_probability += progress
                crm_id.probability += progress
                crm_id._compute_stage_id()
        return super(MailActivity, self).action_done_schedule_next()
        
    
    def action_done(self):
        self = self.sudo()
        if self.res_model == 'crm.lead':
            crm_id = self.env["crm.lead"].search([("id", "=",self.res_id)])
            if crm_id.user_id.employee_id.parent_id.id != self.env.user.employee_id.id:
                raise ValidationError("Only sales manager can use this action!")
            # if crm_id.type == 'opportunity':
            if self.activity_type_id.id not in crm_id.activity_type_done_ids.ids:
                crm_id.update({'activity_type_done_ids': [(4, self.activity_type_id.id)]})
                progress = self.activity_type_id.progress * 100
                prob_comp = crm_id.probability + progress
                crm_id.additional_prob = progress
                crm_id.automated_probability += progress
                crm_id.probability += progress
                crm_id._compute_stage_id()
            case = ['PO Received','Contract Signed','Contract Signed / PO Received','11. Contract Signed / PO Received','11.Contract Signed / PO Received','10. Contract Signed / PO Received','10.Contract Signed / PO Received']
            if any(self.activity_type_id.name in n for n in case):
                crm_id.is_po_receive = True
        res = super(MailActivity, self).action_done()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }

    
    
    def action_feedback(self, feedback=False, attachment_ids=None):
        if self.res_model == 'crm.lead':
            crm_id = self.env[self.res_model].browse(self.res_id)
            # if crm_id.type == 'opportunity':
            case = ['PO Received','Contract Signed','Contract Signed / PO Received','11. Contract Signed / PO Received','11.Contract Signed / PO Received']
            if any(self.activity_type_id.name in n for n in case):
                crm_id.is_po_receive = True

            if crm_id.user_id.employee_id.parent_id.id != self.env.user.employee_id.id:
                raise ValidationError("Only sales manager can use this action!")

            if self.activity_type_id.id not in crm_id.activity_type_done_ids.ids:
                crm_id.update({'activity_type_done_ids': [(4, self.activity_type_id.id)]})    
                progress = self.activity_type_id.progress * 100
                crm_id.probability += progress
                crm_id.automated_probability += progress
                crm_id._compute_stage_id()

        res = super().action_feedback(feedback=False, attachment_ids=None)
        return res

    
    def action_close_dialog(self):
        res = super(MailActivity, self).action_close_dialog()
        case = ['PO Received','Contract Signed','Contract Signed / PO Received','11. Contract Signed / PO Received','11.Contract Signed / PO Received']
        if any(self.activity_type_id.name in n for n in case) and self.res_model == 'crm.lead':
            crm_id = self.env["crm.lead"].search([("id", "=",self.res_id)])
            # if crm_id.type == 'opportunity':
            crm_id.is_po_receive = True
        return res
        