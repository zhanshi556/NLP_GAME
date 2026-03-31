import os
import json
import httpx
import re
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ✅ 正确的 DeepSeek API 地址
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 12星座庇护所设定 (12 Zodiac Shelters)
shelters = {
    "Aries": {"type": "Cave", "resources": {"food":5,"water":3,"tools":2}, "ability": "Defense +10", "apocalypse": "Massive Flooding - Rising waters and flash floods have submerged the world. Water levels keep rising, threatening all low-lying areas."},
    "Taurus": {"type": "Farmhouse", "resources": {"food":7,"water":5,"tools":2}, "ability": "Food Production +1", "apocalypse": "Acid Rain - Toxic precipitation falls from the sky, corroding everything it touches. Find shelter quickly or face chemical burns."},
    "Gemini": {"type": "Mobile RV", "resources": {"food":4,"water":4,"tools":3}, "ability": "Randomly dodge a danger once", "apocalypse": "Zombie Outbreak - The dead have risen and roam the wasteland hunting the living. Stay alert and avoid hordes."},
    "Cancer": {"type": "Seaside Cabin", "resources": {"food":5,"water":7,"tools":1}, "ability": "Seafood catch chance +30%", "apocalypse": "Extreme Heat - Record-breaking temperatures turn the world into an inferno. Dehydration is a constant threat."},
    "Leo": {"type": "Mountain Fortress", "resources": {"food":4,"water":4,"tools":3}, "ability": "See future event hints", "apocalypse": "Extreme Drought - All water sources have vanished. The land is barren and crops cannot grow. Thirst rules survival."},
    "Virgo": {"type": "Underground Bunker", "resources": {"food":5,"water":5,"tools":3}, "ability": "Repair speed +50%", "apocalypse": "Solar Collapse - The Sun's radiation has intensified, scorching the surface. Only underground is safe from cosmic rays."},
    "Libra": {"type": "Treehouse", "resources": {"food":6,"water":5,"tools":2}, "ability": "Resource explore chance +20%", "apocalypse": "Alien Invasion - Extraterrestrial forces have arrived and are harvesting Earth's resources. Avoid detection at all costs."},
    "Scorpio": {"type": "Cave Lab", "resources": {"food":4,"water":4,"tools":4}, "ability": "Tech item explore chance +40%", "apocalypse": "Dinosaur Revival - Prehistoric creatures have been cloned and released into the world. Ancient predators now roam freely."},
    "Sagittarius": {"type": "Desert Tent", "resources": {"food":3,"water":6,"tools":3}, "ability": "Desert event trigger chance reduced", "apocalypse": "Cockroach Plague - Mutant insects have overrun civilization. Billions of them swarm everywhere, consuming everything."},
    "Capricorn": {"type": "Valley Stone House", "resources": {"food":5,"water":5,"tools":2}, "ability": "Shelter durability +20%", "apocalypse": "New Ice Age - Temperatures have plummeted and glaciers spread. Eternal winter has frozen the world."},
    "Aquarius": {"type": "Sky Pod", "resources": {"food":3,"water":4,"tools":4}, "ability": "One extra explore action", "apocalypse": "Mega Tsunami - Colossal waves triggered by underwater earthquakes have devastated coastal areas. Massive flooding everywhere."},
    "Pisces": {"type": "River Boat", "resources": {"food":4,"water":6,"tools":2}, "ability": "Water travel, dodge one land danger event", "apocalypse": "Biological Disaster - A genetically engineered virus has mutated the world's population. The infected are everywhere and hostile."}
}

async def async_deepseek_call(system_prompt, user_prompt):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7
                }
            )
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return content.strip()
    except Exception as e:
        print("DeepSeek API Error:", e)
        return None

async def _summarize_history(history):
    sys_prompt = "You are a specialized summarizer for a post-apocalyptic text game."
    history_lines = [f"- Action: {h.get('action')}\n  Result: {h.get('result')}" for h in history]
    history_text = "\n".join(history_lines)
    user_prompt = f"Summarize the following 5 turns of gameplay into ONE concise, fluent English sentence capturing the main events and outcomes.\n\n{history_text}"
    res = await async_deepseek_call(sys_prompt, user_prompt)
    return res if res else "The survivor continued exploring the wasteland."

