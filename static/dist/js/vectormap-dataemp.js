
$(function() {
    "use strict";

    // Define a mapping of country names to country codes
    var countryCodeMapping = {
        'USA': 'US',
        'Afghanistan': 'AF',
        'Albania': 'AL',
        'Algeria': 'DZ',
        'Andorra': 'AD',
        'Angola': 'AO',
        'Antigua and Barbuda': 'AG',
        'Argentina': 'AR',
        'Armenia': 'AM',
        'Australia': 'AU',
        'Austria': 'AT',
        'Azerbaijan': 'AZ',
        'Bahamas': 'BS',
        'Bahrain': 'BH',
        'Bangladesh': 'BD',
        'Barbados': 'BB',
        'Belarus': 'BY',
        'Belgium': 'BE',
        'Belize': 'BZ',
        'Benin': 'BJ',
        'Bhutan': 'BT',
        'Bolivia': 'BO',
        'Bosnia and Herzegovina': 'BA',
        'Botswana': 'BW',
        'Brazil': 'BR',
        'Brunei': 'BN',
        'Bulgaria': 'BG',
        'Burkina Faso': 'BF',
        'Burundi': 'BI',
        'Cabo Verde': 'CV',
        'Cambodia': 'KH',
        'Cameroon': 'CM',
        'Canada': 'CA',
        'Central African Republic': 'CF',
        'Chad': 'TD',
        'Chile': 'CL',
        'China': 'CN',
        'Colombia': 'CO',
        'Comoros': 'KM',
        'Congo (Congo-Brazzaville)': 'CG',
        'Congo, Democratic Republic of the (Congo-Kinshasa)': 'CD',
        'Costa Rica': 'CR',
        'Croatia': 'HR',
        'Cuba': 'CU',
        'Cyprus': 'CY',
        'Czech Republic': 'CZ',
        'Denmark': 'DK',
        'Djibouti': 'DJ',
        'Dominica': 'DM',
        'Dominican Republic': 'DO',
        'East Timor': 'TL',
        'Ecuador': 'EC',
        'Egypt': 'EG',
        'El Salvador': 'SV',
        'Equatorial Guinea': 'GQ',
        'Eritrea': 'ER',
        'Estonia': 'EE',
        'Eswatini': 'SZ',
        'Ethiopia': 'ET',
        'Fiji': 'FJ',
        'Finland': 'FI',
        'France': 'FR',
        'Gabon': 'GA',
        'Gambia': 'GM',
        'Georgia': 'GE',
        'Germany': 'DE',
        'Ghana': 'GH',
        'Greece': 'GR',
        'Grenada': 'GD',
        'Guatemala': 'GT',
        'Guinea': 'GN',
        'Guinea-Bissau': 'GW',
        'Guyana': 'GY',
        'Haiti': 'HT',
        'Honduras': 'HN',
        'Hungary': 'HU',
        'Iceland': 'IS',
        'India': 'IN',
        'Indonesia': 'ID',
        'Iran': 'IR',
        'Iraq': 'IQ',
        'Ireland': 'IE',
        'Israel': 'IL',
        'Italy': 'IT',
        'Jamaica': 'JM',
        'Japan': 'JP',
        'Jordan': 'JO',
        'Kazakhstan': 'KZ',
        'Kenya': 'KE',
        'Kiribati': 'KI',
        'Korea, North': 'KP',
        'Korea, South': 'KR',
        'Kosovo': 'XK',
        'Kuwait': 'KW',
        'Kyrgyzstan': 'KG',
        'Laos': 'LA',
        'Latvia': 'LV',
        'Lebanon': 'LB',
        'Lesotho': 'LS',
        'Liberia': 'LR',
        'Libya': 'LY',
        'Liechtenstein': 'LI',
        'Lithuania': 'LT',
        'Luxembourg': 'LU',
        'Madagascar': 'MG',
        'Malawi': 'MW',
        'Malaysia': 'MY',
        'Maldives': 'MV',
        'Mali': 'ML',
        'Malta': 'MT',
        'Marshall Islands': 'MH',
        'Mauritania': 'MR',
        'Mauritius': 'MU',
        'Mexico': 'MX',
        'Micronesia': 'FM',
        'Moldova': 'MD',
        'Monaco': 'MC',
        'Mongolia': 'MN',
        'Montenegro': 'ME',
        'Morocco': 'MA',
        'Mozambique': 'MZ',
        'Myanmar (Burma)': 'MM',
        'Namibia': 'NA',
        'Nauru': 'NR',
        'Nepal': 'NP',
        'Netherlands': 'NL',
        'New Zealand': 'NZ',
        'Nicaragua': 'NI',
        'Niger': 'NE',
        'Nigeria': 'NG',
        'North Macedonia': 'MK',
        'Norway': 'NO',
        'Oman': 'OM',
        'Pakistan': 'PK',
        'Palau': 'PW',
        'Panama': 'PA',
        'Papua New Guinea': 'PG',
        'Paraguay': 'PY',
        'Peru': 'PE',
        'Philippines': 'PH',
        'Poland': 'PL',
        'Portugal': 'PT',
        'Qatar': 'QA',
        'Romania': 'RO',
        'Russia': 'RU',
        'Rwanda': 'RW',
        'Saint Kitts and Nevis': 'KN',
        'Saint Lucia': 'LC',
        'Saint Vincent and the Grenadines': 'VC',
        'Samoa': 'WS',
        'San Marino': 'SM',
        'Sao Tome and Principe': 'ST',
        'Saudi Arabia': 'SA',
        'Senegal': 'SN',
        'Serbia': 'RS',
        'Seychelles': 'SC',
        'Sierra Leone': 'SL',
        'Singapore': 'SG',
        'Slovakia': 'SK',
        'Slovenia': 'SI',
        'Solomon Islands': 'SB',
        'Somalia': 'SO',
        'South Africa': 'ZA',
        'South Sudan': 'SS',
        'Spain': 'ES',
        'Sri Lanka': 'LK',
        'Sudan': 'SD',
        'Suriname': 'SR',
        'Sweden': 'SE',
        'Switzerland': 'CH',
        'Syria': 'SY',
        'Taiwan': 'TW',
        'Tajikistan': 'TJ',
        'Tanzania': 'TZ',
        'Thailand': 'TH',
        'Togo': 'TG',
        'Tonga': 'TO',
        'Trinidad and Tobago': 'TT',
        'Tunisia': 'TN',
        'Turkey': 'TR',
        'Turkmenistan': 'TM',
        'Tuvalu': 'TV',
        'Uganda': 'UG',
        'Ukraine': 'UA',
        'United Arab Emirates': 'AE',
        'United Kingdom': 'GB',
        'United States': 'US',
        'Uruguay': 'UY',
        'Uzbekistan': 'UZ',
        'Vanuatu': 'VU',
        'Vatican City': 'VA',
        'Venezuela': 'VE',
        'Vietnam': 'VN',
        'Yemen': 'YE',
        'Zambia': 'ZM',
        'Zimbabwe': 'ZW'
    };
    
	

    // Fetch data from the server
    $.get('/Employee/get_country_data/', function(data) {
        console.log("testittt armm")
        if ($('#world_map_marker_1').length > 0) {
            // Create a data object for the map
            var mapData = {};
            var customColors = {};
			var testing = {}
            // for (var i = 0; i < data.length; i++) {
            //     // Use the country code based on the mapping
            //     var countryCode = countryCodeMapping[data[i].Visa_country__country];
			// 	testing = data[i].Visa_country__country
			// 	console.log("ssssssssssssss",testing)
            //     mapData[countryCode] = data[i].total_inquiries;

			// 	// console.log("heeeeeeeeeeeee",testing)
				

            //     // Check if there is an inquiry in the country and set a custom color
            //     if (data[i].total_inquiries > 0) {
            //         customColors[countryCode] = '#21325d';
            //     }
            // }

            for (var i = 0; i < data.length; i++) {
                // Use the country code based on the mapping
                var countryCode = countryCodeMapping[data[i].Visa_country__country];
                mapData[countryCode] = {
                    total_inquiries: data[i].total_inquiries,
                    country_id: data[i].Visa_country__id,
                    country_name: data[i].Visa_country__country,
                  
                };
               
            
                // Check if there is an inquiry in the country and set a custom color
                if (data[i].total_inquiries > 0) {
                    customColors[countryCode] = '#21325d';
                }
            }
            
			

			

            $('#world_map_marker_1').vectorMap({
                map: 'world_mill_en',
                backgroundColor: 'transparent',
                borderColor: '#fff',
                borderOpacity: 0.25,
                borderWidth: 0,
                color: '#e6e6e6',
                regionStyle: {
                    initial: {
                        fill: '#f4f4f4'
                    }
                },
                markerStyle: {
                    initial: {
                        r: 10,
                        'fill': '#fff',
                        'fill-opacity': 1,
                        'stroke': '#000',
                        'stroke-width': 1,
                        'stroke-opacity': 0.4
                    },
                },
                markers: [],
                series: {
                    regions: [{
                        values: mapData,
                        attribute: 'fill'
						
                    }]
                },
                hoverOpacity: null,
                normalizeFunction: 'linear',
                zoomOnScroll: false,
                scaleColors: ['#000000', '#000000'],
                selectedColor: '#000000',
                selectedRegions: [],
                enableZoom: false,
                hoverColor: '#fff',
                onRegionTipShow: function(event, label, code) {
                    // label.html(label.html() + ': ' + mapData[code]);
                    var countryData = mapData[code];
                    label.html(label.html() + '<br> Total Leads: ' + countryData.total_inquiries);
                },
                onRegionClick: function (event, code,demo) {
                    // Redirect to the leads detail page for the clicked country
                    // window.location.href = '/Admin/leads/detail/?country=' + testing[demo];
					// window.location.href = '/Admin/leads/detail/' + testing[demo];
                    var countryData = mapData[code];
                    var countryId = countryData.country_id;
                    var countryName = countryData.country_name;
                
					window.location.href = `/Employee/leads/details/${countryName}`;

                }
            });

            // Add the custom colors for countries with inquiries to the map
            $('#world_map_marker_1').vectorMap('set', 'regions', customColors);
        }
    });
});

