import os
import requests

images = {
    "plastic_bottles.jpg": "https://images.unsplash.com/photo-1605600659908-0ef719419d41?q=80&w=600&auto=format&fit=crop",
    "cardboard_boxes.jpg": "https://images.unsplash.com/photo-1587320028124-7850a58a9840?q=80&w=600&auto=format&fit=crop",
    "electronic_waste.jpg": "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?q=80&w=600&auto=format&fit=crop"
}

os.makedirs("test_images", exist_ok=True)

for name, url in images.items():
    print(f"Downloading {name}...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join("test_images", name), "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded {name}")
    else:
        print(f"Failed to download {name}")
