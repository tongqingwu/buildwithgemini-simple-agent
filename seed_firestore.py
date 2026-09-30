#!/usr/bin/env python3
"""Seed script for WanderWise travel destinations and itinerary items in Firestore."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-f4db821212f0"

SEED_DESTINATIONS = [
    {
        "id": "kyoto-arashiyama",
        "name": "Arashiyama Bamboo Grove & Tenryu-ji",
        "city": "Kyoto",
        "country": "Japan",
        "category": "Culture & Nature",
        "description": "Walk among towering bamboo stalks followed by zen garden meditation at a UNESCO World Heritage temple.",
        "estimated_cost_usd": 15,
        "recommended_duration_hours": 3.5,
        "vibe": "tranquil, nature, photography",
        "tags": ["bamboo", "temple", "garden", "unesco", "nature"]
    },
    {
        "id": "rome-trastevere-food",
        "name": "Trastevere Evening Culinary Exploration",
        "city": "Rome",
        "country": "Italy",
        "category": "Food & Nightlife",
        "description": "Artisanal pasta, suppli, crisp Roman pizza, and natural wines in cobblestone alleyways.",
        "estimated_cost_usd": 65,
        "recommended_duration_hours": 4.0,
        "vibe": "lively, historic, foodie",
        "tags": ["food", "wine", "nightlife", "pasta", "historic"]
    },
    {
        "id": "banff-lake-louise",
        "name": "Lake Louise & Plain of Six Glaciers Trail",
        "city": "Banff",
        "country": "Canada",
        "category": "Adventure & Nature",
        "description": "Turquoise glacial lake hike ending with afternoon tea at a historic alpine teahouse.",
        "estimated_cost_usd": 25,
        "recommended_duration_hours": 6.0,
        "vibe": "adventurous, breathtaking, alpine",
        "tags": ["hiking", "lake", "glacier", "mountains", "tea"]
    },
    {
        "id": "paris-montmartre-art",
        "name": "Montmartre Bohemian Art & Vineyard Walk",
        "city": "Paris",
        "country": "France",
        "category": "Art & Architecture",
        "description": "Explore vintage artist ateliers, the Place du Tertre, the Clos Montmartre vineyard, and Sacré-Cœur vistas.",
        "estimated_cost_usd": 20,
        "recommended_duration_hours": 3.0,
        "vibe": "romantic, artistic, scenic",
        "tags": ["art", "architecture", "views", "cafes", "bohemian"]
    },
    {
        "id": "reykjavik-golden-circle",
        "name": "Golden Circle & Secret Lagoon Thermal Bath",
        "city": "Reykjavik",
        "country": "Iceland",
        "category": "Nature & Wellness",
        "description": "Witness erupting geysers, Gullfoss waterfall, and relax in Iceland's oldest natural thermal bath.",
        "estimated_cost_usd": 95,
        "recommended_duration_hours": 7.0,
        "vibe": "geothermal, dramatic, rejuvenating",
        "tags": ["geyser", "waterfall", "hot springs", "scenic drive", "wellness"]
    }
]

def seed():
    print(f"Connecting to Firestore using project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("travel_destinations")

    for item in SEED_DESTINATIONS:
        doc_id = item["id"]
        collection.document(doc_id).set(item)
        print(f"  ✓ Seeded destination: {item['name']} ({item['city']}, {item['country']})")

    print("\n✅ Seeding complete! Total destinations added:", len(SEED_DESTINATIONS))

if __name__ == "__main__":
    seed()
