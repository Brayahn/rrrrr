const doctypeName = "UOM";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.listview_settings[doctypeName] = {
  onload: async function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    const { message: activeSetting } = await frappe.call({
      method:
        "savanna_pos.savanna_pos.utils.get_active_settings",
      args: {
        doctype: settingsDoctypeName,
      },
    });

    if (activeSetting?.length > 0) {
      listview.page.add_inner_button(
        __("Fetch eTims UOM List"),
        function (listview) {
          frappe.call({
            method:
              "savanna_pos.savanna_pos.background_tasks.tasks.fetch_etims_uom_list",
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
        __("Submit all UOMs to eTims"),
        function (listview) {
          frappe.call({
            method:
              "savanna_pos.savanna_pos.apis.apis.submit_uom_list",
            args: {},
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
    }
  },
};
