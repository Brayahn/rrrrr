const doctypeName = "Navari eTims UOM Category";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Fetch eTims UOM Categories"),
      function (listview) {
        frappe.call({
          method:
            "savanna_pos.savanna_pos.background_tasks.tasks.fetch_etims_uom_categories",
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