async def _compress_long_term(long_term_memory):
    sys_prompt = "You are an epic story writer capturing macro-level game summaries."
    ltm_text = "\n".join([f"- {m}" for m in long_term_memory])
    user_prompt = f"Condense the following {len(long_term_memory)} summary sentences of gameplay into EXACTLY 3 overarching epic chapters (strings). Ensure it flows like a story. Output ONLY a valid JSON array of 3 strings.\n\n{ltm_text}\n\nExample Output:\n[\"Chapter 1: The Awakening in the Ruins...\", \"Chapter 2: ...\", \"Chapter 3: ...\"]"
    res = await async_deepseek_call(sys_prompt, user_prompt)
    try:
        chapters = json.loads(res)
        if isinstance(chapters, list) and len(chapters) > 0:
            return chapters
    except:
        pass
    return ["A significant chapter of survival passed, filled with unknown struggles and triumphs."]

async def generate_event(player_state, action):
    star_sign = player_state.get("starSign")
    shelter = shelters.get(star_sign, {})

    # Extract memory architecture states
    action_count = player_state.pop("actionCount", 0)
    history = player_state.pop("history", [])
    long_term_memory = player_state.pop("longTermMemory", [])
    epic_memory = player_state.pop("epicMemory", [])

    # Build Hierarchical Context
    background_lore = ""
    lore_parts = []
    if epic_memory:
        lore_parts.append("[Epic Chapters]\n" + "\n".join(f"- {e}" for e in epic_memory))
    if long_term_memory:
        lore_parts.append("[Recent Long-Term Memory]\n" + "\n".join(f"- {m}" for m in long_term_memory))
    if lore_parts:
        background_lore = "\n\n".join(lore_parts)
    else:
        background_lore = "The journey has just begun."

    short_term_text = "No immediate past actions."
    if history:
        # 只取最近的3回合作为眼前场景的焦点，忽略稍微远一点的动作防止场景穿越
        recent_3 = history[-3:] if len(history) >= 3 else history
        short_term_text = "\n".join([f"- Past action: {h.get('action')}\n  Result: {h.get('result')}" for h in recent_3])

    # Construct Prompt
    prompt = f"""
You are an AI Game Master for a text-based post-apocalyptic survival game.

=== APOCALYPSE SETTING ===
{shelter.get("apocalypse", "Unknown apocalyptic scenario")}

=== BACKGROUND LORE (Passive Knowledge) ===
{background_lore}
*Rule: Use this ONLY for world consistency. DO NOT forcefully mention these past events in the current scene unless explicitly relevant.*

=== IMMEDIATE SCENE (What just happened in the current location) ===
{short_term_text}

=== PLAYER STATUS ===
{json.dumps(player_state, ensure_ascii=False, indent=2)}
Shelter Type: {shelter.get("type")} ({shelter.get("ability")})

=== CURRENT ACTION ===
Player Action: "{action}"

INSTRUCTION:
Focus 90% of your attention on resolving the "Current Action" logically based on the "IMMEDIATE SCENE" and the apocalypse setting. The events should vividly reflect the unique apocalypse theme for this zodiac sign. Do not repeat the history. Output strictly in JSON format.

Requirements:
1. eventText: Event description (make it vivid, immersive, and logically continued in English)
2. newItems: Array of items found (each item has: name, food, water, health, repair). Items go to player inventory. Only include items if the player actually found something useful. Set values to 0 if the item doesn't provide that benefit. Repair Kits (repair > 0) should be rare - only about 20% chance to find one during exploration.
3. resourceChanges: Changes in tools only (food/water come from items now)
4. stateChanges: Changes in health (only from combat/damage, NOT from finding items)
5. nextActions: 3 possible next actions for the player to choose from (always include "Rest" as one option)

Example Format:
{{
  "eventText": "You search through the abandoned supermarket. Among the debris, you find some canned goods and a water bottle...",
  "newItems": [
    {{"name": "Canned Beans", "food": 3, "water": 0, "health": 0, "repair": 0}},
    {{"name": "Water Bottle", "food": 0, "water": 2, "health": 0, "repair": 0}},
    {{"name": "First Aid Kit", "food": 0, "water": 0, "health": 15, "repair": 0}},
    {{"name": "Repair Kit", "food": 0, "water": 0, "health": 0, "repair": 30}}
  ],
  "resourceChanges": {{ "tools": -1 }},
  "stateChanges": {{ "health": -10 }},
  "nextActions": ["Continue searching", "Return to shelter", "Rest"]
}}
"""

    # Prepare concurrent tasks
    sys_prompt = "You are a post-apocalyptic survival text game AI."
    main_task = async_deepseek_call(sys_prompt, prompt)

    # 此时如果 action_count % 5 == 0，意味着这是第 5、10、15... 次动作的“结果”之后。 
    # 但是前端传上来的 history 里只有前 4 次的完整记录（含前端尚未知道的本次动作，但当时还没生成结果）。
    # 要做彻底的 5 轮总结，最好是等主剧情结果出来，加进去再拼成 5 轮。 
    # 因此，我们先 run main_task，拿到本次的结果，再结合之前的凑成真正的 5 轮历史去总结。

    # Run main task first to get the outcome of the 5th action
    main_res = await main_task

    # Process main response
    try:
        if not main_res: raise Exception("Null response from AI")
        event_data = json.loads(main_res)
    except Exception as e:
        print("Json Parse Error in main generation:", e)
        event_data = {
            "eventText": "Communication lost... You can't reach the outside world temporarily, but you can still act.",
            "newItems": [],
            "resourceChanges": {},
            "stateChanges": {},
            "nextActions": ["Continue exploring", "Search for supplies", "Rest"]
        }

    # Ensure newItems field exists
    if "newItems" not in event_data:
        event_data["newItems"] = []

    # Now that we have the 5th action's result (event_data["eventText"]), we can form the perfect 5-turn memory!
    summary_task = None
    compress_task = None
    memory_updates = {}

    # triggers every 5 actions
    if action_count > 0 and action_count % 5 == 0:
        # Create a temporary copy of history and append the JUST generated 5th event
        # (This guarantees it summarizes EXACTLY rounds 1 to 5 instead of missing the current one)
        temp_history_for_summary = history[-4:] if len(history) >= 4 else history.copy()
        temp_history_for_summary.append({
            "action": action,
            "result": event_data.get("eventText", "")
        })
        summary_res = await _summarize_history(temp_history_for_summary)
        memory_updates["newSummary"] = summary_res

    # triggers when exactly hitting the 10-item limit (after getting a new summary, but evaluating existing LTM)
    if len(long_term_memory) >= 10:
        compress_res = await _compress_long_term(long_term_memory)
        memory_updates["newEpicChapters"] = compress_res
        
    event_data["_memoryUpdates"] = memory_updates
    return event_data


