// Cookie Definitions
// Configuration for all available proxy cookies
// Update this file to add/modify cookie options

const COOKIE_DEFINITIONS = [
    {
        name: 'mitm-mode',
        description: 'Control Html content mode',
        type: 'select',
        options: [   { value: 'cache'           , label: 'Cache (Html Graph)'     },
                     { value: 'xxx'           , label: 'Html to XXX'              },
        //           { value: 'xxx-random'    , label: 'Html to XXX (Random)'     },
                     { value: 'hashes'        , label: 'Html to Hashes'           },
        //           { value: 'hashes-random' , label: 'Html to Hashes (Random)'  },
                     { value: 'abcde-by-size' , label: 'Html to ABCDE (by size)'  },
        //           { value: 'roundtrip'     , label: 'Html to Html (roundtrip)' }],
                     { value: 'xxx-negative-0.5' , label: 'Show XXX | Negative > 0.5'  } ,
                     { value: 'xxx-negative-1'   , label: 'Show XXX | Negative > 1'  } ,
                     { value: 'xxx-negative-2'   , label: 'Show XXX | Negative > 2'  } ,
                     { value: 'xxx-negative-3'   , label: 'Show XXX | Negative > 3'  } ,
                     { value: 'xxx-negative-4'   , label: 'Show XXX | Negative > 4'  } ,
                ]
        },
     {
        name: 'mitm-show',
        description: 'Control content display',
        type: 'select',
        options: [ { value: 'url-to-html-min-rating' , label: 'Filter content (with min 0.5)' },
                   { value: 'url-to-html-xxx'        , label: 'Url to Html XXX'         },
                   { value: 'url-to-html-hashes'     , label: 'Url to Html Hashes'      },
                   { value: 'url-to-html-dict'       , label: 'Url to Html Dict (json)' },
                   { value: 'url-to-html-ratings'    , label: 'Url to Html Ratings'     },
                   { value: 'url-to-html-min-rating' , label: 'Url to Html Min Rating'  },
                   { value: 'url-to-lines'           , label: 'Url to Html Lines'       },
                   { value: 'url-to-text-nodes'      , label: 'Url to Text Nodes (json)'},
                   { value: 'url-to-ratings'         , label: 'Url to Ratings'          },
                   { value: 'response-data'          , label: 'Response Data (json)'    }]
    },
    {
        name: 'mitm-inject',
        description: 'Inject debug content',
        type: 'select',
        options: [
            { value: 'debug-panel', label: 'Debug Panel' },
            { value: 'debug-banner', label: 'Debug Banner' }
        ]
    },
    {
        name: 'mitm-replace',
        description: 'Replace text (format: old:new)',
        type: 'text',
        placeholder: 'oldtext:newtext'
    },
    {
        name: 'mitm-debug',
        description: 'Enable debug mode',
        type: 'select',
        options: [
            { value: 'true', label: 'Enabled (true)' },
            { value: 'false', label: 'Disabled (false)' }
        ]
    },
    {
        name: 'mitm-rating',
        description: 'Set minimum rating threshold',
        type: 'number',
        placeholder: '0.5',
        min: '0',
        max: '1',
        step: '0.1'
    },
    {
        name: 'mitm-model',
        description: 'Override WCF model',
        type: 'text',
        placeholder: 'google/gemini-2.0-flash-lite-001'
    },
    {
        name: 'mitm-cache',
        description: 'Enable response caching',
        type: 'select',
        options: [
            { value: 'true', label: 'Enabled (true)' },
            { value: 'false', label: 'Disabled (false)' }
        ]
    }
];
