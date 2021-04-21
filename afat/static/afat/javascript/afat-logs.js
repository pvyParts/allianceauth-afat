/* global afatSettings, moment, console, manageModal */

$(document).ready(function () {
    'use strict';

    const DATETIME_FORMAT = 'YYYY-MMM-DD, HH:mm';

    /**
     * DataTable :: FAT link list
     */
    $('#afat-logs').DataTable({
        ajax: {
            url: afatSettings.url.logs,
            dataSrc: '',
            cache: false
        },
        columns: [
            {
                data: 'log_time',
                render: {
                    display: function (data) {
                        return moment(data.time).utc().format(DATETIME_FORMAT);
                    },
                    _: 'timestamp'
                },
            },
            {data: 'log_event'},
            {data: 'user'},
            {data: 'fatlink'},
            {data: 'description'},
        ],

        order: [
            [0, 'desc']
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 1
                },
                {
                    idx: 2
                }
            ],
            autoSize: false,
            bootstrap: true
        }
    });
});
