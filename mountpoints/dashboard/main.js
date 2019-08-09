/* globals $, document */

let top_level_data = [];

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
    "validation_status_code": "Validation Result",
    "validation_time_added": "Validation Time Added",
    "import_success": "Import Success",
    "import_status_code": "Import Result",
    "import_time_added": "Import Time Added",
    "output": "Output",
    "level": "Log Level",
    "path": "Path",
    "message": "Log Message",
    "Validation Results": "Validation Results",
    "Import Results": "Import Results"
};

function timeConverter(UNIX_timestamp) {
    if (UNIX_timestamp == null) return UNIX_timestamp;
    const a = new Date(UNIX_timestamp * 1000);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const year = a.getFullYear();
    const month = months[a.getMonth()];
    const date = a.getDate();
    const hour = a.getHours();
    const min = a.getMinutes();
    const sec = a.getSeconds();
    return date + ' ' + month + ' ' + year + (' ' + hour).padStart(2, "0") + (':' + min).padStart(2, "0") + (':' + sec).padStart(2, "0")
}

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
    let ElemAjaxGetText = function (elem, url) {
        $.ajax({
            type: "GET",
            url: url,
            param: '{}',
            contentType: "text/plain; charset=utf-8",
            dataType: "text",
            async: true,
            success: function (data) {
                elem.text(data)
            }
        });
    };

    top_level_data = AjaxGet("/cbioportaldashboard/data/top_level.json");
    second_level_data = AjaxGet("/cbioportaldashboard/data/second_level.json");

    const second_level_headers = {
        //"passes_validation": "bool",
        //"loads_successfully": "bool",
        //"currently_loaded": "bool",
        //"validation_success": "bool",
        //"validation_status_code": "exit_code",
        //"validation_time_added": "timestamp",
        //"import_success": "bool",
        //"import_status_code": "exit_code",
        "import_time_added": "timestamp",
        "Validation Results": "text",
        "Import Results": "text"
    };

    const top_level_headers = {
        "study_name": "text",
        //"current_version_passes_validation": "bool",
        //"current_version_loads_successfully": "bool",
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
            if (row['current_version_loaded'] || row['previous_version_loaded']) tr.addClass('positive');
            else if (!(row['current_version_loaded'] == null && row['previous_version_loaded'] == null))
                tr.addClass('negative');
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

    const link_info_lookup = {
        'Import Results': 'import-link',
        'Validation Results': 'validation-link'
    };
    const othermap = {
        'Import Results': 'import_status_code',
        'Validation Results': 'validation_status_code'
    };

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

                    const value_type = second_level_headers[property];
                    const value = row[property];
                    const td = $('<td>').data('label', property);
                    if (value_type === "bool") {
                        handle_bool(td, value, property)
                    } else if (property === "validation_time_added") {
                        td.text(timeConverter(value));
                    } else if (value_type === "exit_code") {
                        if ([0, 1, 2, 3].includes(value))
                            td.text(value === 0 ? "SUCCESS" : (value === 3 ? "WARNING" : "ERROR"));
                    } else if (property === "import_time_added") {
                        td.text(timeConverter(value));
                    } else if (["Import Results", "Validation Results"].includes(property)) {
                        const click_here = $('<td>').data('label', property);
                        let link = $('<a>');
                        link.addClass(link_info_lookup[property]);
                        link.attr('href', '#');
                        link.data('study-version-id', row['study_version_id']);
                        link.text(row[othermap[property]] === 0 ? "SUCCESS" : (row[othermap[property]] === 3 ? "WARNING" : "ERROR"));
                        click_here.append(link);
                        td.append(click_here);
                    }
                    else {
                        td.text(value)
                    }
                    tr.append(td)
                }
                tbody.append(tr)
            }
        );
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

    function render_validation(study_version_id) {
        const iframe = $('<iframe>')
            .attr("height", "100%")
            .attr("width", "100%")
            .attr("src", "/cbioportaldashboard/validation/" + study_version_id + ".html")
            .attr("frameborder", 0);
        main.empty();
        main.append(iframe);
        breadcrumbs.append($('<i>').addClass('right angle icon divider'));
        breadcrumbs.append($('<a>').addClass('section').attr('id', '#validation-breadcrumb').text("study version " + study_version_id + " validation"));
        $('#validation-breadcrumb').nextAll().remove()
    }


    function render_import(study_version_id) {
        const table = $('<table>').addClass('ui celled table unstackable');
        const thead = $('<thead>');
        const tr = $('<tr>');
        tr.append($('<th>').text(display_names["output"]))
        thead.append(tr);
        table.append(thead);
        const tbody = $('<tbody>');
        const tr_inner = $('<tr>');
        const pre = $('<pre>').addClass('pretag-import')
        const td = $('<td>').data('label', 'level');
        td.append(pre);
        tr.append(td);
        tbody.append(tr_inner);
        table.append(tbody);
        main.empty();
        main.append(table);
        ElemAjaxGetText($('.pretag-import'), '/cbioportaldashboard/import/' + study_version_id + '.txt');
        breadcrumbs.append($('<i>').addClass('right angle icon divider'));
        breadcrumbs.append($('<a>').addClass('section').attr('id', '#import-breadcrumb').text("study import " + study_version_id + " output"));
        $('#import-breadcrumb').nextAll().remove()
    }

    render_toplevel();
    $("#main-breadcrumb").click(function () {
        render_toplevel()
    })
})
;