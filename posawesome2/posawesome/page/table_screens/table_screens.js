frappe.pages["table-screens"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Table Numbers"),
    single_column: true,
  });

  wrapper.page_no = 1;
  wrapper.page_length = 20;

  $(wrapper).find(".layout-main-section").html(`
        <div class="filter-bar" style="margin-bottom: 15px;">
            <label>${__("Branch")}:</label>
            <input type="text" class="form-control input-sm branch-filter" placeholder="Enter Branch" style="width:200px; display:inline-block; margin-right:10px;">
            <button class="btn btn-sm btn-primary btn-filter">${__(
              "Filter"
            )}</button>
        </div>

        <div class="cards-container" 
            style="
                display:grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap:15px;
            ">
        </div>

        <div class="pagination-bar" style="margin-top:20px; text-align:center;">
            <button class="btn btn-default btn-sm btn-prev">${__(
              "Previous"
            )}</button>
            <span class="page-info" style="margin:0 10px;"></span>
            <button class="btn btn-default btn-sm btn-next">${__(
              "Next"
            )}</button>
        </div>
    `);

  const $wrapper = $(wrapper);
  const $cards = $wrapper.find(".cards-container");
  const $pageInfo = $wrapper.find(".page-info");

  function load_cards() {
    const branch = $wrapper.find(".branch-filter").val();
    frappe.call({
      method:
        "posawesome.posawesome.page.table_screens.table_screens.get_table_number_data",
      args: {
        branch: branch,
        page_no: wrapper.page_no,
        page_length: wrapper.page_length,
      },
      freeze: true,
      freeze_message: __("Loading..."),
      callback: function (r) {
        if (!r.message) return;
        const data = r.message.data;

        $cards.empty();

        data.forEach((row) => {
          const disabled_class = row.disabled ? "opacity:0.5;" : "";
          const reopen_btn = row.disabled
            ? `<div style="margin-top:12px;">
                <button class="btn btn-warning btn-xs btn-reopen"
                  data-name="${row.name}"
                  data-branch="${row.branch}">
                  ${__("Reopen")}
                </button>
            </div>`
            : "";

          $cards.append(`
          <div class="card table-card"
              data-name="${row.name}"
              data-branch="${row.branch}"
              data-disabled="${row.disabled}"
              style="
                border:1px solid #ccc; border-radius:10px; padding:15px; text-align:center;
                background:#fff; box-shadow:0 2px 5px rgba(0,0,0,0.1); ${disabled_class}
              ">
            <h3 style="margin:0; font-size:22px; font-weight:bold;">${
              row.no
            }</h3>
            <div style="margin-top:8px; font-size:14px; color:#555;">
              ${__("Branch")}: ${row.branch}
            </div>
            <div style="margin-top:5px; font-size:13px; color:${
              row.disabled ? "red" : "green"
            };">
              ${row.disabled ? __("Disabled") : __("Active")}
            </div>
            ${reopen_btn}
          </div>
        `);
        });

        const total_pages = Math.ceil(
          r.message.total_count / wrapper.page_length
        );
        $pageInfo.text(`Page ${wrapper.page_no} of ${total_pages}`);

        $wrapper.find(".btn-prev").prop("disabled", wrapper.page_no <= 1);
        $wrapper
          .find(".btn-next")
          .prop("disabled", wrapper.page_no >= total_pages);
      },
    });
  }

  // Events
  $wrapper.on("click", ".btn-filter", function () {
    wrapper.page_no = 1;
    load_cards();
  });
  $wrapper.on("click", ".btn-reopen", function (e) {
    e.stopPropagation(); // don't trigger the card click
    const tableName = $(this).data("name");
    const branch = $(this).data("branch");

    frappe.confirm(__("Reopen this table?"), () => {
      frappe.call({
        method:
          "posawesome.posawesome.page.table_screens.table_screens.reopen_table",
        args: { table_name: tableName, branch: branch },
        freeze: true,
        freeze_message: __("Reopening..."),
        callback: function (r) {
          if (r.message && (r.message.ok || r.message === true)) {
            frappe.show_alert({
              message: __("Table reopened"),
              indicator: "green",
            });
            load_cards();
          } else {
            frappe.msgprint(r.message || __("Could not reopen this table."));
          }
        },
        error: function (err) {
          frappe.msgprint(__("Server error while reopening the table."));
        },
      });
    });
  });
  $wrapper.on("click", ".btn-prev", function () {
    if (wrapper.page_no > 1) {
      wrapper.page_no--;
      load_cards();
    }
  });
  $wrapper.on("click", ".table-card", function () {
    const tableName = $(this).data("name");
    const tableBranch = $(this).data("branch");
    const isDisabled = $(this).data("disabled");

    if (!isDisabled) {
      frappe.msgprint(__("This table is active and has no Sales Order."));
      return;
    }

    frappe.call({
      method:
        "posawesome.posawesome.page.table_screens.table_screens.get_sales_order_details_for_table",
      args: {
        table_name: tableName,
        branch: tableBranch,
      },
      callback: function (r) {
        if (!r.message) {
          frappe.msgprint(
            __("No Sales Order found for this table and branch.")
          );
          return;
        }
        show_sales_order_dialog(r.message);
      },
    });
  });

  $wrapper.on("click", ".btn-next", function () {
    wrapper.page_no++;
    load_cards();
  });

  load_cards(); // initial
  frappe.realtime.on("table_number_updated", () => {
    load_cards();
  });
};
function show_sales_order_dialog(so) {
  console.log("SO DATA:", so); // <--- debug

  const d = new frappe.ui.Dialog({
    title: __("Sales Order Details"),
    size: "large",
    // primary_action_label: __("Open Full Sales Order"),
    // primary_action() {
    //   frappe.set_route("Form", "Sales Order", so.name);
    // },
  });

  // Build items table dynamically
  let items_html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>${__("Item")}</th>
                    <th>${__("Qty")}</th>
                    <th>${__("Rate")}</th>
                    <th>${__("Amount")}</th>
                </tr>
            </thead>
            <tbody>
                ${so.items
                  .map(
                    (i) => `
                    <tr>
                        <td>${i.item_name}</td>
                        <td>${i.qty}</td>
                        <td>${i.rate}</td>
                        <td>${i.amount}</td>
                    </tr>
                `
                  )
                  .join("")}
            </tbody>
        </table>
    `;

  // ⭐ THIS IS THE CORRECT WAY ⭐
  d.$body.html(`
        <div style="font-size:15px; margin-bottom:10px;">
            <b>${__("Sales Order")}:</b> ${so.name}<br>
            <b>${__("Customer")}:</b> ${so.customer}<br>
            <b>${__("Grand Total")}:</b> ${format_currency(so.grand_total)}
        </div>

        <h4>${__("Items")}</h4>
        ${items_html}
    `);

  d.show();
}
