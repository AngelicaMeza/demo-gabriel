odoo.define('crm_lead_form.BasicModel', function (require) {
"use strict";

var BasicModel = require('web.BasicModel');
var Dialog = require('web.Dialog');

BasicModel.include({
	/**
	 * Duplicate a record (by calling the 'copy' route)
	 *
	 * @param {string} recordID id for a local resource
	 * @returns {Promise<string>} resolves to the id of duplicate record
	 */
	duplicateRecord: function (recordID) {
		var self = this;
		var record = this.localData[recordID];
		if (record.model === 'crm.lead') {
			self._rpc({
				model: record.model,
				method: 'onchange_check_lead',
				args: [record.res_id],
			})
			.then(function (result) {
				if (result && result.warning) {
					var warning = result.warning;
					Dialog.alert(self, warning.message, {title: warning.title});
				}
			});
		}
		return this._super.apply(this, arguments);
	},
});

});