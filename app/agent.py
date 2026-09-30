# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from typing import Optional, List, Dict, Any
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-04-f4db821212f0"


def _get_firestore_db():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def list_destinations(city: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List or search curated travel destinations and experiences from the catalog.

    Args:
        city: Optional city name filter (e.g., 'Kyoto', 'Rome', 'Banff', 'Paris', 'Reykjavik').
        category: Optional category filter (e.g., 'Culture & Nature', 'Food & Nightlife', 'Adventure & Nature').

    Returns:
        A list of destination dictionaries matching the criteria.
    """
    db = _get_firestore_db()
    docs = db.collection("travel_destinations").stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if city and city.lower() not in data.get("city", "").lower():
            continue
        if category and category.lower() not in data.get("category", "").lower():
            continue
        results.append(data)
    return results


def add_destination(
    name: str,
    city: str,
    country: str,
    category: str,
    description: str,
    estimated_cost_usd: float,
    recommended_duration_hours: float,
    vibe: str,
) -> Dict[str, Any]:
    """Add a new travel destination or spot into the catalog.

    Args:
        name: Name of the destination, activity, or venue.
        city: City where it is located.
        country: Country where it is located.
        category: Category (e.g., 'Adventure & Nature', 'Food & Nightlife', 'Art & Culture').
        description: Engaging description of the experience.
        estimated_cost_usd: Estimated cost per person in USD.
        recommended_duration_hours: Recommended time spent in hours.
        vibe: Descriptive vibe words (e.g., 'romantic, scenic, lively').

    Returns:
        A dictionary with the status and created destination record.
    """
    db = _get_firestore_db()
    doc_id = f"{city.lower()}-{name.lower().replace(' ', '-')[:25]}"
    record = {
        "id": doc_id,
        "name": name,
        "city": city,
        "country": country,
        "category": category,
        "description": description,
        "estimated_cost_usd": float(estimated_cost_usd),
        "recommended_duration_hours": float(recommended_duration_hours),
        "vibe": vibe,
        "tags": [t.strip().lower() for t in vibe.split(",") if t.strip()]
    }
    db.collection("travel_destinations").document(doc_id).set(record)
    return {"status": "success", "destination": record}


def calculate_trip_budget(
    destination_ids: List[str],
    num_days: int = 3,
    num_travelers: int = 1,
    accommodation_tier: str = "moderate",
) -> Dict[str, Any]:
    """Calculate an itemized trip budget breakdown based on selected activities and travel style.

    Args:
        destination_ids: List of destination IDs/slugs from the catalog (e.g. ['kyoto-arashiyama', 'banff-lake-louise']).
        num_days: Number of days for the trip (minimum 1).
        num_travelers: Number of people traveling (minimum 1).
        accommodation_tier: Accommodation tier: 'budget' (~$60/night), 'moderate' (~$150/night), or 'luxury' (~$350/night).

    Returns:
        A dictionary containing itemized costs (activities, lodging, daily meals/transit) and overall totals.
    """
    db = _get_firestore_db()
    activities_cost = 0.0
    matched_activities = []

    for doc_id in destination_ids:
        doc = db.collection("travel_destinations").document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            cost = float(data.get("estimated_cost_usd", 0.0))
            activities_cost += cost * num_travelers
            matched_activities.append({
                "id": doc_id,
                "name": data.get("name"),
                "city": data.get("city"),
                "cost_per_person_usd": cost,
                "subtotal_usd": cost * num_travelers,
            })

    tier_rates = {
        "budget": {"lodging_per_night": 60.0, "daily_food_transit_per_person": 35.0},
        "moderate": {"lodging_per_night": 150.0, "daily_food_transit_per_person": 75.0},
        "luxury": {"lodging_per_night": 350.0, "daily_food_transit_per_person": 180.0},
    }
    rates = tier_rates.get(accommodation_tier.lower(), tier_rates["moderate"])

    # Lodging assumes 1 room per 2 travelers (minimum 1 room)
    rooms_needed = max(1, (num_travelers + 1) // 2)
    total_lodging = rates["lodging_per_night"] * max(1, num_days) * rooms_needed
    total_food_transit = rates["daily_food_transit_per_person"] * max(1, num_days) * num_travelers
    grand_total = activities_cost + total_lodging + total_food_transit

    return {
        "summary": {
            "num_days": num_days,
            "num_travelers": num_travelers,
            "accommodation_tier": accommodation_tier.capitalize(),
            "grand_total_usd": round(grand_total, 2),
            "cost_per_person_usd": round(grand_total / max(1, num_travelers), 2),
            "cost_per_day_usd": round(grand_total / max(1, num_days), 2),
        },
        "breakdown": {
            "lodging_total_usd": round(total_lodging, 2),
            "food_and_transit_total_usd": round(total_food_transit, 2),
            "activities_total_usd": round(activities_cost, 2),
        },
        "activities_included": matched_activities,
    }


def get_currency_exchange_rates(
    base_currency: str = "USD",
    target_currencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch live real-world currency exchange rates for trip budgeting.

    Uses the free public ExchangeRate-API (from public-apis directory).
    If an optional EXCHANGE_RATE_API_KEY environment variable is set, it uses it;
    otherwise it seamlessly uses the open public endpoint.

    Args:
        base_currency: Base 3-letter currency code (e.g. 'USD', 'EUR', 'GBP').
        target_currencies: Optional list of target currencies to return (e.g. ['JPY', 'EUR', 'CAD']).

    Returns:
        A dictionary with base currency, last update date, and exchange rates.
    """
    import json
    import os
    import urllib.request

    base = base_currency.upper().strip()
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")

    if api_key:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    else:
        url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WanderWise-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return {"error": f"Failed to retrieve currency rates: {str(e)}", "base": base}

    rates = data.get("rates", {})
    if target_currencies:
        filtered_rates = {
            curr.upper().strip(): rates.get(curr.upper().strip())
            for curr in target_currencies
            if curr.upper().strip() in rates
        }
    else:
        # Default to popular travel currencies
        default_targets = ["EUR", "JPY", "GBP", "CAD", "AUD", "CHF", "ISK"]
        filtered_rates = {c: rates.get(c) for c in default_targets if c in rates}

    return {
        "base_currency": base,
        "last_updated_utc": data.get("time_last_update_utc"),
        "rates": filtered_rates,
    }


def geocode_address(address: str) -> Dict[str, Any]:
    """Convert a physical address or landmark name into geographic coordinates (lat/lng).

    Calls the Google Maps Geocoding API directly.

    Args:
        address: The address, city, or landmark name (e.g. 'Eiffel Tower, Paris', 'Shibuya Crossing, Tokyo').

    Returns:
        A dictionary containing the formatted address and location coordinates (lat, lng).
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WanderWise-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return {"error": f"Failed to call Geocoding API: {str(e)}"}

    if data.get("status") != "OK" or not data.get("results"):
        return {"error": f"No geocoding results found (status: {data.get('status')})"}

    result = data["results"][0]
    return {
        "formatted_address": result.get("formatted_address"),
        "location": result.get("geometry", {}).get("location", {}),
    }


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: float = 1500.0,
    max_results: int = 5,
) -> Dict[str, Any]:
    """Find nearby places or attractions of a given type around coordinates.

    Calls Google Maps Places API (New) searchNearby REST endpoint directly.

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Type of place to search for (e.g., 'tourist_attraction', 'restaurant', 'museum', 'lodging', 'cafe', 'park').
        radius_meters: Search radius in meters (default 1500 meters, max 50000).
        max_results: Maximum number of places to return (default 5, max 20).

    Returns:
        A dictionary containing a list of places with name, formatted address, and location.
    """
    import json
    import os
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": min(max(1, max_results), 20),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return {"error": f"Failed to call Places API (New): {str(e)}"}

    places = []
    for item in data.get("places", []):
        places.append({
            "name": item.get("displayName", {}).get("text", "Unknown"),
            "address": item.get("formattedAddress"),
            "location": item.get("location"),
        })

    return {"places": places, "count": len(places)}


from google.adk.tools import ToolContext
from google.cloud import storage
import uuid

IMAGE_STORAGE_BUCKET = "wanderwise-assets-qwiklabs-gcp-04-f4db821212f0-k5w97d"
IMAGE_PROJECT_ID = "qwiklabs-gcp-04-f4db821212f0"


async def generate_destination_image(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate a scenic travel postcard, landscape, or activity visual for a destination.

    Uses the gemini-3.1-flash-lite-image model in the global region.
    Saves the image as an ADK session artifact (visible in Playground) and uploads the bytes
    to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: Detailed description of the travel scene or destination to visualize (e.g. 'A breathtaking aerial postcard of Lake Louise with turquoise water and snow-capped Rocky Mountains in Banff').

    Returns:
        A dictionary with the public image URL, artifact filename, and status.
    """
    from google import genai

    # Generate image using gemini-3.1-flash-lite-image in global region
    client = genai.Client(
        vertexai=True,
        project=IMAGE_PROJECT_ID,
        location="global",
    )

    image_prompt = f"Travel photography postcard: {prompt}. Beautiful lighting, vivid detail, professional quality."
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=image_prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Failed to generate image from model.", "prompt": prompt}

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    extension = "jpg" if "jpeg" in mime_type else "png"
    artifact_filename = f"destination_{uuid.uuid4().hex[:8]}.{extension}"
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

    # 2. Upload same image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=IMAGE_PROJECT_ID)
    bucket = storage_client.bucket(IMAGE_STORAGE_BUCKET)
    blob = bucket.blob(artifact_filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{IMAGE_STORAGE_BUCKET}/{artifact_filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": artifact_filename,
        "prompt": prompt,
    }


async def generate_destination_video(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate a short video clip for a destination or travel scene.

    Uses Google's Omni model (gemini-omni-flash-preview) in the global region.
    Saves the video as an ADK session artifact (visible in Playground) and uploads the bytes
    to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: Description of the short travel video clip to generate (e.g. 'A scenic aerial video of waves crashing on a tropical beach in Maui at sunset').

    Returns:
        A dictionary with the public video URL, artifact filename, and status.
    """
    import asyncio
    import base64
    from google import genai

    client = genai.Client(
        vertexai=True,
        project=IMAGE_PROJECT_ID,
        location="global",
    )

    video_prompt = f"Cinematic travel video: {prompt}. High resolution, smooth motion, professional travel footage."

    # Create interaction in background for gemini-omni-flash-preview
    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=video_prompt,
        background=True,
    )

    interaction_id = getattr(interaction, "id", None)
    if not interaction_id:
        return {"error": "Failed to initiate video generation.", "prompt": prompt}

    # Poll interaction until completed
    max_attempts = 36  # up to 3 minutes
    res = interaction
    for _ in range(max_attempts):
        if getattr(res, "status", None) not in ("in_progress", "pending"):
            break
        await asyncio.sleep(5)
        res = client.interactions.get(id=interaction_id)

    output_video = getattr(res, "output_video", None)
    video_bytes = None
    mime_type = "video/mp4"

    if output_video:
        data = getattr(output_video, "data", None)
        if isinstance(output_video, dict):
            data = output_video.get("data")
            mime_type = output_video.get("mime_type") or "video/mp4"
        elif hasattr(output_video, "mime_type") and output_video.mime_type:
            mime_type = output_video.mime_type

        if data:
            if isinstance(data, str):
                video_bytes = base64.b64decode(data)
            elif isinstance(data, bytes):
                video_bytes = data

    if not video_bytes:
        return {
            "error": "Video generation did not return video bytes or timed out.",
            "prompt": prompt,
            "status": getattr(res, "status", "unknown"),
        }

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    artifact_filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

    # 2. Upload same video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=IMAGE_PROJECT_ID)
    bucket = storage_client.bucket(IMAGE_STORAGE_BUCKET)
    blob = bucket.blob(artifact_filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{IMAGE_STORAGE_BUCKET}/{artifact_filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": artifact_filename,
        "prompt": prompt,
    }


from google.adk.code_executors import AgentEngineSandboxCodeExecutor

SANDBOX_RESOURCE_NAME = (
    "projects/125288171693/locations/us-east1/reasoningEngines/6200504509819518976/sandboxEnvironments/1979833413531598848"
)

sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME
)

from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext

MEMORY_BANK_ID = "6200504509819518976"
MEMORY_PROJECT_ID = "qwiklabs-gcp-04-f4db821212f0"
MEMORY_LOCATION = "us-east1"


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: After each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are WanderWise, an enthusiastic and expert travel concierge and itinerary planner. "
        "You remember the user's travel preferences, dietary restrictions, medical and food allergies, "
        "and facts across conversations from your Memory Bank and use them to personalize your recommendations. "
        "Crucially: Always pay attention to and remember all user allergies (e.g. peanuts, gluten, shellfish, lactose, bee stings, medication). "
        "Never recommend foods, restaurants, or experiences containing known allergens for the user. "
        "You have access to a curated catalog of travel destinations and activities stored in Firestore. "
        "When users ask about trip ideas, itineraries, or recommendations, query the destinations catalog "
        "using `list_destinations`. You can register newly discovered travel spots using `add_destination`. "
        "When users ask for budget estimates, cost breakdowns, or trip calculations, use `calculate_trip_budget`. "
        "When users ask about currency exchange rates or converting costs to local money, use `get_currency_exchange_rates`. "
        "When users need to find coordinates for an address or landmark, use `geocode_address`. "
        "When users want to discover nearby attractions, restaurants, museums, or cafes around an area, "
        "first geocode the area with `geocode_address` if needed, then call `find_nearby_places`. "
        "When users want a visual preview, photo, scenic view, or travel postcard of a destination or activity, "
        "call `generate_destination_image` to generate it and upload to Cloud Storage. "
        "When users want a short video clip or cinematic preview of a destination or scene, "
        "call `generate_destination_video` to generate it with Google Omni model and upload to Cloud Storage. "
        "When users ask complex mathematical, statistical, or data-analysis questions (e.g. route optimizations, exact date math, customized budget modeling), "
        "you can safely write Python code in ```python ... ``` blocks which will execute in your secure Agent Engine Sandbox. "
        "You can also check local time/weather using the respective tools."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_code_executor,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        add_destination,
        calculate_trip_budget,
        get_currency_exchange_rates,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)





