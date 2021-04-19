frappe.ready(async () => {
  new EditAsset();
});

class EditAsset {
  constructor(opts) {
    this.edited_files = {};
    this.make_code_field_group();
    this.make_edit_field_group();
    this.make_submit_section_field_group();
    this.render_preview();
    this.add_attachment_handler();
  }

  render_preview() {
    // frappe.ready(() => {
    $('a[data-toggle="tab"]').on("shown.bs.tab", (e) => {
      let activeTab = $(e.target);

      if (
        activeTab.prop("id") === "preview-tab" ||
        activeTab.prop("id") === "diff-tab"
      ) {
        console.log("in");
        let content = $("textarea#content").val();
        let $preview = $(".wiki-preview");
        let $diff = $(".wiki-diff");
        $preview.html("Loading preview...");
        frappe.call({
          method: "edit_docs.www.edit.preview",
          args: {
            content: this.code_field_group.get_value("code"),
            path: this.route,
            attachments: this.attachments,
          },
          callback: (r) => {
            if (r.message) {
              $preview.html(r.message.html);
              $diff.html(r.message.diff);
            }
          },
        });
      }

      if (activeTab.prop("id") === "diff-tab") {
        console.log("diff");
      }
    });
    // })
  }

  make_edit_field_group() {
    const route = $("#route").val();
    this.edit_field_group = new frappe.ui.FieldGroup({
      fields: [
        {
          label: __("Route Link"),
          fieldname: "route_link",
          fieldtype: "Data",
          default: route || "",
        },
        {
          label: __("Edit Code"),
          fieldname: "code",
          fieldtype: "Button",
          click: () => this.update_code(),
        },
        {
          label: __("Overwrite From Disk"),
          fieldname: "code_from_disk",
          fieldtype: "Button",
          click: () => this.update_code(true),
        },
      ],
      body: $(".routedisp"),
    });
    this.edit_field_group.make();
  }

  make_code_field_group() {
    this.code_field_group = new frappe.ui.FieldGroup({
      fields: [
        {
          label: __("Edit Code"),
          fieldname: "code",
          fieldtype: "Code",
          columns: 4,
          reqd: 1,
          options: "Markdown",
        },
      ],
      body: $(".wiki-write").get(0),
    });
    this.code_field_group.make();
  }

  update_code(from_disk = false) {
    const route = this.edit_field_group.get_value("route_link");
    if (route === this.route && !from_disk) return;
    if (route in this.edited_files && !from_disk) {
      this.code_field_group
        .get_field("code")
        .set_value(this.edited_files[route]);
      this.route = route;
      return;
    }
    frappe.call({
      method: "edit_docs.www.edit.get_code",
      args: { route: route },
      callback: (r) => {
        console.log(r);
        if (this.route)
          this.edited_files[this.route] = this.code_field_group.get_value(
            "code"
          );
        console.log(this.edited_files);
        this.route = route;
        this.code_field_group.get_field("code").set_value(r.message);
        this.build_file_table();
      },
    });
  }
  make_submit_section_field_group() {
    this.submit_section_field_group = new frappe.ui.FieldGroup({
      fields: [
        {
          label: __("Submit"),
          fieldname: "submit_button",
          fieldtype: "Button",
          primary: 1,
          btn_size: "lg",
          reqd: 1,
          click: () => this.raise_pr(),
        },
      ],
      body: $(".submit-section"),
    });
    this.submit_section_field_group.make();
  }

  raise_pr() {
    if (this.route)
      this.edited_files[this.route] = this.code_field_group.get_value("code");
    frappe.call({
      method: "edit_docs.www.edit.update",
      args: {
        content: this.edited_files,
        attachments: this.attachments,
      },
      callback: (r) => {
        frappe.show_alert(
          "A Change Request has been generated. You can track your requests here after a few mins",
          5
        );
        window.location.href = "/pull-request";
      },
    });
  }

  add_attachment_handler() {
    var me = this;
    $(".add-attachment").click(function () {
      me.new_attachment();
    });
  }

  new_attachment(fieldname) {
    if (this.dialog) {
      // remove upload dialog
      this.dialog.$wrapper.remove();
    }

    new frappe.ui.FileUploader({
      folder: "Home/Attachments",
      on_success: (file_doc) => {
        if (!this.attachments) this.attachments = [];
        if (!this.save_paths) this.save_paths = {};
        this.attachments.push(file_doc);
        console.log(this.attachments);
        this.build_attachment_table();
      },
    });
  }

  build_attachment_table() {
    var wrapper = $(".wiki-attachment");
    wrapper.empty();

    var table = $(
      '<table class="table table-bordered" style="cursor:pointer; margin:0px;"><thead>\
	<tr><th style="width: 33%">' +
        __("File Name") +
        '</th><th style="width: 33%">' +
        __("Current Path") +
        "</th><th>" +
        __("Path While Submitting") +
        "</th></tr>\
	</thead><tbody></tbody></table>"
    ).appendTo(wrapper);
    $(
      '<p class="text-muted small">' + __("Click table to edit") + "</p>"
    ).appendTo(wrapper);

    this.attachments.forEach((f) => {
      const row = $("<tr></tr>").appendTo(table.find("tbody"));
      $("<td>" + f.file_name + "</td>").appendTo(row);
      $("<td>" + f.file_url + "</td>").appendTo(row);
      $("<td>" + f.save_path + "</td>").appendTo(row);
    });

    table.on("click", () => this.table_click_handler());
  }

  table_click_handler() {
    var me = this;
    var dfs = [];
    this.attachments.forEach((f) => {
      dfs.push({
        fieldname: f.file_name,
        fieldtype: "Data",
        label: f.file_name,
      });
    });
    let dialog = new frappe.ui.Dialog({
      fields: dfs,
      primary_action: function () {
        var values = this.get_values();
        if (values) {
          this.hide();
          // frm.set_value('filters', JSON.stringify(values));
          me.save_paths = values;
          me.attachments.forEach((f) => {
            f.save_path = values[f.file_name];
          });
          console.log(values);
          console.log(me.attachments);
          me.build_attachment_table();
        }
      },
    });
    dialog.show();
    dialog.set_values(me.save_paths);
  }

  build_file_table() {
    var wrapper = $(".wiki-files");
    wrapper.empty();
    debugger;
    var table = $(
      '<table class="table table-bordered" style="cursor:pointer; margin:0px;"><thead>\
	<tr><th>' +
        __("Route") +
        "</th></tr>\
	</thead><tbody></tbody></table>"
    ).appendTo(wrapper);

    for (var file in this.edited_files) {
      const row = $("<tr></tr>").appendTo(table.find("tbody"));
      $("<td>" + file + "</td>").appendTo(row);
    }
    const row = $("<tr></tr>").appendTo(table.find("tbody"));
    $("<td>" + this.route + "</td>").appendTo(row);
  }
}
