from scrapping_script import Scraper

if __name__ == "__main__":

    user_1 = Scraper()
    data = user_1.get_restaurants(write_json=True)
    next_data = user_1.get_restaurants(write_json=True)
    for restaurant_data in data:
        restaurant_menu = user_1.get_menu(restaurant_data, write_json=True)
    