# from odoo import models, fields, api
# from odoo.tools.safe_eval import safe_eval

# class DashboardComponent(models.Model):
#     _name = "dashboard.custom.component"
#     _description = "Dashboard Component"
    
#     name = fields.Char("Component Name", required=True)
#     content = fields.Html("Widget Content")
#     component_type = fields.Selection([
#         ('chart', 'Chart'),
#         ('kpi', 'KPI'),
#         ('list', 'List'),
#         ('custom', 'Custom'),
#         ('card', 'Card')
#     ], string="Component Type", default='custom')
#     is_active = fields.Boolean("Active", default=True)
#     sequence = fields.Integer("Sequence", default=10)
    
#     # Fields for card type
#     icon = fields.Char("Icon Class", help="Font Awesome icon class (e.g., 'fa fa-users')")
#     card_value = fields.Char("Card Value", help="Value to display on the card")
#     card_subtitle = fields.Char("Card Subtitle", help="Small text below the value")
#     card_color = fields.Selection([
#         ('primary', 'Blue'),
#         ('success', 'Green'),
#         ('warning', 'Yellow'),
#         ('info', 'Light Blue'),
#         ('danger', 'Red'),
#         ('secondary', 'Gray'),
#     ], string="Card Color", default='primary')
    
#     # Dynamic data source fields
#     model_id = fields.Many2one('ir.model', string="Data Model")
#     count_field = fields.Char("Count Field", help="Field to count or use for calculation")
#     domain = fields.Char("Filter Domain", default="[]", help="Domain filter in Python list format")
#     calculation_type = fields.Selection([
#         ('count', 'Count Records'),
#         ('sum', 'Sum Field'),
#         ('avg', 'Average Field'),
#         ('formula', 'Custom Formula')
#     ], string="Calculation Type", default='count')
#     formula = fields.Char("Custom Formula", help="Python expression for custom calculation")
    
#     @api.onchange('model_id')
#     def _onchange_model_id(self):
#         self.count_field = False
    
#     def _compute_card_data(self):
#         """Compute the data to be displayed on the card"""
#         self.ensure_one()
#         if not self.model_id:
#             return self.card_value or "0"
            
#         model_name = self.model_id.model
#         model = self.env[model_name]
        
#         # Use safer domain evaluation with proper error handling
#         try:
#             # For simple domains, use literal_eval
#             if self.domain and self.domain != "[]":
#                 domain = safe_eval(self.domain)
#             else:
#                 domain = []
#         except Exception as e:
#             return f"Domain Error: {str(e)[:20]}"
        
#         try:
#             if self.calculation_type == 'count':
#                 return str(model.search_count(domain))
#             elif self.calculation_type in ['sum', 'avg'] and self.count_field:
#                 records = model.search(domain)
#                 if not records:
#                     return "0"
                
#                 # Safely get field values
#                 try:
#                     values = records.mapped(self.count_field)
#                     if not values:
#                         return "0"
                        
#                     if self.calculation_type == 'sum':
#                         total = sum(values)
#                         return str(total)
#                     else:  # avg
#                         avg = sum(values) / len(values) if values else 0
#                         return str(round(avg, 1))
#                 except Exception as e:
#                     return f"Field Error: {str(e)[:20]}"
            
