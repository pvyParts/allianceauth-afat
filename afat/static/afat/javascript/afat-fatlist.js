/* global afatSettings, moment, console, manageModal */

$(document).ready(function () {
    'use strict';

    const DATETIME_FORMAT = 'YYYY-MMM-DD, HH:mm';

    /**
     * DataTable :: FAT link list
     */
    let linkListTable = $('#link-list').DataTable({
        ajax: {
            url: afatSettings.url.linkList,
            dataSrc: '',
            cache: false
        },
        columns: [
            {data: 'fleet_name'},
            {data: 'fleet_type'},
            {data: 'creator_name'},
            {
                data: 'fleet_time',
                render: {
                    display: function (data, type, row) {
                        return moment(data.time).utc().format(DATETIME_FORMAT);
                    },
                    _: 'timestamp'
                }
            },
            {data: 'fats_number'},

            {
                data: 'actions',
                render: function (data, type, row) {
                    if (afatSettings.permissions.addFatLink === true || afatSettings.permissions.manageAfat === true) {
                        return data;
                    } else {
                        return '';
                    }
                }
            },

            // hidden column
            {data: 'via_esi'},
            {data: 'hash'}
        ],

        columnDefs: [
            {
                targets: [5],
                orderable: false,
                createdCell: function (td) {
                    $(td).addClass('text-right');
                }
            },
            {
                visible: false,
                targets: [6, 7]
            }
        ],

        order: [
            [3, 'desc']
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 1
                },
                {
                    idx: 6,
                    title: afatSettings.translation.dataTable.filter.viaEsi
                }
            ],
            autoSize: false,
            bootstrap: true
        }
    });

    /**
     * refresh the datatable information every 60 seconds
     */
    let intervalReloadDatatable = 60000; // ms
    let expectedReloadDatatable = Date.now() + intervalReloadDatatable;

    /**
     * reload datatable "linkListTable"
     */
    let realoadDataTable = function () {
        let dt = Date.now() - expectedReloadDatatable; // the drift (positive for overshooting)

        if (dt > intervalReloadDatatable) {
            // something really bad happened. Maybe the browser (tab) was inactive?
            // possibly special handling to avoid futile "catch up" run
            window.location.replace(
                window.location.pathname + window.location.search + window.location.hash
            );
        }

        linkListTable.ajax.reload();

        expectedReloadDatatable += intervalReloadDatatable;

        // take drift into account
        setTimeout(
            realoadDataTable,
            Math.max(0, intervalReloadDatatable - dt)
        );
    };

    setTimeout(
        realoadDataTable,
        intervalReloadDatatable
    );

    /**
     * Modal :: Delete FAT link
     */
    let deleteFatLinkModal = $(afatSettings.modal.deleteModal.element);
    manageModal(deleteFatLinkModal);
});
