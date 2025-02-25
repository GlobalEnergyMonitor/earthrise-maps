var config = {

    /* name of the data file; use key `csv` if data file is CSV format */
    // csv: 'GOGET_Earthgenome_file2024-04-01.csv',
    csv: 'compilation_output/Oil & Gas Extraction-map-file-2025-02-21.csv',
    
    /* Define labels for sitewide colors, referenced in tracker config */
    colors: {
        'red': '#c74a48',
        'blue': '#5c62cf',
        'green': '#4c9d4f',
        'grey': '#8f8f8e',
        'black': '#000000',
    },

    /* define the column and associated values for color application */
    countryField: 'country/area',
    linkField: 'unit-id',
    urlField: 'url',

    color: {
        field: 'status',
        values: {
            'operating': 'red',
            'in_development': 'blue',
            'discovered': 'blue',
            'shut_in': 'green',
            'decommissioned': 'green',
            'cancelled': 'green',
            'abandoned': 'grey',
            'UGS': 'grey',
            'not_found': 'black'
        }
    },

    /* define the column and values used for the filter UI. There can be multiple filters listed. 
      Additionally a custom `label` can be defined (default is the field), 
      and `values_label` (an array matching elements in `values`)
      */
    filters: [
        {
            field: 'status',
            values: ['operating', 'in_development', 'discovered', 'shut_in', 'decommissioned', 'cancelled', 'abandoned', 'UGS', ""],
            values_labels: ['Operating','In development','Discovered','Shut in','Decommissioned','Cancelled','Abandoned','UGS','Not found']
        }
    ],

    /* define the field for calculating and showing capacity along with label.
       this is defined per tracker since it varies widely */
    capacityField: 'production---total-(oil,-gas-and-hydrocarbons)-(million-boe/y)',
    capacityDisplayField: 'capacity',
    // capacityLabel: 'million boe/y',
    capacityLabel: '', // (million boe/y)
    /* Labels for describing the assets */
    assetFullLabel: "Oil & Gas Extraction Areas",
    assetLabel: 'areas',

    /* the column that contains the asset name. this varies between trackers */
    nameField: 'wiki-name',
    statusDisplayField: 'status_display',
    /* configure the table view, selecting which columns to show, how to label them, 
        and designated which column has the link */
    
    tableHeaders: {
        values: ['wiki-name', 'operator', 'status_display', 'country/area', 'subnational-unit-(province,-state)', 'production---oil-(million-bbl/y)', 'production---gas-(million-m³/y)', 'production-year---oil', 'production-year---gas', 'production-start-year',],        labels: ['Extraction Area', 'Operator', 'Status','Country/Area(s)','Subnational unit (province/state)', 'Production - Oil (Million bbl/y)', 'Production - Gas (Million m³/y)', 'Production Year - Oil', 'Production Year - Gas', 'Production start year',],
        clickColumns: ['wiki-name'],
        rightAlign: ['wiki-name','discovery-year', 'fid-year', 'production-start-year', 'production-year---gas', 'production---gas-(million-m³/y)', 'production-year---oil', 'production---oil-(million-bbl/y)', ]
    },

    /* configure the search box; 
        each label has a value with the list of fields to search. Multiple fields might be searched */
    searchFields: { 'Extraction Area': ['wiki-name'], 
        'Companies': ['owner', 'operator', 'parent'],
        'Discovery Year': ['discovery-year'],
        'Production start year': ['production-start-year']
    },

    /* define fields and how they are displayed. 
      `'display': 'heading'` displays the field in large type
      `'display': 'range'` will show the minimum and maximum values.
      `'display': 'join'` will join together values with a comma separator
      `'display': 'location'` will show the fields over the detail image
      `'label': '...'` prepends a label. If a range, two values for singular and plural.
    */
    detailView: {
        'wiki-name': {'display': 'heading'},
        // 'status': {'label': 'Status'},
        'loc_accuracy': {'label': 'Location Accuracy'},
        'operator': {'label': 'Operator'},
        'discovery-year': {'label': 'Discovery Year'},
        'fid-year': {'label': 'FID Year'},
        'production-start-year': {'label': 'Production Start Year'},
        'production-year---oil': {'label': 'Production Year - Oil'},
        'production-year---gas': {'label': 'Production Year - Gas'},
        'production---oil-(million-bbl/y)': {'label': 'Production - Oil (Million bbl/y)'},
        'production---gas-(million-m³/y)': {'label': 'Production - Gas (Million m³/y)'},
        'subnational-unit-(province,-state)': {'display': 'location'},
        'country/area': {'display': 'location'}
    },
    countryFile: './countries.js',
    showMaxCapacity: false,
}
