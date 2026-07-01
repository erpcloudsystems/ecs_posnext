frappe.pages["pos_super_opening"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("POS Super Opening"),
		single_column: true,
	});

	const $body = $(`
		<div class="p-6">
			<div class="card bg-white p-6 shadow-sm border rounded-xl" style="max-width: 600px; margin: 0 auto;">
				<h2 class="text-xl font-bold mb-6 text-gray-800">${__("Prepare Opening Shift")}</h2>
				
				<div class="space-y-4">
					<div id="user_field"></div>
					<div id="pos_profile_field"></div>
					<div id="cash_amount_field"></div>
					
					<div class="pt-4">
						<button class="btn btn-primary btn-lg w-full font-bold" id="btn_prepare">
							${__("Prepare Opening Shift")}
						</button>
					</div>
				</div>
				
				<div id="result_area" class="mt-6"></div>
			</div>
		</div>
	`);

	$(page.body).append($body);

	// Create Fields
	const user_field = frappe.ui.form.make_control({
		df: {
			label: __("Cashier / User"),
			fieldname: "user",
			fieldtype: "Link",
			options: "User",
			reqd: 1,
			get_query: () => {
				return {
					filters: {
						enabled: 1,
						user_type: "System User"
					}
				};
			},
			onchange: () => {
				pos_profile_field.set_value("");
				pos_profile_field.get_query = () => {
					return {
						query: "ecs_posnext.api.pos_profile.get_user_pos_profiles",
						filters: { user: user_field.get_value() }
					};
				};
			}
		},
		parent: $body.find("#user_field"),
		render_input: true,
	});

	const pos_profile_field = frappe.ui.form.make_control({
		df: {
			label: __("POS Profile"),
			fieldname: "pos_profile",
			fieldtype: "Link",
			options: "POS Profile",
			reqd: 1,
		},
		parent: $body.find("#pos_profile_field"),
		render_input: true,
	});

	const cash_amount_field = frappe.ui.form.make_control({
		df: {
			label: __("Opening Cash Amount"),
			fieldname: "cash_amount",
			fieldtype: "Currency",
			default: 0,
			reqd: 1,
		},
		parent: $body.find("#cash_amount_field"),
		render_input: true,
	});

	// Button Action
	$body.find("#btn_prepare").on("click", () => {
		const user = user_field.get_value();
		const pos_profile = pos_profile_field.get_value();
		const cash_amount = cash_amount_field.get_value();

		if (!user || !pos_profile) {
			frappe.msgprint(__("Please fill all required fields"));
			return;
		}

		frappe.call({
			method: "ecs_posnext.api.shifts.prepare_opening_shift",
			args: {
				user: user,
				pos_profile: pos_profile,
				cash_amount: cash_amount
			},
			freeze: true,
			freeze_message: __("Preparing Shift..."),
			callback: (r) => {
				if (r.message) {
					const name = r.message;
					$body.find("#result_area").html(`
						<div class="alert alert-success border-0 bg-green-50 text-green-800 p-4 rounded-lg flex items-center gap-3">
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
							</svg>
							<div>
								<p class="font-bold">${__("Shift Prepared Successfully")}</p>
								<p class="text-sm">${__("Shift Name")}: <a href="/app/pos-opening-shift/${name}" class="underline font-medium">${name}</a></p>
							</div>
						</div>
					`);
					
					// Clear fields
					user_field.set_value("");
					pos_profile_field.set_value("");
					cash_amount_field.set_value(0);
				}
			}
		});
	});
};
