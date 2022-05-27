from odoo import api, fields, models


class WithholdingIGTF(models.Model):
	_name = 'withholding.igtf'
	_description = 'Withholding IGTF'

# 	name = fields.Char()
# 	withholding_date = fields.Date()
# 	state = fields.Selection([
# 		('draft', 'Draft'),
# 		('confirm', 'Confirm'),
# 		('cancel', 'Cancel')
# 	], default='draft')
# 	withholding_subject_id = fields.Many2one('res.partner')
# 	withholding_agent_id = fields.Many2one('res.partner')
# 	company_id = fields.Many2one('res.company',
# 		default=lambda self: self.env.company
# 	)
# 	currency_id = fields.Many2one('res.currency',
# 		related='company_id.currency_id',
# 		store=True
# 	)
# 	#line_ids = fields.One2many('withholding.igtf.line', 'withholding_id')
# 	total_base_amount = fields.Monetary()
# 	total_wh_amount = fields.Monetary()


# class WithholdingIGTFLine(models.Model):
# 	_name = 'withholding.igtf.line'
# 	_description = 'Withholding IGTF Line'

# 	withholding_id = fields.Many2one('withholding.igtf', ondelete='cascade')
# 	igtf_tax_id = fields.Many2one('account.tax')
# 	base_amount = fields.Monetary()
# 	wh_amount = fields.Monetary()
# 	company_id = fields.Many2one('res.company',
# 		related='withholding_id.company_id',
# 		store=True
# 	)
# 	currency_id = fields.Many2one('res.currency',
# 		related='withholding_id.currency_id',
# 		store=True
# 	)