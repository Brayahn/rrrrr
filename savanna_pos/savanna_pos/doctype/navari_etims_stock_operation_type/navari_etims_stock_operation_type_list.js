const doctypeName = "Navari eTims Stock Operation Type";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Fetch eTims Stock Operation Types"),
      function (listview) {
        frappe.call({
          method:
            "savanna_pos.savanna_pos.background_tasks.tasks.fetch_etims_operation_types",
          args: {
            request_data: {
              company_name: companyName,
            },
          },
          callback: (response) => {},
          error: (error) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("eTims Actions")
    );
  },
};
