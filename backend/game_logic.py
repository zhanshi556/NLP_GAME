import os
import json
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ✅ 正确的 DeepSeek API 地址
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 12星座庇护所设定
shelters = {
    "白羊座": {"type": "山洞", "resources": {"food":5,"water":3,"tools":2}, "ability": "防御力+10"},
    "金牛座": {"type": "农场小屋", "resources": {"food":7,"water":5,"tools":2}, "ability": "食物产出+1"},
    "双子座": {"type": "移动避难车", "resources": {"food":4,"water":4,"tools":3}, "ability": "随机避开一次危险事件"},
    "巨蟹座": {"type": "海边木屋", "resources": {"food":5,"water":7,"tools":1}, "ability": "捕获海产品概率+30%"},
    "狮子座": {"type": "山顶堡垒", "resources": {"food":4,"water":4,"tools":3}, "ability": "先看到未来事件提示"},
    "处女座": {"type": "地下避难室", "resources": {"food":5,"water":5,"tools":3}, "ability": "修复速度+50%"},
    "天秤座": {"type": "林间树屋", "resources": {"food":6,"water":5,"tools":2}, "ability": "探索资源概率+20%"},
    "天蝎座": {"type": "洞穴实验室", "resources": {"food":4,"water":4,"tools":4}, "ability": "探索科技物品概率+40%"},
    "射手座": {"type": "沙漠帐篷", "resources": {"food":3,"water":6,"tools":3}, "ability": "沙漠事件触发概率降低"},
    "摩羯座": {"type": "山谷石屋", "resources": {"food":5,"water":5,"tools":2}, "ability": "庇护所耐久+20%"},
    "水瓶座": {"type": "空中吊舱", "resources": {"food":3,"water":4,"tools":4}, "ability": "探索额外行动一次"},
    "双鱼座": {"type": "河边小舟", "resources": {"food":4,"water":6,"tools":2}, "ability": "水路自由，可逃避一次陆地危险事件"}
}

async def generate_event(player_state, action):
    star_sign = player_state.get("starSign")
    shelter = shelters.get(star_sign, {})

    # 构造 Prompt
    prompt = f"""
你是一款末日生存文字游戏 AI。

玩家当前状态：
{json.dumps(player_state, ensure_ascii=False, indent=2)}

庇护所类型：{shelter.get("type")}
庇护所特殊能力：{shelter.get("ability")}

玩家选择动作：{action}

请生成下一步事件，并严格输出 JSON 格式：

要求：
1. eventText: 事件描述（生动一点）
2. resourceChanges: 资源变化（food, water, tools）
3. stateChanges: 状态变化（health）
4. nextActions: 3个可选行动

示例格式：
{{
  "eventText": "你在废墟中找到一些罐头，但遭遇野兽袭击。",
  "resourceChanges": {{ "food": 2, "water": 0, "tools": -1 }},
  "stateChanges": {{ "health": -10 }},
  "nextActions": ["逃跑", "反击", "躲藏"]
}}
"""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一个末日生存文字游戏AI"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            )

            result = response.json()

            # 获取 AI 返回内容
            content = result["choices"][0]["message"]["content"]

            # 尝试解析 JSON
            try:
                return json.loads(content)
            except:
                # fallback（AI没按JSON输出）
                return {
                    "eventText": content,
                    "resourceChanges": {},
                    "stateChanges": {},
                    "nextActions": ["继续探索","修理庇护所","休息"]
                }

    except Exception as e:
        # 🚑 防止游戏直接崩溃
        print("DeepSeek调用失败:", e)
        return {
            "eventText": "通讯中断……你暂时无法获取外界信息，但仍然可以行动。",
            "resourceChanges": {},
            "stateChanges": {},
            "nextActions": ["继续探索","修理庇护所","休息"]
        }