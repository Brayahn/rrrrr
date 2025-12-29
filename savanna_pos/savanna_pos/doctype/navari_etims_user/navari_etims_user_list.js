const doctypeName = "Navari eTims User";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Add eTims Users from System Users"),
      function (listview) {
        frappe.call({
          method:
            "savanna_pos.savanna_pos.apis.apis.create_branch_user",
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

    listview.page.add_inner_button(
      __("Sync Default eTims User Details"),
      function (listview) {
        frappe.call({
          method:
            "savanna_pos.savanna_pos.apis.apis.get_my_user_details",
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
