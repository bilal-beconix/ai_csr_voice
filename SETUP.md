# Voice Order AI — Setup Guide
## Get live in ~45 minutes

---

## What you're building
Phone calls → VAPI (speech-to-text) → Make.com (webhook router) → Your FastAPI/LangGraph backend → response spoken back to caller.

---

## STEP 1 — Deploy the backend to Railway (10 min)

1. Go to **railway.app** → sign up / log in
2. Click **New Project → Deploy from GitHub**
3. Push these files to a new GitHub repo:
   - `main.py`
   - `requirements.txt`
   - `Procfile`
4. Railway auto-detects Python and deploys
5. Once deployed, copy your public URL — looks like:
   `https://your-app-name.up.railway.app`

**Test it:**
```
GET https://your-app-name.up.railway.app/health
```
Should return: `{ "status": "ok", "tools": ["estimate_price", "place_order", ...] }`

**Test estimate_price:**
```
POST https://your-app-name.up.railway.app/invoke
Content-Type: application/json

{
  "tool_name": "estimate_price",
  "parameters": {
    "items": [
      { "name": "burger", "quantity": 2 },
      { "name": "fries", "quantity": 1 }
    ]
  }
}
```
Expected: `{ "estimated_value": 30.97, "message": "Your estimated total is $30.97..." }`

---

## STEP 2 — Set up Make.com scenario (15 min)

### Create the webhook scenario:

**Module 1: Webhooks → Custom webhook**
- Click "Add" → give it a name like "VAPI Order Webhook"
- Copy the webhook URL — you'll paste it into VAPI
- Click "Determine data structure" → trigger a test call from VAPI later to auto-map the fields

**Module 2: Tools → Set variable** (extract tool data)
- Tool name: `{{1.message.toolCallList[].function.name}}`
- Tool args: `{{1.message.toolCallList[].function.arguments}}`
- Tool call ID: `{{1.message.toolCallList[].id}}`

**Module 3: HTTP → Make a request**
- URL: `https://your-app-name.up.railway.app/invoke`
- Method: POST
- Headers: `Content-Type: application/json`
- Body (Raw / JSON):
```json
{
  "tool_name": "{{2.tool_name}}",
  "parameters": {{parseJSON(2.tool_args)}}
}
```

**Module 4: Webhooks → Webhook response**
- Status: 200
- Body:
```json
{
  "results": [
    {
      "toolCallId": "{{2.tool_call_id}}",
      "result": "{{3.message}}"
    }
  ]
}
```

**Save & activate the scenario.**

---

## STEP 3 — Set up VAPI (15 min)

1. Go to **vapi.ai** → Dashboard → **Assistants → New Assistant**
2. Open `vapi-config.json` — copy the `systemPrompt` text into the System Prompt field
3. Paste your **Make.com webhook URL** into the **Server URL** field
4. Go to **Tools tab** → add 4 tools by copying each function block from `vapi-config.json`:
   - `estimate_price`
   - `place_order`
   - `make_reservation`
   - `get_menu_info`
5. Set voice (11labs Rachel works well for restaurants)
6. Set model to **GPT-4o**

**Test with VAPI's built-in call simulator:**
- Click "Test Assistant"
- Say: *"Hi, how much would 2 burgers and a coke cost?"*
- You should hear the estimated total spoken back

---

## STEP 4 — Customize your menu

Edit the `MENU` dict at the top of `main.py`:
```python
MENU: dict[str, float] = {
    "your item":  9.99,
    "another item": 12.99,
    # ...
}
```
Push to GitHub → Railway auto-redeploys in ~60 seconds.

---

## Common issues

| Symptom | Fix |
|---|---|
| Make.com returns empty result | Check that `parseJSON(2.tool_args)` is parsing correctly — VAPI sends arguments as a JSON string |
| Tool never fires | Make sure the tool names in VAPI exactly match the function names in main.py |
| Railway deploy fails | Check that `Procfile` has no extra spaces and Python version is 3.11+ |
| Voice sounds robotic | Switch to 11labs in VAPI voice settings |

---

## Next upgrades (after it's live)

- **Save orders to Airtable/Supabase** — add a webhook call inside `place_order()` in main.py
- **Send SMS confirmation** — add Twilio to Make.com after the webhook response module
- **Real-time order dashboard** — build a simple HTML page that polls `/orders` endpoint
- **Multi-location support** — add a `location` parameter and route to different menus
