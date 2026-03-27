import os
import json
import re
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class NLUModel:
    """NLU 模型类：使用 LLM API 进行意图分类和实体提取"""
    
    def __init__(self, model_name="deepseek-chat", checkpoint_dir="backend/nlu/checkpoints"):
        """
        初始化 NLU 模型
        
        Args:
            model_name: API 模型名称（DeepSeek）
            checkpoint_dir: 数据目录（保留以兼容旧代码）
        """
        self.model_name = model_name
        self.data_dir = Path("backend/nlu/data")
        
        # 加载意图映射表
        with open(self.data_dir / "intent_mapping.json", "r", encoding="utf-8") as f:
            self.intent_mapping = json.load(f)
        
        # 意图列表
        self.intent_list = list(self.intent_mapping.keys())
        self.intent_to_id = {intent: idx for idx, intent in enumerate(self.intent_list)}
        self.id_to_intent = {idx: intent for intent, idx in self.intent_to_id.items()}
        
        print(f"意图列表: {self.intent_list}")
        print(f"总意图数: {len(self.intent_list)}")
        
        # 加载静态实体映射
        self._load_static_entities()
        
        # 初始化动态实体库
        self.dynamic_entities = {
            "LOCATION": set(),
            "NPC": set(),
            "ITEM": set()
        }
        
        # 构建 Few-shot 示例（从训练数据）
        self._build_few_shot_examples()
        
        print(f"✅ NLU 模型已初始化（LLM 版本）")
    
    def _load_static_entities(self):
        """加载预定义的静态实体"""
        try:
            with open(self.data_dir / "entity_mapping.json", "r", encoding="utf-8") as f:
                entity_data = json.load(f)
            
            # 转换为集合格式便于查询
            self.static_entities = {
                entity_type: set(keywords) 
                for entity_type, keywords in entity_data.items()
            }
            print(f"✅ 已加载静态实体库")
            for entity_type, keywords in self.static_entities.items():
                print(f"   - {entity_type}: {len(keywords)} 个")
        except FileNotFoundError:
            print("⚠️  未找到实体映射文件，使用空实体库")
            self.static_entities = {}
    
    def _build_few_shot_examples(self):
        """从训练数据构建 Few-shot 示例"""
        try:
            with open(self.data_dir / "train.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 从每个意图选 2 个示例
            self.few_shot_examples = {}
            for item in data:
                examples = item.get("examples", [])[:2]  # 每个意图取 2 个示例
                for ex in examples:
                    intent = ex["intent"]
                    text = ex["text"]
                    if intent not in self.few_shot_examples:
                        self.few_shot_examples[intent] = []
                    self.few_shot_examples[intent].append(text)
            
            print(f"✅ 已加载 Few-shot 示例（{sum(len(v) for v in self.few_shot_examples.values())} 条）")
        except Exception as e:
            print(f"⚠️  加载 Few-shot 示例失败: {e}")
            self.few_shot_examples = {}
    
    def add_entity(self, entity_type: str, entity_text: str):
        """
        动态添加新实体
        
        Args:
            entity_type: 实体类型 (LOCATION, NPC, ITEM)
            entity_text: 实体文本
        """
        if entity_type in self.dynamic_entities:
            entity_lower = entity_text.lower().strip()
            self.dynamic_entities[entity_type].add(entity_lower)
            print(f"✨ 新实体已添加: {entity_type}='{entity_text}'")
        else:
            print(f"⚠️  未知的实体类型: {entity_type}")
    
    def get_all_entities(self, entity_type: str) -> set:
        """获取所有实体（静态 + 动态）"""
        static = self.static_entities.get(entity_type, set())
        dynamic = self.dynamic_entities.get(entity_type, set())
        return static.union(dynamic)
    
    def _extract_entities(self, text: str) -> dict:
        """
        从文本中提取实体（使用静态+动态库）
        
        Returns:
            {
                "LOCATION": ["forest"],
                "NPC": ["merchant"],
                "ITEM": []
            }
        """
        entities = {entity_type: [] for entity_type in self.dynamic_entities.keys()}
        text_lower = text.lower()
        
        # 查找所有实体
        for entity_type in self.dynamic_entities.keys():
            all_entities = self.get_all_entities(entity_type)
            
            for entity in all_entities:
                # 使用单词边界防止部分匹配
                pattern = rf'\b{re.escape(entity)}\b'
                if re.search(pattern, text_lower):
                    entities[entity_type].append(entity)
        
        return entities
    
    def _call_deepseek_api(self, system_prompt: str, user_input: str) -> str:
        """调用 DeepSeek API"""
        if not DEEPSEEK_API_KEY:
            raise ValueError("❌ 未设置 DEEPSEEK_API_KEY 环境变量")
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.3,  # 降低温度，使分类更稳定
            "max_tokens": 500
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            raise
    
    def predict(self, text: str) -> dict:
        """
        预测文本的意图 + 提取实体
        
        Args:
            text: 用户输入文本
        
        Returns:
            {
                "intent": "explore",
                "action": "探索废墟",
                "confidence": 0.95,
                "intent_id": 0,
                "entities": {
                    "LOCATION": ["forest"],
                    "NPC": ["merchant"],
                    "ITEM": []
                }
            }
        """
        # 构建 prompt
        intent_desc = ", ".join([f"{i}: {self.intent_mapping[i]}" for i in self.intent_list])
        
        # Few-shot 示例
        few_shot_text = ""
        for intent in self.intent_list[:3]:  # 只用前 3 个意图的示例，节省 tokens
            examples = self.few_shot_examples.get(intent, [])
            if examples:
                few_shot_text += f"\n- Intent: {intent}\n"
                for ex in examples[:1]:  # 每个意图只用 1 个例子
                    few_shot_text += f"  Example: \"{ex}\"\n"
        
        system_prompt = f"""You are an NLU classifier for a survival game. Analyze player input and return ONLY a valid JSON response.

Intent options (must be one of these):
{intent_desc}

Few-shot examples:
{few_shot_text}

IMPORTANT:
1. Return ONLY valid JSON, no markdown, no explanation
2. confidence must be between 0.0 and 1.0
3. confidence should be HIGH (>0.85) for clear intents, MEDIUM (0.55-0.85) for unclear, LOW (<0.55) for very unclear
4. entities should be extracted from input if available (or empty arrays)
5. Map found entities to: LOCATION, NPC, or ITEM

Example response format:
{{"intent": "explore", "confidence": 0.92, "entities": {{"LOCATION": ["supermarket"], "NPC": [], "ITEM": []}}}}"""
        
        user_input = f'Analyze this player input: "{text}"'
        
        try:
            response = self._call_deepseek_api(system_prompt, user_input)
            
            # 解析 JSON 响应
            # 清理可能的 markdown 代码块
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            result = json.loads(response)
            
            # 验证和补全结果
            intent = result.get("intent", "other")
            if intent not in self.intent_list:
                intent = "other"
            
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # 限制在 0-1 之间
            
            # 提取实体
            entities = result.get("entities", {})
            for entity_type in self.dynamic_entities.keys():
                if entity_type not in entities:
                    entities[entity_type] = []
            
            # 映射意图 ID
            intent_id = self.intent_to_id.get(intent, len(self.intent_list) - 1)
            action = self.intent_mapping.get(intent, "其他")
            
            # 调试输出
            print(f"[NLU DEBUG] 输入: '{text}'")
            print(f"[NLU DEBUG] 预测: intent={intent}, confidence={confidence:.4f}, action={action}")
            print(f"[NLU DEBUG] 实体: {entities}")
            
            return {
                "intent": intent,
                "action": action,
                "confidence": float(confidence),
                "intent_id": intent_id,
                "entities": entities
            }
        
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"原始响应: {response}")
            # 降级处理：返回 "other"
            return {
                "intent": "other",
                "action": self.intent_mapping["other"],
                "confidence": 0.3,
                "intent_id": self.intent_to_id["other"],
                "entities": {"LOCATION": [], "NPC": [], "ITEM": []}
            }
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            raise
    
    def predict_batch(self, texts: list) -> list:
        """
        批量预测文本的意图
        
        Args:
            texts: 文本列表
        
        Returns:
            预测结果列表
        """
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results