#             return self.card_value or "0"
#         except Exception as e:
#             return f"Error: {str(e)[:20]}"

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class DashboardComponent(models.Model):
    _name = "dashboard.custom.component"
    _description = "Dashboard Component"
    
    name = fields.Char("Component Name", required=True)
    content = fields.Html("Widget Content")
    component_type = fields.Selection([
        ('chart', 'Chart'),
        ('kpi', 'KPI'),
        ('list', 'List'),
        ('custom', 'Custom'),
        ('card', 'Card'),
        ('inclue_stats', 'iN-Clue Statistics')  # Added new option
    ], string="Component Type", default='custom')
    is_active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", default=10)
    
    # Fields for card type
    icon = fields.Char("Icon Class", help="Font Awesome icon class (e.g., 'fa fa-users')")
    card_value = fields.Char("Card Value", help="Value to display on the card")
    card_subtitle = fields.Char("Card Subtitle", help="Small text below the value")
    card_color = fields.Selection([
        ('primary', 'Blue'),
        ('success', 'Green'),
        ('warning', 'Yellow'),
        ('info', 'Light Blue'),
        ('danger', 'Red'),
        ('secondary', 'Gray'),
    ], string="Card Color", default='primary')
    
    # Dynamic data source fields
    model_id = fields.Many2one('ir.model', string="Data Model")
    count_field = fields.Char("Count Field", help="Field to count or use for calculation")
    domain = fields.Char("Filter Domain", default="[]", help="Domain filter in Python list format")
    calculation_type = fields.Selection([
        ('count', 'Count Records'),
        ('sum', 'Sum Field'),
        ('avg', 'Average Field'),
        ('formula', 'Custom Formula'),
        ('completion_rate', 'Survey Completion Rate'),      # Added new option
        ('facilitator_performance', 'Facilitator Performance')  # Added new option
    ], string="Calculation Type", default='count')
    formula = fields.Char("Custom Formula", help="Python expression for custom calculation")
    
    # iN-Clue specific fields
    facilitator_id = fields.Many2one('res.partner', string='Filter by Facilitator',
                                   domain="[('is_facilitator', '=', True)]")
    session_type = fields.Selection([
        ('all', 'All Sessions'),
        ('kickoff', 'Kickoff Only'),
        ('followup', 'Follow-ups Only')
    ], string="Session Type Filter", default='all')
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.count_field = False
    
    def _compute_card_data(self):
        """Compute the data to be displayed on the card"""
        self.ensure_one()
        
        # Special calculations for iN-Clue
        if self.calculation_type in ['completion_rate', 'facilitator_performance']:
            try:
                if self.calculation_type == 'completion_rate':
                    return self._compute_completion_rate()
                elif self.calculation_type == 'facilitator_performance':
                    return self._compute_facilitator_performance()
            except Exception as e:
                return f"Error: {str(e)[:20]}"
        
        if not self.model_id:
            return self.card_value or "0"
            
        model_name = self.model_id.model
        model = self.env[model_name]
        
        # Use safer domain evaluation with proper error handling
        try:
            # For simple domains, use literal_eval
            if self.domain and self.domain != "[]":
                domain = safe_eval(self.domain)
            else:
                domain = []
        except Exception as e:
            return f"Domain Error: {str(e)[:20]}"
        
        try:
            if self.calculation_type == 'count':
                return str(model.search_count(domain))
            elif self.calculation_type in ['sum', 'avg'] and self.count_field:
                records = model.search(domain)
                if not records:
                    return "0"
                
                # Safely get field values
                try:
                    values = records.mapped(self.count_field)
                    if not values:
                        return "0"
                        
                    if self.calculation_type == 'sum':
                        total = sum(values)
                        return str(total)
                    else:  # avg
                        avg = sum(values) / len(values) if values else 0
                        return str(round(avg, 1))
                except Exception as e:
                    return f"Field Error: {str(e)[:20]}"
                    
            elif self.calculation_type == 'formula' and self.formula:
                records = model.search(domain)
                if not records:
                    return "0"
                
                # Use safer formula evaluation
                try:
                    # Create a sandbox for the formula with limited globals
                    global_vars = {
                        'records': records,
                        'len': len,
                        'sum': sum,
                        'min': min,
                        'max': max,
                        'round': round,
                        'mapped': lambda field: records.mapped(field),
                        'filtered': lambda func: records.filtered(func),
                    }
                    
                    result = safe_eval(self.formula, global_vars)
                    return str(result)
                except Exception as e:
                    return f"Formula Error: {str(e)[:20]}"
            
            return self.card_value or "0"
        except Exception as e:
            return f"Error: {str(e)[:20]}"
    
    def _compute_completion_rate(self):
        """Calculate survey completion rate"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                domain = safe_eval(self.domain)
            except Exception as e:
                return f"Domain Error: {str(e)[:20]}"
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
        # Apply session type filter if specified
        if self.session_type == 'kickoff':
            domain.append(('session_type', '=', 'kickoff'))
        elif self.session_type == 'followup':
            domain.append(('session_type', '!=', 'kickoff'))
        
        # Get the participation records
        try:
            participations = self.env['inclue.participation'].search(domain)
        except Exception:
            return "N/A"  # Model might not exist
        
        if not participations:
            return "0%"
        
        # Calculate completion rate
        total = len(participations)
        completed = len(participations.filtered(lambda p: p.completed))
        
        completion_rate = (completed / total) * 100 if total > 0 else 0
        return f"{round(completion_rate)}%"
    
    def _compute_facilitator_performance(self):
        """Calculate facilitator performance metrics"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                domain = safe_eval(self.domain)
            except Exception as e:
                return f"Domain Error: {str(e)[:20]}"
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
        # Get the participation records
        try:
            participations = self.env['inclue.participation'].search(domain)
        except Exception:
            return "N/A"  # Model might not exist
        
        if not participations:
            return "0"
        
        # Get unique events facilitated
        events = participations.mapped('event_id')
        
        # Get unique participants
        participants = participations.mapped('partner_id')
        
        # Calculate completion rate
        total = len(participations)
        completed = len(participations.filtered(lambda p: p.completed))
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # Return the score based on what field is set to count
        if self.count_field == 'events':
            return str(len(events))
        elif self.count_field == 'participants': 
            return str(len(participants))
        elif self.count_field == 'completion_rate':
            return f"{round(completion_rate)}%"
        else:
            # Default to events count if no field specified
            return str(len(events))