# API 接口文档

## 1. 游戏事件生成

### 定义
```
POST /api/play
```

### 功能
玩家执行动作，后端调用 DeepSeek AI 生成事件，返回事件描述、资源变化和下一步选项。

### 请求参数

```json
{
  "playerState": {
    "starSign": "白羊座",
    "shelter": {
      "type": "山洞",
      "durability": 85
    },
    "resources": {
      "food": 7,
      "water": 4,
      "tools": 1
    },
    "health": 85,
    "day": 3
  },
  "action": "探索废墟"
}
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `playerState` | Object | ✅ | 玩家当前游戏状态 |
| `playerState.starSign` | String | ✅ | 玩家星座（12星座之一） |
| `playerState.shelter` | Object | ✅ | 庇护所信息 |
| `playerState.shelter.type` | String | ✅ | 庇护所类型 |
| `playerState.shelter.durability` | Number | ❌ | 庇护所耐久度 |
| `playerState.resources.food` | Number | ✅ | 食物数量 |
| `playerState.resources.water` | Number | ✅ | 水数量 |
| `playerState.resources.tools` | Number | ✅ | 工具数量 |
| `playerState.health` | Number | ✅ | 健康值 |
| `playerState.day` | Number | ✅ | 游戏天数 |
| `action` | String | ✅ | 玩家选择的动作 |

### 返回值

```json
{
  "eventText": "你在废墟中发现了一个通风口...",
  "resourceChanges": {
    "food": 2,
    "water": -1,
    "tools": 0
  },
  "stateChanges": {
    "health": -5
  },
  "nextActions": [
    "继续探索",
    "返回庇护所",
    "学习修复技能"
  ]
}
```

| 返回字段 | 类型 | 说明 |
|---------|------|------|
| `eventText` | String | AI 生成的事件描述 |
| `resourceChanges.food` | Number | 食物变化量 |
| `resourceChanges.water` | Number | 水变化量 |
| `resourceChanges.tools` | Number | 工具变化量 |
| `stateChanges.health` | Number | 健康值变化量 |
| `nextActions` | Array[String] | 下一步可选动作（通常3个） |
