from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 兼容两种启动方式：
# 1) 项目根目录: uvicorn backend.main:app --reload
# 2) backend 目录: uvicorn main:app --reload
try:
    from .game_logic import generate_event, extract_entities_from_event
    from .nlu.model import NLUModel
except ImportError:
    from game_logic import generate_event, extract_entities_from_event
    from nlu.model import NLUModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 NLU 模型
print("=" * 60)
print("初始化 NLU 模块...")
try:
    nlu_model = NLUModel()
    nlu_enabled = True
    print("✅ NLU 模块已启用（LLM 版本 - DeepSeek API）")
except Exception as e:
    print(f"❌ NLU 模块加载失败: {e}")
    print("⚠️  不使用 NLU，游戏将按预设动作模式运行")
    nlu_enabled = False
print("=" * 60)

# 预设动作列表
PRESET_ACTIONS = ["探索废墟", "寻找水源", "狩猎食物", "修理庇护所", "休息", "逃离", "逃离移动"]

# NLU 置信度阈值设置
NLU_CONFIDENCE_THRESHOLD = 0.55  # 低于此阈值时触发回退机制（从 0.6 改为 0.55）
NLU_HIGH_CONFIDENCE_THRESHOLD = 0.85  # 高置信度标记

class PlayRequest(BaseModel):
    playerState: dict
    action: str

@app.post("/api/play")
async def play(request: PlayRequest):
    """
    游戏事件生成接口
    
    支持两种模式：
    1. 预设动作：直接使用提供的动作
    2. 自然语言：使用 NLU 模块理解并转换为标准动作
        低置信度处理：
    - 置信度 >= 0.85：高置信度，直接使用预测
    - 置信度 0.6-0.85：中置信度，使用预测但标记为"可能理解"
    - 置信度 < 0.6：低置信度，拒绝本次输入并提示玩家重新表述
    
    同时支持动态实体提取：
    - 从用户输入中提取实体（包括被拒的低置信输入）
    - 从 AI 生成的事件中提取新实体
    - 动态补充到 NLU 实体库
    """
    action = request.action
    nlu_info = {}
    
    # NLU 处理逻辑
    if nlu_enabled and action not in PRESET_ACTIONS:
        try:
            # 使用 NLU 模型预测意图 + 提取实体
            nlu_result = nlu_model.predict(action)
            original_action = action
            confidence = nlu_result["confidence"]
            entities = nlu_result.get("entities", {})
            
            # 低置信度处理 - 直接拒绝，不执行动作
            if confidence < NLU_CONFIDENCE_THRESHOLD:
                print(f"❌ 低置信度输入被拒绝 ({confidence:.2f} < {NLU_CONFIDENCE_THRESHOLD}): '{original_action}'")
                nlu_info = {
                    "nlu_enabled": True,
                    "original_input": original_action,
                    "predicted_intent": nlu_result["intent"],
                    "predicted_action": nlu_result["action"],
                    "confidence": confidence,
                    "rejected": True,
                    "rejection_reason": f"置信度过低 ({confidence:.2f} < {NLU_CONFIDENCE_THRESHOLD})",
                    "entities": entities
                }
                
                # 返回拒绝响应，不执行游戏事件
                return {
                    "error": True,
                    "type": "low_confidence",
                    "message": "❌ 输入不够清楚，请重新表述。",
                    "hint": f"你说的 \"{original_action}\" 我没有完全理解（置信度仅 {confidence*100:.0f}%）。",
                    "suggestion": "请用以下动作之一重新选择：探索废墟、寻找水源、狩猎食物、修理庇护所、休息、逃离",
                    "nlu_info": nlu_info,
                    "playerState": request.playerState  # 保持玩家状态不变
                }
            else:
                # 中等或高置信度 - 继续处理
                action = nlu_result["action"]
                confidence_level = "高" if confidence >= NLU_HIGH_CONFIDENCE_THRESHOLD else "中"
                print(f"🧠 NLU 转换: '{original_action}' → '{action}' (置信度: {confidence:.2f} [{confidence_level}])")
                if entities and any(entities.values()):
                    print(f"📍 提取实体: {entities}")
                
                nlu_info = {
                    "nlu_enabled": True,
                    "original_input": original_action,
                    "predicted_intent": nlu_result["intent"],
                    "predicted_action": action,
                    "confidence": confidence,
                    "confidence_level": confidence_level,
                    "rejected": False,
                    "entities": entities
                }
        except Exception as e:
            print(f"❌ NLU 处理失败: {e}")
            nlu_info = {
                "nlu_enabled": True,
                "error": str(e),
                "rejected": True,
                "rejection_reason": "处理异常，请重试"
            }
            
            # 异常也要拒绝当前输入
            return {
                "error": True,
                "type": "nlu_error",
                "message": "⚠️ 处理出错，请重新输入。",
                "hint": f"系统处理你的输入时出现异常，请稍后重试。",
                "nlu_info": nlu_info,
                "playerState": request.playerState
            }
    else:
        # 预设动作或 NLU 未启用
        nlu_info = {"nlu_enabled": nlu_enabled, "used": False}
    
    # 生成游戏事件（只有置信度达标或预设动作才会到达这里）
    event = await generate_event(request.playerState, action)
    
    # 从事件中提取新实体并添加到 NLU 动态库
    if nlu_enabled:
        event_text = event.get("eventText", "")
        extract_entities_from_event(event_text, nlu_model)
    
    # 添加 NLU 信息到响应中
    event["nlu_info"] = nlu_info
    
    return event

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)