def extract_entities_from_event(event_text: str, nlu_model=None):
    """
    从事件文本中提取新实体（NPC、地点、物品）
    并添加到 NLU 动态库
    
    Args:
        event_text: AI生成的事件文本
        nlu_model: NLU模型实例
    
    Examples:
        "You find Sarah, a trader from New Denver..."
        → NPC: Sarah, LOCATION: New Denver
    """
    if not nlu_model:
        return
    
    # 提取 NPC 名字（大写开头的单词）
    npc_pattern = r'\b([A-Z][a-z]+)\b'
    npc_matches = re.findall(npc_pattern, event_text)
    for npc in npc_matches:
        # 过滤常见非实体词（I, You, The等）
        if npc not in ["You", "The", "A", "An", "In", "From", "To", "At", "On"]:
            nlu_model.add_entity("NPC", npc)
    
    # 提取地点（包含关键词：city, base, zone, area, settlement等）
    location_keywords = ["city", "base", "zone", "area", "settlement", "town", "village", "outpost", "camp", "haven"]
    for keyword in location_keywords:
        # 查找 "XXX [location_keyword]" 模式
        pattern = rf'([A-Z][a-z]+)\s+{keyword}'
        matches = re.findall(pattern, event_text, re.IGNORECASE)
        for location in matches:
            nlu_model.add_entity("LOCATION", f"{location} {keyword}")
    
    # 提取物品（包含关键词：weapon, tool, supplies等）
    item_keywords = ["weapon", "tool", "supplies", "medicine", "weapon", "gadget", "device", "equipment"]
    for keyword in item_keywords:
        pattern = rf'([a-z\s]+?)\s+{keyword}'
        matches = re.findall(pattern, event_text, re.IGNORECASE)
        for item in matches:
            item_clean = item.strip()
            if len(item_clean) > 0 and len(item_clean) < 30:  # 合理长度
                nlu_model.add_entity("ITEM", f"{item_clean} {keyword}")