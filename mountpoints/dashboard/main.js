/* globals $, document */

let top_level_data = [];

let study_version_validation = [];

let study_version_import = [];

let second_level_data = [];

const display_names = {
    "org_name": "Folder",
    "study_name": "Study",
    "current_version_passes_validation": "Current Version Passes Validation",
    "current_version_loads_successfully": "Current Version Loads Successfully",
    "current_version_loaded": "Current Version Loaded",
    "previous_version_loaded": "Previous Version Loaded",
    "passes_validation": "Passes Validation",
    "loads_successfully": "Loads Successfully",
    "currently_loaded": "Currently Loaded",
    "validation_success": "Validation Success",
    "validation_status_code": "Validation Exit Code",
    "validation_time_added": "Validation Time Added",
    "import_success": "Import Success",
    "import_status_code": "Import Exit Code",
    "import_time_added": "Import Time Added",
    "output": "Output",
    "level": "Log Level",
    "path": "Path",
    "message": "Log Message"
};
$(document).ready(function () {
    const main = $('#main');
    const breadcrumbs = $('#breadcrumbs');
    let AjaxGet = function (url) {
        const result = $.ajax({
            type: "GET",
            url: url,
            param: '{}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            async: false,
        });
        return eval(result.responseText)
    };

    top_level_data = AjaxGet("/dashboard/data/top_level.json");
    second_level_data = AjaxGet("/dashboard/data/second_level.json");
    study_version_validation = AjaxGet("/dashboard/data/study_version_validation.json");
    study_version_import = AjaxGet("/dashboard/data/study_version_import.json");

    const second_level_headers = {
        "passes_validation": "bool",
        "loads_successfully": "bool",
        "currently_loaded": "bool",
        "validation_success": "bool",
        "validation_status_code": "text",
        "validation_time_added": "text",
        "import_success": "bool",
        "import_status_code": "text",
        "import_time_added": "text"
    };

    const top_level_headers = {
        "org_name": "text",
        "study_name": "text",
        "current_version_passes_validation": "bool",
        "current_version_loads_successfully": "bool",
        "current_version_loaded": "bool",
        "previous_version_loaded": "bool"
    };

    const bool_key_emotion_if_true = {
        "available": "positive",
        "current_version_passes_validation": "positive",
        "current_version_loads_successfully": "positive",
        "passes_validation": "positive",
        "loads_successfully": "positive",
        "validation_success": "positive",
        "import_success": "positive",
        "success": "positive"
    };

    function handle_bool(td, value, property) {
        value = (value === null) ? null : (value !== 0);
        const emotion = bool_key_emotion_if_true[property];
        if (value != null) {
            if (emotion != null) {
                if (value) td.addClass(emotion === 'positive' ? 'positive' : 'negative');
                else td.addClass(emotion === 'positive' ? 'negative' : 'positive');
            }
            td.append($("<i>").addClass("icon").addClass(value ? "checkmark" : "close"))
        }
    }

    function render_toplevel() {
        const table = $('<table>').addClass('ui celled table unstackable');
        const thead = $('<thead>');
        const tr = $('<tr>');
        for (let i in top_level_headers) {
            tr.append($('<th>').text(display_names[i]))
        }
        thead.append(tr);
        table.append(thead);
        const tbody = $('<tbody>');
        top_level_data.forEach(function (row) {
            const tr = $('<tr>');
            for (let property in top_level_headers) {
                const value_type = top_level_headers[property];
                const value = row[property];
                const td = $('<td>').data('label', property);
                if (value_type === "bool") {
                    handle_bool(td, value, property)
                }
                else if (property === "study_name") {
                    const link = $('<a>');
                    link.addClass('secondlevel-link');
                    link.text(value);
                    link.attr('href', '#');
                    link.data('study-id', row['study_id']);
                    link.data('study-name', row['study_name']);
                    td.append(link)
                } else {
                    td.text(value)
                }

                tr.append(td)
            }
            tbody.append(tr)
        });
        table.append(tbody);
        main.empty();
        main.append(table);
        $('.secondlevel-link').click(function () {
            render_secondlevel($(this).data('study-id'), $(this).data('study-name'))
        });
        $('#main-breadcrumb').nextAll().remove()
    }

    function render_secondlevel(study_id, study_name) {
        const table = $('<table>').addClass('ui celled table unstackable');
        const thead = $('<thead>');
        const tr = $('<tr>');
        for (let i in second_level_headers) {
            tr.append($('<th>').text(display_names[i]))
        }
        thead.append(tr);
        table.append(thead);
        const tbody = $('<tbody>');
        second_level_data.forEach(function (row) {
            if (!(row.study_id === study_id)) {
                return
            }
            const tr = $('<tr>');
            for (let property in second_level_headers) {
                let link;
                const value_type = second_level_headers[property];
                const value = row[property];
                const td = $('<td>').data('label', property);
                if (value_type === "bool") {
                    handle_bool(td, value, property)
                } else if (property === "validation_time_added") {
                    link = $('<a>');
                    link.addClass('validation-link');
                    link.text(value);
                    link.attr('href', '#');
                    link.data('study-version-id', row['study_version_id']);
                    td.append(link)
                } else if (property === "import_time_added") {
                    link = $('<a>');
                    link.addClass('import-link');
                    link.text(value);
                    link.attr('href', '#');
                    link.data('study-version-id', row['study_version_id']);
                    td.append(link)
                }
                else {
                    td.text(value)
                }
                tr.append(td)
            }
            tbody.append(tr)
        });
        table.append(tbody);
        main.empty();
        main.append(table);
        $('.validation-link').click(function () {
            render_validation($(this).data('study-version-id'))
        });
        $('.import-link').click(function () {
            render_import($(this).data('study-version-id'))
        });

        breadcrumbs.append($('<i>').addClass('right angle icon divider'));
        breadcrumbs.append($('<a>').addClass('section').attr('id', 'secondlevel-breadcrumb').text(study_name));
        const secondlevel_breadcrumb = $('#secondlevel-breadcrumb');
        secondlevel_breadcrumb.click(function () {
            render_secondlevel(study_id, study_name)
        });
        secondlevel_breadcrumb.nextAll().remove()
    }

    const validation_headers = {
        "level": "text",
        "path": "text",
        "message": "text"
    };

    function render_validation(study_version_id) {
        const rx = /^((([A-Z]+):\W([a-zA-Z0-9\/\s_\\.\-():]+?):\s*(.*))|(.*\w.*))$/gm;
        let m;
        const table = $('<table>').addClass('ui celled table unstackable');
        const thead = $('<thead>');
        const tr = $('<tr>');
        for (let i in validation_headers) {
            tr.append($('<th>').text(display_names[i]))
        }
        thead.append(tr);
        table.append(thead);
        const tbody = $('<tbody>');
        study_version_validation.forEach(function (row) {
            if (!(row.study_version_id === study_version_id)) {
                return
            }
            while ((m = rx.exec(row['output'])) !== null) {
                // This is necessary to avoid infinite loops with zero-width matches
                if (m.index === rx.lastIndex) {
                    rx.lastIndex++;
                }

                // The result can be accessed through the `m`-variable.
                const level = m[3];
                const path = m[4];
                const message = m[5];
                const tr = $('<tr>').addClass((level === "WARNING") ? "warning" : (level === "INFO") ? "positive" : (level === "ERROR") ? "negative" : "");
                const level_td = $('<td>').data('label', 'level').text(level);
                const level_path = $('<td>').data('label', 'path').text(path);
                const level_message = $('<td>').data('label', 'message').text(message);
                tr.append(level_td).append(level_path).append(level_message);
                tbody.append(tr)

            }
        });
        table.append(tbody);
        main.empty();
        main.append(table);
        breadcrumbs.append($('<i>').addClass('right angle icon divider'));
        breadcrumbs.append($('<a>').addClass('section').attr('id', '#validation-breadcrumb').text("study version " + study_version_id + " validation"));
        $('#validation-breadcrumb').nextAll().remove()
    }

    const import_headers = {"output": "text"};

    function render_import(study_version_id) {
        const table = $('<table>').addClass('ui celled table unstackable');
        const thead = $('<thead>');
        const tr = $('<tr>');
        for (let i in import_headers) {
            tr.append($('<th>').text(display_names[i]))
        }
        thead.append(tr);
        table.append(thead);
        const tbody = $('<tbody>');
        study_version_import.forEach(function (row) {
            if (!(row.study_version_id === study_version_id)) {
                return
            }
            const tr = $('<tr>');
            const pre = $('<pre>').text(row['output']);
            const td = $('<td>').data('label', 'level');
            td.append(pre);
            tr.append(td);
            tbody.append(tr)
        });
        table.append(tbody);
        main.empty();
        main.append(table);
        breadcrumbs.append($('<i>').addClass('right angle icon divider'));
        breadcrumbs.append($('<a>').addClass('section').attr('id', '#import-breadcrumb').text("study import " + study_version_id + " output"));
        $('#import-breadcrumb').nextAll().remove()
    }

    render_toplevel();
    $("#main-breadcrumb").click(function () {
        render_toplevel()
    })
});