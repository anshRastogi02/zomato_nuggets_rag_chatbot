import location, requests, json, re, os

class Scraper():
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        self.page_no = 1
        self.get_initial_data()
    
    def get_current_area(self):
        lat, lon = location.get_location()
        
        url = f"https://www.zomato.com/webroutes/location/get?lat={lat}&lon={lon}"

        response = requests.get(url, headers=self.headers)

        return response.json()
    
    def get_initial_data(self):
        self.location_data = self.get_current_area()['locationDetails']

        url = f"https://www.zomato.com/vadodara/delivery?delivery_subzone={self.location_data['deliverySubzoneId']}&place_name={self.location_data['orderLocationName']}"

        get_response = self.session.get(url, headers=self.headers)

        self.csrf_token = self.session.cookies.get_dict().get('csrf')

        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*JSON\.parse\("(.+?)"\);', get_response.text)

        if match:
            json_str = match.group(1).encode('utf-8').decode('unicode_escape')
            filters = next(iter(json.loads(json_str)['pages']['search'].values()))['sections']['SECTION_SEARCH_META_INFO']['searchMetaData']
            filters.pop('filterInfo')

            previousSearchParams = json.loads(filters['previousSearchParams'])
            self.PreviousSearchId = previousSearchParams['PreviousSearchId']
            self.category_context = json.loads(previousSearchParams['PreviousSearchFilter'][0])['category_context']

            postbackParams = json.loads(filters['postbackParams'])
            self.processed_chain_ids = []
            self.shown_res_count = 0
            self.search_id = postbackParams['search_id']

            self.totalResults = filters['totalResults']

            self.hasMore = str(filters['hasMore']).lower()

            self.getInactive = str(filters['getInactive']).lower()

        else:
            print("JSON not found")

    def get_restaurants(self, write_json=False):
        os.makedirs("restaurant_data", exist_ok=True)

        print(f"getting restaurants page {self.page_no}")

        post_url = "https://www.zomato.com/webroutes/search/home"
        self.headers.update({
            "x-zomato-csrft": self.csrf_token,
        })

        filters = "{\"searchMetadata\":{\"previousSearchParams\":\"{\\\"PreviousSearchId\\\":\\\"%s\\\",\\\"PreviousSearchFilter\\\":[\\\"{\\\\\\\"category_context\\\\\\\":\\\\\\\"%s\\\\\\\"}\\\",\\\"\\\"]}\",\"postbackParams\":\"{\\\"processed_chain_ids\\\":%s,\\\"shown_res_count\\\":%s,\\\"search_id\\\":\\\"%s\\\"}\",\"totalResults\":%s,\"hasMore\":%s,\"getInactive\":%s},\"appliedFilter\":[{\"filterType\":\"category_sheet\",\"filterValue\":\"delivery_home\",\"isHidden\":true,\"isApplied\":true,\"postKey\":\"{\\\"category_context\\\":\\\"delivery_home\\\"}\"}]}"%(self.PreviousSearchId, self.category_context, self.processed_chain_ids, self.shown_res_count, self.search_id, self.totalResults, self.hasMore, self.getInactive)
        data = {
            **self.location_data,
            "context": "delivery_home",
            "filters": filters,
        }

        post_response = self.session.post(post_url, headers=self.headers, json=data)

        data = post_response.json()
        
        postbackParams = json.loads(data['sections']['SECTION_SEARCH_META_INFO']['searchMetaData']['postbackParams'])
        self.processed_chain_ids = postbackParams['processed_chain_ids']
        self.shown_res_count = postbackParams['shown_res_count']

        if write_json:
            with open(f"restaurant_data/restaurants_page{self.page_no}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        self.page_no += 1
        return data['sections']['SECTION_SEARCH_RESULT']

    def get_menu(self, restaurant_data, write_json=False):
        os.makedirs("menus", exist_ok=True)
        
        restaurant_name = restaurant_data['info']['name']
        restaurant_url = restaurant_data['order']['actionInfo']['clickUrl']

        print(f"getting menu for {restaurant_name}")


        url = f"https://www.zomato.com/webroutes/getPage?page_url={restaurant_url}"

        get_response = self.session.get(url, headers=self.headers)

        data = get_response.json()

        if write_json:
            with open(f"menus/{restaurant_name}_menu.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        return data