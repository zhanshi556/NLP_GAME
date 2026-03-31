<template>
  <div class="game-container">
    <h2>Post-Apocalyptic Zodiac Survival</h2>

    <div v-if="!playerState.starSign">
      <h3>Choose your Zodiac sign:</h3>
      <button v-for="s in starSigns" :key="s" @click="selectStar(s)">
        {{ s }}
      </button>
    </div>

    <div v-else>
      <div class="status">
        <p>Day: {{ playerState.day }}</p>
        <p>Health: {{ playerState.health }}</p>
        <p>Food: {{ playerState.resources.food }}</p>
        <p>Water: {{ playerState.resources.water }}</p>
        <p>Tools: {{ playerState.resources.tools }}</p>
      </div>

      <div class="event-text">
        <p v-html="currentEvent"></p>
      </div>

      <!-- Low confidence warning -->
      <div v-if="warning" class="warning-box">
        <p v-html="warning"></p>
      </div>

      <!-- 文本输入框 (仅当游戏未结束时显示) -->
      <div class="input-section" v-if="playerState.health > 0 && playerState.day < 100">
        <input 
          v-model="userInput" 
          placeholder="Enter your action (e.g., I want to explore)"
          @keyup.enter="submitAction"
          type="text"
          class="action-input"
        />
        <button @click="submitAction" class="submit-btn">Submit</button>
      </div>

      <!-- 或选择预设按钮 (仅当游戏未结束时显示) -->
      <div class="or-divider" v-if="playerState.health > 0 && playerState.day < 100">OR</div>

      <div class="actions" v-if="playerState.health > 0 && playerState.day < 100">
        <button v-for="a in nextActions" :key="a" @click="takeAction(a)" class="preset-btn">
          {{ a }}
        </button>
      </div>

      <!-- 游戏结束提示：重新开始按钮 -->
      <div v-if="playerState.health <= 0 || playerState.day >= 100" style="text-align: center; margin-top: 20px;">
        <button @click="restartGame" style="background-color: #f44336; padding: 12px 24px; font-size: 16px;">Restart Game (重新开始)</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      starSigns: ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
      playerState: {
        starSign: null,
        shelter: {},
        resources: { food:5, water:5, tools:3 },
        health: 100,
        day: 1,
        actionCount: 0,
        history: [], // 5回合短期记忆 (Short-term memory)
        longTermMemory: [], // 长期记忆 (Long-term memory max 10)
        epicMemory: [] // 史诗章节 (Epic Chapters compressed from LTM)
      },
      currentEvent: "Please choose your Zodiac sign to begin.",
      nextActions: [],
      userInput: "",  // 用户文本输入
      loading: false,  // 加载状态
      warning: ""  // 警告信息（如低置信提示）
    };
  },
  methods: {
    selectStar(sign) {
      this.playerState.starSign = sign;
      this.playerState.shelter = { type: "Basic Shelter", durability:100 };
      this.currentEvent = `You selected ${sign}. Shelter has been established.`;
      this.nextActions = ["Explore Ruins", "Fix Shelter", "Rest"];
      this.warning = "";  // 清除任何警告信息
    },

    restartGame() {
      // 重新开始游戏，重置所有状态
      this.playerState = {
        starSign: null,
        shelter: {},
        resources: { food:5, water:5, tools:3 },
        health: 100,
        day: 1,
        actionCount: 0,
        history: [], 
        longTermMemory: [], 
        epicMemory: [] 
      };
      this.currentEvent = "Please choose your Zodiac sign to begin.";
      this.nextActions = [];
      this.userInput = "";
      this.warning = "";
    },
    
    submitAction() {
      // 用户输入的文本提交
      if (!this.userInput.trim()) {
        alert("Please enter your action");
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
          console.warn("NLU rejected the input:", data);
          
          // 只显示警告提示，不改变任何游戏状态
          if (data.type === "low_confidence") {
            this.warning = `<strong>❌ Unclear Input</strong><br>${data.hint}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
          } else if (data.type === "nlu_error") {
            this.warning = `<strong>⚠️ Processing Error</strong><br>${data.hint}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
          } else {
            this.warning = `<strong>⚠️ Input Error</strong><br>${data.message || "Please try again."}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
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
        
        // 更新状态 (Health with max 100 limit)
        if(data.stateChanges){
          for(const key in data.stateChanges){
            if(this.playerState[key]!==undefined) {
              this.playerState[key] += data.stateChanges[key];
              // 限制健康度最大为 100
              if (key === 'health' && this.playerState[key] > 100) {
                this.playerState[key] = 100;
              }
            }
          }
        }
        
        // 更新动作计数 (触发后续长时记忆的基础)
        this.playerState.actionCount = (this.playerState.actionCount || 0) + 1;
        
        // 处理后端的记忆架构更新 (长期记忆与史诗章节更新)
        if (data._memoryUpdates) {
          if (data._memoryUpdates.newEpicChapters) {
             // 将长篇大论压缩进史诗章节，并清空当前的长时记忆
             this.playerState.epicMemory.push(...data._memoryUpdates.newEpicChapters);
             this.playerState.longTermMemory = []; 
          }
          if (data._memoryUpdates.newSummary) {
             this.playerState.longTermMemory.push(data._memoryUpdates.newSummary);
          }
        }

        // 短期记忆滑动窗口（最大保留5回合，最旧的被挤出）
        this.playerState.history.push({
          action: action,
          result: data.eventText
        });
        if (this.playerState.history.length > 5) {
          this.playerState.history.shift();
        }
        
        // 推进游戏
        this.playerState.day += 1;
        this.currentEvent = data.eventText;
        this.nextActions = data.nextActions || ["Explore Ruins", "Fix Shelter", "Rest"];
        
        // 检查游戏结束条件 (死亡或胜利)
        if (this.playerState.health <= 0) {
          this.playerState.health = 0; // 避免出现负数健康度
          this.currentEvent += "<br><br><strong style='color: red; font-size: 1.2em;'>💀 Game Over: You have failed to survive. (游戏结束，你已失败)</strong>";
          this.nextActions = []; // 清空操作按钮，玩家无法继续操作
          this.userInput = ""; // 禁用输入框在UI层面的对应处理可在上面通过 v-if 加强限制，但清空是一个好习惯
        } else if (this.playerState.day >= 100) {
          this.currentEvent += "<br><br><strong style='color: green; font-size: 1.2em;'>🏆 Game Over: You have successfully survived 100 days! (游戏结束，存活成功)</strong>";
          this.nextActions = []; // 清空操作按钮
        }
        
      } catch(err){
        console.error(err);
        alert("Request failed, please check if the backend is running");
        this.currentEvent = "❌ An error occurred, please try again later.";
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