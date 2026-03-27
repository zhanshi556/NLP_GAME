<template>
  <div class="game-container">
    <h2>末日星座生存游戏</h2>

    <div v-if="!playerState.starSign">
      <h3>选择你的星座：</h3>
      <button v-for="s in starSigns" :key="s" @click="selectStar(s)">
        {{ s }}
      </button>
    </div>

    <div v-else>
      <div class="status">
        <p>日数: {{ playerState.day }}</p>
        <p>健康: {{ playerState.health }}</p>
        <p>食物: {{ playerState.resources.food }}</p>
        <p>水: {{ playerState.resources.water }}</p>
        <p>工具: {{ playerState.resources.tools }}</p>
      </div>

      <div class="event-text">
        <p v-html="currentEvent"></p>
      </div>

      <!-- 低置信度警告提示 -->
      <div v-if="warning" class="warning-box">
        <p v-html="warning"></p>
      </div>

      <!-- 文本输入框 -->
      <div class="input-section">
        <input 
          v-model="userInput" 
          placeholder="输入你的动作（如：我想探索一下）"
          @keyup.enter="submitAction"
          type="text"
          class="action-input"
        />
        <button @click="submitAction" class="submit-btn">提交</button>
      </div>

      <!-- 或选择预设按钮 -->
      <div class="or-divider">或</div>

      <div class="actions">
        <button v-for="a in nextActions" :key="a" @click="takeAction(a)" class="preset-btn">
          {{ a }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      starSigns: ["白羊座","金牛座","双子座","巨蟹座","狮子座","处女座","天秤座","天蝎座","射手座","摩羯座","水瓶座","双鱼座"],
      playerState: {
        starSign: null,
        shelter: {},
        resources: { food:5, water:5, tools:3 },
        health: 100,
        day: 1
      },
      currentEvent: "请选择你的星座开始游戏。",
      nextActions: [],
      userInput: "",  // 用户文本输入
      loading: false,  // 加载状态
      warning: ""  // 警告信息（如低置信提示）
    };
  },
  methods: {
    selectStar(sign) {
      this.playerState.starSign = sign;
      this.playerState.shelter = { type: "基础庇护所", durability:100 };
      this.currentEvent = `你选择了 ${sign}，庇护所已建立。`;
      this.nextActions = ["探索废墟","修理庇护所","休息"];
      this.warning = "";  // 清除任何警告信息
    },
    
    submitAction() {
      // 用户输入的文本提交
      if (!this.userInput.trim()) {
        alert("请输入你的动作");
        return;
      }
      this.takeAction(this.userInput.trim());
      this.userInput = "";  // 清空输入框
    },
    
    async takeAction(action) {
      if (this.loading) return;  // 防止重复提交
      
      this.loading = true;
      try {
        const response = await axios.post("http://localhost:8000/api/play", {
          playerState: this.playerState,
          action
        });
        
        const data = response.data;
        
        // 错误处理：后端返回了错误（如低置信度）
        if (data.error) {
          console.warn("NLU 拒绝了输入：", data);
          
          // 只显示警告提示，不改变任何游戏状态
          if (data.type === "low_confidence") {
            this.warning = `<strong>❌ 输入不够清楚</strong><br>${data.hint}<br><strong>请重新输入，或者选择下方的参考选项。</strong>`;
          } else if (data.type === "nlu_error") {
            this.warning = `<strong>⚠️ 处理出错</strong><br>${data.hint}<br><strong>请重新输入，或者选择下方的参考选项。</strong>`;
          } else {
            this.warning = `<strong>⚠️ 输入错误</strong><br>${data.message || "请重新输入。"}<br><strong>请重新输入，或者选择下方的参考选项。</strong>`;
          }
          
          // 关键：不改变 currentEvent、nextActions、playerState、日期
          // 玩家保留当前状态，可以重新尝试
          return;  // 提前返回，不执行下面的正常逻辑
        }
        
        // 正常游戏流程（只有成功的情况才执行）
        
        // 清除之前的警告信息
        this.warning = "";
        
        // 更新资源
        if(data.resourceChanges){
          for(const key in data.resourceChanges){
            if(this.playerState.resources[key]!==undefined)
              this.playerState.resources[key] += data.resourceChanges[key];
          }
        }
        
        // 更新状态
        if(data.stateChanges){
          for(const key in data.stateChanges){
            if(this.playerState[key]!==undefined)
              this.playerState[key] += data.stateChanges[key];
          }
        }
        
        // 推进游戏
        this.playerState.day += 1;
        this.currentEvent = data.eventText;
        this.nextActions = data.nextActions || ["探索废墟","修理庇护所","休息"];
        
        // 检查游戏是否结束
        if(this.playerState.health <= 0) {
          this.currentEvent += "\n\n💀 你已经死亡，游戏结束。";
          this.nextActions = [];
        }
        
      } catch(err){
        console.error(err);
        alert("请求失败，请检查后端是否运行");
        this.currentEvent = "❌ 发生错误，请稍后重试。";
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.game-container {
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 800px;
  margin: 0 auto;
}

.status {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f0f0f0;
  border-radius: 5px;
}

.status p {
  margin: 5px 0;
  font-size: 14px;
}

.event-text {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff8dc;
  border-left: 4px solid #ffa500;
  border-radius: 3px;
  min-height: 60px;
  line-height: 1.6;
}

/* 文本输入框样式 */
.input-section {
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
}

.action-input {
  flex: 1;
  padding: 10px;
  border: 2px solid #4CAF50;
  border-radius: 5px;
  font-size: 14px;
}

.action-input:focus {
  outline: none;
  box-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
}

.submit-btn {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}

.submit-btn:hover {
  background-color: #45a049;
}

/* 分割线 */
.or-divider {
  text-align: center;
  margin: 10px 0;
  color: #888;
  font-size: 12px;
}

/* 按钮组 */
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-btn {
  padding: 8px 12px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
}

.preset-btn:hover {
  background-color: #0b7dda;
}

button {
  padding: 10px 15px;
  margin: 5px;
  background-color: #008CBA;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #007399;
}

h2 {
  text-align: center;
  color: #333;
}

h3 {
  text-align: center;
  color: #666;
}

/* 警告/提示框 */
.warning-box {
  margin: 15px 0;
  padding: 12px;
  background-color: #fff3cd;
  border-left: 4px solid #ff9800;
  border-radius: 3px;
  color: #856404;
  line-height: 1.6;
}

.warning-box p {
  margin: 0;
}
</style>