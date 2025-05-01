from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

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
    
    # User filtering
    filter_by_current_user = fields.Boolean("Filter by Current User", 
                                         help="Only show data related to the current user")
    
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
                _logger.error(f"Error in dashboard calculation: {str(e)}")
                return f"Error: {str(e)[:20]}"

        if not self.model_id:
            return self.card_value or "0"
        
        model_name = self.model_id.model

        # Check if model exists
        if not model_name in self.env:
            return "Model Not Found"
        
        model = self.env[model_name]

        # Use safer domain evaluation with proper error handling
        try:
            # Create evaluation context with date/time functions
            eval_context = {
                'datetime': datetime,
                'relativedelta': relativedelta,
                'date': datetime.date,
                'fields': fields,
                'today': fields.Date.today(),
                'now': fields.Datetime.now(),
                'uid': self.env.uid,
                'user': self.env.user,
            }

            # For simple domains, use safe_eval with context
            if self.domain and self.domain != "[]":
                try:
                    domain = safe_eval(self.domain, eval_context)
                except Exception as e:
                    _logger.error(f"Domain evaluation error: {str(e)}")
                    domain = []
            else:
                domain = []

            # Add user filter if enabled
            if self.filter_by_current_user:
                # Check the model and apply the relevant filter for the current user
                fields_list = model.fields_get_keys()
                if model_name == 'inclue.participation':
                    if self.env.user.partner_id.is_facilitator:
                        # If user is a facilitator, filter by their facilitator_id
                        domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
                        _logger.info(f"Applied facilitator filter: {self.env.user.partner_id.id}")
                    else:
                        # If user is a participant, filter by partner_id
                        domain.append(('partner_id', '=', self.env.user.partner_id.id))
                        _logger.info(f"Applied participant filter: {self.env.user.partner_id.id}")
                elif model_name == 'event.event':
                    if self.env.user.partner_id.is_facilitator:
                        # If user is a facilitator, filter by their facilitator_id
                        domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
                        _logger.info(f"Applied event facilitator filter: {self.env.user.partner_id.id}")
                    else:
                        # If user is not a facilitator, filter by create_uid (creator of the event)
                        domain.append(('create_uid', '=', self.env.uid))
                        _logger.info(f"Applied event creator filter: {self.env.uid}")
                else:
                    # For other models, apply user-specific filters based on available fields
                    if 'user_id' in fields_list:
                        domain.append(('user_id', '=', self.env.uid))
                        _logger.info(f"Applied user_id filter: {self.env.uid}")
                    elif 'facilitator_id' in fields_list:
                        domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
                        _logger.info(f"Applied facilitator_id filter: {self.env.user.partner_id.id}")
                    elif 'partner_id' in fields_list:
                        domain.append(('partner_id', '=', self.env.user.partner_id.id))
                        _logger.info(f"Applied partner_id filter: {self.env.user.partner_id.id}")
                    elif 'create_uid' in fields_list:
                        domain.append(('create_uid', '=', self.env.uid))
                        _logger.info(f"Applied create_uid filter: {self.env.uid}")
                    else:
                        _logger.warning(f"No suitable field found for user filtering in model {model_name}")

        except Exception as e:
            _logger.error(f"Domain preparation error: {str(e)}")
            return f"Domain Error: {str(e)[:20]}"
        
        # Now perform the actual calculation using the domain
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
                    _logger.error(f"Field mapping error: {str(e)}")
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
                        'datetime': datetime,
                        'relativedelta': relativedelta,
                    }
                    
                    result = safe_eval(self.formula, global_vars)
                    return str(result)
                except Exception as e:
                    _logger.error(f"Formula evaluation error: {str(e)}")
                    return f"Formula Error: {str(e)[:20]}"
            
            return self.card_value or "0"
        except Exception as e:
            _logger.error(f"Card computation error: {str(e)}")
            return f"Error: {str(e)[:20]}"

    
    # def _compute_completion_rate(self):
    #     """Calculate survey completion rate"""
    #     domain = []
        
    #     # Apply base domain if specified
    #     if self.domain and self.domain != "[]":
    #         try:
    #             # Create evaluation context
    #             eval_context = {
    #                 'datetime': datetime,
    #                 'relativedelta': relativedelta,
    #                 'date': datetime.date,
    #                 'fields': fields,
    #                 'today': fields.Date.today(),
    #                 'now': fields.Datetime.now(),
    #                 'uid': self.env.uid,
    #                 'user': self.env.user,
    #             }
    #             domain = safe_eval(self.domain, eval_context)
    #         except Exception as e:
    #             _logger.error(f"Domain evaluation error in completion rate: {str(e)}")
    #             # Continue with empty domain rather than failing
        
    #     # Apply facilitator filter if specified
    #     if self.facilitator_id:
    #         domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
    #     # Apply session type filter if specified
    #     if self.session_type == 'kickoff':
    #         domain.append(('session_type', '=', 'kickoff'))
    #     elif self.session_type == 'followup':
    #         domain.append(('session_type', '!=', 'kickoff'))
            
    #     # Add user filter if enabled
    #     if self.filter_by_current_user:
    #         # For inclue.participation, filter by facilitator if user is a facilitator
    #         if self.env.user.partner_id.is_facilitator:
    #             domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
        
    #     # Get the participation records
    #     try:
    #         # Check if model exists
    #         if 'inclue.participation' not in self.env:
    #             return "Model Not Found"
                
    #         participations = self.env['inclue.participation'].search(domain)
    #     except Exception as e:
    #         _logger.error(f"Search error in completion rate: {str(e)}")
    #         return "Error"
        
    #     if not participations:
    #         return "0%"
        
    #     # Calculate completion rate
    #     total = len(participations)
    #     completed = len(participations.filtered(lambda p: p.completed))
        
    #     completion_rate = (completed / total) * 100 if total > 0 else 0
    #     return f"{round(completion_rate)}%"

    def _compute_completion_rate(self):
        """Calculate survey completion rate"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                # Create evaluation context
                today_date = fields.Date.today()
                now_datetime = fields.Datetime.now()
                
                eval_context = {
                    'datetime': datetime,
                    'relativedelta': relativedelta,
                    'date': datetime.date,
                    'today': today_date,
                    'now': now_datetime,
                    'uid': self.env.uid,
                    'user': self.env.user,
                }
                domain = safe_eval(self.domain, eval_context)
            except Exception as e:
                _logger.error(f"Domain evaluation error in completion rate: {str(e)}")
                # Continue with empty domain rather than failing
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
        # Apply session type filter if specified
        if self.session_type == 'kickoff':
            domain.append(('session_type', '=', 'kickoff'))
        elif self.session_type == 'followup':
            domain.append(('session_type', '!=', 'kickoff'))
            
        # Add user filter if enabled
        if self.filter_by_current_user:
            # For inclue.participation, filter by facilitator if user is a facilitator
            if self.env.user.partner_id.is_facilitator:
                domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
        
        # Get the participation records
        try:
            # Check if model exists
            if 'inclue.participation' not in self.env:
                return "Model Not Found"
                
            participations = self.env['inclue.participation'].search(domain)
        except Exception as e:
            _logger.error(f"Search error in completion rate: {str(e)}")
            return "Error"
        
        if not participations:
            return "0%"
        
        # Calculate completion rate
        total = len(participations)
        completed = len(participations.filtered(lambda p: p.completed))
        
        completion_rate = (completed / total) * 100 if total > 0 else 0
        return f"{round(completion_rate)}%"
    
    # def _compute_facilitator_performance(self):
    #     """Calculate facilitator performance metrics"""
    #     domain = []
        
    #     # Apply base domain if specified
    #     if self.domain and self.domain != "[]":
    #         try:
    #             # Create evaluation context
    #             eval_context = {
    #                 'datetime': datetime,
    #                 'relativedelta': relativedelta,
    #                 'date': datetime.date,
    #                 'fields': fields,
    #                 'today': fields.Date.today(),
    #                 'now': fields.Datetime.now(),
    #                 'uid': self.env.uid,
    #                 'user': self.env.user,
    #             }
    #             domain = safe_eval(self.domain, eval_context)
    #         except Exception as e:
    #             _logger.error(f"Domain evaluation error in facilitator performance: {str(e)}")
    #             # Continue with empty domain rather than failing
        
    #     # Apply facilitator filter if specified
    #     if self.facilitator_id:
    #         domain.append(('facilitator_id', '=', self.facilitator_id.id))
    #     elif self.filter_by_current_user and self.env.user.partner_id.is_facilitator:
    #         # If filter by current user is enabled and user is a facilitator
    #         domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
        
    #     # Get the participation records
    #     try:
    #         # Check if model exists
    #         if 'inclue.participation' not in self.env:
    #             return "Model Not Found"
                
    #         participations = self.env['inclue.participation'].search(domain)
    #     except Exception as e:
    #         _logger.error(f"Search error in facilitator performance: {str(e)}")
    #         return "Error"
        
    #     if not participations:
    #         return "0"
        
    #     # Get unique events facilitated
    #     events = participations.mapped('event_id')
        
    #     # Get unique participants
    #     participants = participations.mapped('partner_id')
        
    #     # Calculate completion rate
    #     total = len(participations)
    #     completed = len(participations.filtered(lambda p: p.completed))
    #     completion_rate = (completed / total) * 100 if total > 0 else 0
        
    #     # Return the score based on what field is set to count
    #     if self.count_field == 'events':
    #         return str(len(events))
    #     elif self.count_field == 'participants': 
    #         return str(len(participants))
    #     elif self.count_field == 'completion_rate':
    #         return f"{round(completion_rate)}%"
    #     else:
    #         # Default to events count if no field specified
    #         return str(len(events))

    def _compute_facilitator_performance(self):
        """Calculate facilitator performance metrics"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                # Create evaluation context
                today_date = fields.Date.today()
                now_datetime = fields.Datetime.now()
                
                eval_context = {
                    'datetime': datetime,
                    'relativedelta': relativedelta,
                    'date': datetime.date,
                    'today': today_date,
                    'now': now_datetime,
                    'uid': self.env.uid,
                    'user': self.env.user,
                }
                domain = safe_eval(self.domain, eval_context)
            except Exception as e:
                _logger.error(f"Domain evaluation error in facilitator performance: {str(e)}")
                # Continue with empty domain rather than failing
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        elif self.filter_by_current_user and self.env.user.partner_id.is_facilitator:
            # If filter by current user is enabled and user is a facilitator
            domain.append(('facilitator_id', '=', self.env.user.partner_id.id))
        
        # Get the participation records
        try:
            # Check if model exists
            if 'inclue.participation' not in self.env:
                return "Model Not Found"
                
            participations = self.env['inclue.participation'].search(domain)
        except Exception as e:
            _logger.error(f"Search error in facilitator performance: {str(e)}")
            return "Error"
        
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