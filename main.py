"""
Voice Order AI - LangGraph + FastAPI Backend
Handles: price estimation, pickup orders, reservations
Deploy on Railway → connect via Make.com → VAPI calls it
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any
import json, random, string
from datetime import datetime

app = FastAPI(title="Voice Order Agent")

# ─────────────────────────────────────────────
# MENU — grouped by category
# Add items from the other tabs (Chef Signature,
# Soup, Rice, Naan/Bread, etc.) as you go.
# ─────────────────────────────────────────────

MENU_CATEGORIES: dict[str, dict[str, float]] = {
    "Appetizers": {
        "chicken samosa (2pc)":       5.00,
        "vegetable samosa (2pc)":     4.00,
        "dahi balla (3pc)":           8.00,
        "samosa chaat":               8.00,
        "pani puri (8pc)":           10.00,
        "chicken spring roll (2pc)":  5.00,
        "vegetable spring roll (6pc)":5.00,
        "vegetable pakora (per lb)":  9.00,
        "shami kabab (2pc)":          5.00,
        "papri chaat":                8.00,
        "fish pakora (per lb)":      16.00,
        "chicken momo (8pc steam)":  12.00,
        "veg momo (8pc steam)":      10.00,
        "paneer pakora (4pc)":        6.00,
    },

    # ── Paste items from each tab below ──────

    "Chef Signature": {
        # "dish name": price,
    },
    "Soup": {
        # "dish name": price,
    },
    "Rice": {
        # "dish name": price,
    },
    "Naan / Bread": {
        # "dish name": price,
    },
    "Breakfast": {
        # "dish name": price,
    },
    "Main Entree": {
        # "dish name": price,
    },
    "Seafood Entree": {
        # "dish name": price,
    },
    "Chinese Wok": {
        # "dish name": price,
    },
    "Vegetable Entree": {
        # "dish name": price,
    },
    "Snacks / Sides": {
        # "dish name": price,
    },
    "Tandoori Entree": {
        # "dish name": price,
    },
    "Platter": {
        # "dish name": price,
    },
}

# Flat lookup used by all tool handlers
MENU: dict[str, float] = {
    item: price
    for category in MENU_CATEGORIES.values()
    for item, price in category.items()
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def match_item(name: str) -> str | None:
    """Fuzzy match caller's item name to menu key."""
    name = name.lower().strip()
    for key in MENU:
        if key in name or name in key:
            return key
    # partial word match (e.g. "cheeseburgers" → "cheeseburger")
    for key in MENU:
        if any(word in key for word in name.split()):
            return key
    return None

def generate_id(prefix: str) -> str:
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{prefix}-{suffix}"


# ─────────────────────────────────────────────
# TOOL HANDLERS (LangGraph nodes as plain fns)
# ─────────────────────────────────────────────

def estimate_price(params: dict) -> dict:
    """
    Called when caller asks: 'how much would X and Y cost?'
    Params:
      items: [{ name: str, quantity: int }]
    """
    items = params.get("items", [])
    total = 0.0
    breakdown = []
    not_found = []

    for item in items:
        raw_name = item.get("name", "").strip()
        qty = int(item.get("quantity", 1))
        matched = match_item(raw_name)

        if matched:
            line_price = MENU[matched] * qty
            total += line_price
            breakdown.append(f"{qty}x {matched.title()} — ${line_price:.2f}")
        else:
            not_found.append(raw_name)

    msg = f"Your estimated total is ${total:.2f}."
    if breakdown:
        msg += " That includes " + ", ".join(breakdown) + "."
    if not_found:
        msg += f" Sorry, I couldn't find {', '.join(not_found)} on our menu. Can I help you with something else?"

    return {
        "estimated_value": round(total, 2),
        "breakdown": breakdown,
        "not_found": not_found,
        "message": msg,
    }


def place_order(params: dict) -> dict:
    """
    Called when caller confirms they want to place a pickup order.
    Params:
      items:          [{ name: str, quantity: int }]
      customer_name:  str
      phone:          str
      pickup_time:    str  (e.g. '20 minutes', '6:30 PM')
    """
    items          = params.get("items", [])
    customer_name  = params.get("customer_name", "Guest")
    phone          = params.get("phone", "not provided")
    pickup_time    = params.get("pickup_time", "as soon as possible")

    price_data = estimate_price({"items": items})
    total      = price_data["estimated_value"]
    order_id   = generate_id("ORD")

    # TODO: swap this with a real DB write (Supabase, Airtable, etc.)
    order = {
        "order_id":     order_id,
        "customer":     customer_name,
        "phone":        phone,
        "items":        items,
        "total":        total,
        "pickup_time":  pickup_time,
        "placed_at":    datetime.utcnow().isoformat(),
    }

    msg = (
        f"Perfect! Your order is confirmed, {customer_name}. "
        f"Order ID is {order_id}. "
        f"Total is ${total:.2f}. "
        f"Ready for pickup {pickup_time}. "
        f"We'll see you soon!"
    )

    return {**order, "message": msg}


