import requests

def get_location():
    ip_request = requests.get('https://api.ipify.org?format=json')
    ip_address = ip_request.json()['ip']

    # Get the location data based on the IP address
    location_request = requests.get(f'https://ipinfo.io/{ip_address}/json')
    location_data = location_request.json()

    # Extract latitude and longitude
    location = location_data['loc'].split(',')
    latitude = location[0]
    longitude = location[1]
    return latitude, longitude
