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

      <div class="actions">
        <button v-for="a in nextActions" :key="a" @click="takeAction(a)">
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
      nextActions: []
    };
  },
  methods: {
    selectStar(sign) {
      this.playerState.starSign = sign;
      this.playerState.shelter = { type: "基础庇护所", durability:100 };
      this.currentEvent = `你选择了 ${sign}，庇护所已建立。`;
      this.nextActions = ["探索废墟","修理庇护所","休息"];
    },
    async takeAction(action) {
      try {
        const response = await axios.post("http://localhost:8000/api/play", {
          playerState: this.playerState,
          action
        });
        const data = response.data;
        if(data.resourceChanges){
          for(const key in data.resourceChanges){
            if(this.playerState.resources[key]!==undefined)
              this.playerState.resources[key] += data.resourceChanges[key];
          }
        }
        if(data.stateChanges){
          for(const key in data.stateChanges){
            if(this.playerState[key]!==undefined)
              this.playerState[key] += data.stateChanges[key];
          }
        }
        this.playerState.day += 1;
        this.currentEvent = data.eventText;
        this.nextActions = data.nextActions;
      } catch(err){
        console.error(err);
      }
    }
  }
}
</script>

<style>
.game-container { padding: 20px; font-family: sans-serif; }
.status { margin-bottom: 10px; }
.actions button { margin: 5px; }
</style>