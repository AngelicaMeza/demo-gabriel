odoo.define('test_modulo.BasicView', function (require) {
    "use strict";
    
    var session = require('web.session');
    var BasicView = require('web.BasicView');
    var core = require('web.core');
    var _t = core._t;

    BasicView.include({
        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            var model = self.controllerParams.modelName == 'res.users';
            if(model) {
                session.user_has_group('hide_action_option.root_admin_group').then(function(has_group) {
                    if(!has_group) {
                        self.controllerParams.activeActions.delete = false ;
                        if (self.controllerParams.toolbarActions){
                            self.controllerParams.toolbarActions.action = _.reject(self.controllerParams.toolbarActions.action, function (act) {
                                return act.res_model === 'change.password.wizard'
                            })
                        }
                    }
                });
            }
        },
    });
});
