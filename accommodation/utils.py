# accommodation/utils.py

import math
import requests
import json


def lookup_address(building_name):
    """
    Look up an address using the DATA.GOV.HK Address Lookup Service.
    """
    try:
        url = "https://www.als.gov.hk/lookup"
        params = {
            "q": building_name,
            "n": 1,
            "output": "json"  # Explicitly request JSON output
        }

        headers = {
            "Accept": "application/json"
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
            except ValueError:
                # If it's not JSON, print the first 100 chars to debug
                print(f"Response is not JSON: {response.text[:100]}...")
                return None
            # Parse based on the structure you provided
            if 'SuggestedAddress' in data and len(data['SuggestedAddress']) > 0:
                address_data = data['SuggestedAddress'][0]['Address']['PremisesAddress']

                # Extract English address components
                eng_address = address_data['EngPremisesAddress']
                building_name = eng_address.get('BuildingName', building_name)

                # Construct full address
                address_parts = []

                if 'BuildingName' in eng_address:
                    address_parts.append(eng_address['BuildingName'])

                if 'EngEstate' in eng_address and 'EstateName' in eng_address['EngEstate']:
                    address_parts.append(eng_address['EngEstate']['EstateName'])

                if 'EngStreet' in eng_address:
                    street = eng_address['EngStreet']
                    if 'BuildingNoFrom' in street:
                        address_parts.append(f"{street['BuildingNoFrom']} {street['StreetName']}")
                    else:
                        address_parts.append(street['StreetName'])

                if 'EngDistrict' in eng_address and 'DcDistrict' in eng_address['EngDistrict']:
                    address_parts.append(eng_address['EngDistrict']['DcDistrict'])

                if 'Region' in eng_address:
                    address_parts.append(eng_address['Region'])

                full_address = ", ".join(address_parts)

                # Get geospatial information
                geo_info = address_data.get('GeospatialInformation', {})
                latitude = float(geo_info.get('Latitude', 0))
                longitude = float(geo_info.get('Longitude', 0))
                geo_address = address_data.get('GeoAddress', '')

                return {
                    'name': building_name,
                    'address': full_address,
                    'latitude': latitude,
                    'longitude': longitude,
                    'geo_address': geo_address,
                    'is_campus': False
                }

        # If API call fails or no results, return None
        return None

    except Exception as e:
        print(f"Error looking up address: {str(e)}")
        return None

def calculate_distance(point1, point2):
    """
    Calculate distance between two points using equirectangular approximation.
    point1 and point2 are (latitude, longitude) tuples in degrees.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers

    # Convert to radians
    lat1 = math.radians(point1[0])
    lon1 = math.radians(point1[1])
    lat2 = math.radians(point2[0])
    lon2 = math.radians(point2[1])

    # Calculate the mean latitude for x calculation
    lat_mean = (lat1 + lat2) / 2

    # Calculate x and y differences
    x = (lon2 - lon1) * math.cos(lat_mean)
    y = lat2 - lat1

    # Calculate distance
    distance = math.sqrt(x * x + y * y) * R

    return distance


def get_address_info(building_name):
    url = "https://www.als.gov.hk/lookup"
    params = {
        "q": building_name,
        "n": 1,
        "output": "json"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        # Extract latitude, longitude and GeoAddress from response
        # This will depend on the exact structure of their API response
        return {
            'latitude': data['AddressLookupResult'][0]['Latitude'],
            'longitude': data['AddressLookupResult'][0]['Longitude'],
            'geo_address': data['AddressLookupResult'][0]['GeoAddress']
        }
    else:
        # Handle error
        return None



# Update in utils.py
CAMPUS_LOCATIONS = {
    # HKU
    'Main Campus': (22.28405, 114.13784),
    'Sassoon Road Campus': (22.2675, 114.12881),
    'Swire Institute of Marine Science': (22.20805, 114.26021),
    'Kadoorie Centre': (22.43022, 114.11429),
    'Faculty of Dentistry': (22.28649, 114.14426),
    # HKUST
    'HKUST Campus': (22.33584, 114.26355),
    # CUHK
    'CUHK Campus': (22.41907, 114.20693),
}

def get_campus_coordinates(campus_name):
    """Get coordinates for a named HKU campus."""
    return CAMPUS_LOCATIONS.get(campus_name.lower())