odoo.define('dashboard_custom.dashboard_snippet', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var options = require('web_editor.snippets.options');
    var ajax = require('web.ajax');
    var core = require('web.core');
    
    // Define snippet options
    options.registry.dashboard_widget = options.Class.extend({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },
    });
    
    // Define frontend widget
    publicWidget.registry.dashboardWidget = publicWidget.Widget.extend({
        selector: '.dashboard-component',
        events: {
            'click .dashboard-refresh-btn': '_onRefreshClick',
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                console.log('Dashboard widget initialized!');
                // Initial setup
                self._setupAutoRefresh();
            });
        },
        
        _onRefreshClick: function(ev) {
            ev.preventDefault();
            this._fullRefreshContent();
        },
        
        _setupAutoRefresh: function() {
            var self = this;
            // Set up timer for auto-refresh
            setInterval(function() {
                self._refreshData();
            }, 60000); // 1 minute
        },
        
        _refreshData: function() {
            var self = this;
            ajax.jsonRpc('/dashboard/refresh_data', 'call', {})
                .then(function (result) {
                    if (result.error) {
                        console.error("Error refreshing dashboard:", result.error);
                        return;
                    }
                    
                    // Update all component values
                    _.each(result, function(data, id) {
                        var card = self.$el.find('[data-component-id="' + id + '"]');
                        if (card.length) {
                            card.find('.dashboard-card-value').text(data.value);
                        }
                    });
                })
                .catch(function(error) {
                    console.error("Failed to refresh dashboard data:", error);
                });
        },
        
        _fullRefreshContent: function() {
            var self = this;
            // Show loading indicator
            self.$('.dashboard-content').addClass('o_loading');
            
            // Get fresh content
            ajax.jsonRpc('/dashboard/get_components', 'call', {})
                .then(function (result) {
                    if (result.error) {
                        console.error("Error refreshing dashboard:", result.error);
                        return;
                    }
                    
                    // Replace the entire content
                    self.$('.dashboard-content').html(result.html);
                    self.$('.dashboard-content').removeClass('o_loading');
                })
                .catch(function(error) {
                    console.error("Failed to refresh dashboard:", error);
                    self.$('.dashboard-content').removeClass('o_loading');
                });
        }
    });
    
    return {
        dashboardWidget: publicWidget.registry.dashboardWidget
    };
});