def make_reservation(params: dict) -> dict:
    """
    Called when caller wants to book a table.
    Params:
      name:         str
      date:         str  (e.g. 'tomorrow', 'March 25th')
      time:         str  (e.g. '7 PM')
      party_size:   int
      phone:        str
      notes:        str  (optional special requests)
    """
    name        = params.get("name", "Guest")
    date        = params.get("date", "")
    time_       = params.get("time", "")
    party_size  = params.get("party_size", 2)
    phone       = params.get("phone", "not provided")
    notes       = params.get("notes", "")
    res_id      = generate_id("RES")

    # TODO: swap with a real calendar / booking system
    reservation = {
        "reservation_id": res_id,
        "name":           name,
        "date":           date,
        "time":           time_,
        "party_size":     party_size,
        "phone":          phone,
        "notes":          notes,
        "created_at":     datetime.utcnow().isoformat(),
    }

    msg = (
        f"Got it! Reservation confirmed for {name}, "
        f"party of {party_size} on {date} at {time_}. "
        f"Your reservation ID is {res_id}. "
        f"{'Special note: ' + notes + '. ' if notes else ''}"
        f"We look forward to seeing you!"
    )

    return {**reservation, "message": msg}


def get_menu_info(params: dict) -> dict:
    """Called when caller asks what's on the menu, a specific item, or a category."""
    item_query     = params.get("item", "").strip()
    category_query = params.get("category", "").strip().lower()

    # Category lookup — e.g. "what appetizers do you have?"
    if category_query:
        for cat_name, cat_items in MENU_CATEGORIES.items():
            if category_query in cat_name.lower() or cat_name.lower() in category_query:
                if not cat_items:
                    return {"message": f"I don't have the {cat_name} menu loaded yet. Let me find out for you."}
                items_str = ", ".join(
                    f"{k.title()} for ${v:.2f}" for k, v in cat_items.items()
                )
                return {
                    "category": cat_name,
                    "items":    cat_items,
                    "message":  f"Under {cat_name} we have: {items_str}. Anything sound good?",
                }

    # Specific item lookup
    if item_query:
        matched = match_item(item_query)
        if matched:
            cat_label = next(
                (cat for cat, items in MENU_CATEGORIES.items() if matched in items), ""
            )
            return {
                "item":     matched,
                "price":    MENU[matched],
                "category": cat_label,
                "message":  f"{matched.title()} is ${MENU[matched]:.2f}.",
            }
        else:
            return {
                "message": f"Sorry, I couldn't find {item_query} on our menu. Can I help you with something else?",
            }

    # Full menu — list categories only to keep spoken response short
    available_cats = [cat for cat, items in MENU_CATEGORIES.items() if items]
    cats_str = ", ".join(available_cats)
    return {
        "categories": available_cats,
        "message": (
            f"We have several sections: {cats_str}. "
            f"Which category would you like to hear more about, or is there a specific dish you're looking for?"
        ),
    }


# ─────────────────────────────────────────────
# TOOL ROUTER
# ─────────────────────────────────────────────

TOOL_MAP = {
    "estimate_price":   estimate_price,
    "place_order":      place_order,
    "make_reservation": make_reservation,
    "get_menu_info":    get_menu_info,
}


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

class InvokeRequest(BaseModel):
    tool_name:  str
    parameters: dict = {}

@app.post("/invoke")
async def invoke(req: InvokeRequest):
    """
    Called by Make.com after stripping the VAPI wrapper.
    Body: { "tool_name": "estimate_price", "parameters": { ... } }
    """
    handler = TOOL_MAP.get(req.tool_name)
    if not handler:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown tool: {req.tool_name}"},
        )
    result = handler(req.parameters)
    return result


@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """
    Direct VAPI server URL endpoint — skip Make.com if you want fewer hops.
    VAPI sends tool-call events here and expects the response format below.
    """
    body = await request.json()
    message = body.get("message", {})

    if message.get("type") != "tool-calls":
        return {"results": []}   # ignore non-tool events

    results = []
    for call in message.get("toolCallList", []):
        call_id   = call.get("id")
        fn        = call.get("function", {})
        tool_name = fn.get("name", "")
        try:
            raw_args  = fn.get("arguments", "{}")
            arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception:
            arguments = {}

        handler = TOOL_MAP.get(tool_name)
        if handler:
            result = handler(arguments)
            spoken = result.get("message", str(result))
        else:
            spoken = f"Sorry, I don't have a handler for {tool_name}."

        results.append({"toolCallId": call_id, "result": spoken})

    return {"results": results}


@app.get("/menu")
async def menu_endpoint():
    """Handy reference — returns your full menu as JSON."""
    return {"menu": MENU}


@app.get("/health")
async def health():
    return {"status": "ok", "tools": list(TOOL_MAP.keys())}
