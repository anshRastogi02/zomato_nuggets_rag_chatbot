import os
import json

def extract_chunks_from_file(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = []

    # Extract restaurant and location info
    restaurant = {
        "restaurant_name": data.get("page_info", {}).get("pageTitle", ""),
        "restaurant_description": data.get("page_info", {}).get("pageDescription", ""),
        "res_id": data.get("page_info", {}).get("resId", ""),
        "page_url": data.get("page_info", {}).get("pageUrl", ""),
        "canonical_url": data.get("page_info", {}).get("canonicalUrl", "")
    }

    location = {
        "latitude": data.get("location", {}).get("latitude", ""),
        "longitude": data.get("location", {}).get("longitude", ""),
        "user_defined_latitude": data.get("location", {}).get("userDefinedLatitude", ""),
        "user_defined_longitude": data.get("location", {}).get("userDefinedLongitude", ""),
        "entity_name": data.get("location", {}).get("entityName", ""),
        "entity_type": data.get("location", {}).get("entityType", ""),
        "order_location_name": data.get("location", {}).get("orderLocationName", ""),
        "place_name": data.get("location", {}).get("placeName", "")
    }

    menus = data.get("page_data", {}).get("order", {}).get("menuList", {}).get("menus", [])
    for menu_entry in menus:
        menu = menu_entry.get("menu", {})
        menu_name = menu.get("name", "")
        categories = menu.get("categories", [])

        for category_entry in categories:
            category = category_entry.get("category", {})
            category_name = category.get("name", "")
            items = category.get("items", [])

            for item_entry in items:
                item = item_entry.get("item", {})

                chunk = {
                    "restaurant": restaurant,
                    "location": location,
                    "name": item.get("name", ""),
                    "price": item.get("price"),
                    "min_price": item.get("min_price"),
                    "max_price": item.get("max_price"),
                    "desc": item.get("desc", ""),
                    "rating_value": item.get("rating", {}).get("value") if item.get("rating") else None,
                    "total_ratings": item.get("rating", {}).get("total_rating_text") if item.get("rating") else None,
                    "name_slug": item.get("name_slug", ""),
                    "item_type": item.get("item_type", ""),
                    "category": category_name,
                    "menu": menu_name,
                    "tag_slugs": item.get("tag_slugs", []),
                    "dietary_slugs": item.get("dietary_slugs", []),
                    "availability": item.get("item_state", "Unknown"),
                    "discount_info": item.get("offer", {}).get("text", ""),
                    "media": [
                            media_item.get("image", {}).get("url", "")
                            for media_item in item.get("media", [])
                            if media_item.get("mediaType") == "image" and media_item.get("image", {}).get("url")
                        ]

                }

                chunks.append(chunk)

    return chunks

def generate_text_blob(chunk):
    restaurant = chunk.get("restaurant", {})
    location = chunk.get("location", {})

    return f"""Dish: {chunk.get("name", "")}
Description: {chunk.get("desc", "")}
Price: ₹{chunk.get("price", "N/A")}
Price Range: ₹{chunk.get("min_price", "N/A")} - ₹{chunk.get("max_price", "N/A")}
Available: {chunk.get("availability", "Unknown")}
Image URLs: {', '.join(chunk.get("media", [])) or "N/A"}
Menu: {chunk.get("menu", "")}
Category: {chunk.get("category", "Not Specified")}
Rating: {chunk.get("rating_value", "N/A")} ({chunk.get("total_ratings", "No votes")})
Tags: {", ".join(chunk.get("tag_slugs", []))}
Dietary Preferences: {", ".join(chunk.get("dietary_slugs", []))}

Restaurant: {restaurant.get("restaurant_name", "")}
Restaurant Description: {restaurant.get("restaurant_description", "")}
Restaurant Page: https://www.zomato.com{restaurant.get("page_url", "")}

Location: {location.get("entity_name", "")}
Entity Type: {location.get("entity_type", "")}
Latitude: {location.get("latitude", "")}, Longitude: {location.get("longitude", "")}
User Defined Location: {location.get("user_defined_latitude", "")}, {location.get("user_defined_longitude", "")}
Place Name: {location.get("place_name", "")}
"""


def process_all_jsons(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)
            chunks = extract_chunks_from_file(input_path)
            blobs = [generate_text_blob(chunk) for chunk in chunks]

            output_filename = os.path.splitext(filename)[0] + "_blobs.txt"
            output_path = os.path.join(output_folder, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                for blob in blobs:
                    f.write(blob + "\n\n" + "=" * 80 + "\n\n")

            print(f"Processed {filename}: {len(blobs)} items -> {output_path}")

# Example usage
if __name__ == "__main__":
    process_all_jsons("menus", "text_blobs")
