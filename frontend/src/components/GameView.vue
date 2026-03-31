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
        <p>Day: {{ playerState.day }} <span v-if="isCataclysmDay" class="cataclysm-warning">⚠️ CATACLYSM DAY!</span></p>
        <p>Health: {{ playerState.health }}</p>
        <p>Food: {{ playerState.resources.food }}</p>
        <p>Water: {{ playerState.resources.water }}</p>
        <p>Tools: {{ playerState.resources.tools }}</p>
        <p>Shelter Durability: {{ playerState.shelter.durability }}</p>
        <p v-if="playerState.apocalypseTheme" class="apocalypse-theme"><strong>🌍 {{ playerState.apocalypseTheme }}</strong></p>
      </div>

      <!-- Inventory Section (Hidden by default, shown only with backpack button) -->
      <div class="inventory-toggle-section">
        <button class="backpack-btn" @click="showInventory = !showInventory">
          🎒 Backpack ({{ playerState.inventory.length }}/{{ MAX_INVENTORY_SLOTS }})
        </button>
      </div>

      <div v-if="showInventory" class="inventory-section">
        <h4>🎒 Inventory</h4>
        <div v-if="playerState.inventory.length === 0" class="empty-inventory">
          No items in backpack
        </div>
        <div v-else class="inventory-grid">
          <div v-for="(item, index) in playerState.inventory" :key="index" class="inventory-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-effect">
              <span v-if="item.food > 0">🍖+{{ item.food }}</span>
              <span v-if="item.water > 0">💧+{{ item.water }}</span>
              <span v-if="item.health > 0">❤️+{{ item.health }}</span>
              <span v-if="item.repair > 0">🔧+{{ item.repair }}</span>
            </span>
          </div>
        </div>
        <div v-if="playerState.inventory.length >= MAX_INVENTORY_SLOTS" class="inventory-full-warning">
          ⚠️ Your backpack is full! Max {{ MAX_INVENTORY_SLOTS }} items.
        </div>
      </div>

      <div class="event-text">
        <p v-html="currentEvent"></p>
      </div>

      <!-- Cataclysm Day Warning -->
      <div v-if="isCataclysmDay && !playerState.atShelter" class="cataclysm-box">
        <p><strong>⚠️ CATACLYSM APPROACHING!</strong></p>
        <p>You must return to shelter before the day ends! Resource consumption is 5x today.</p>
        <button @click="returnToShelter" class="shelter-btn">Return to Shelter</button>
      </div>

      <!-- Rest Modal -->
      <div v-if="showRestModal" class="modal-overlay">
        <div class="modal-content">
          <h3>🛏️ Rest & Recover</h3>
          <p>Select items to consume:</p>
          <div class="rest-inventory">
            <div v-for="(item, index) in playerState.inventory" :key="index"
                 class="rest-item"
                 :class="{ selected: selectedItems.includes(index), 'repair-item': item.repair > 0 }"
                 @click="toggleItemSelection(index)">
              <input type="checkbox" :checked="selectedItems.includes(index)" :disabled="item.repair > 0" />
              <span class="item-name">{{ item.name }}</span>
              <span class="item-effect">
                <span v-if="item.food > 0">🍖+{{ item.food }}</span>
                <span v-if="item.water > 0">💧+{{ item.water }}</span>
                <span v-if="item.health > 0">❤️+{{ item.health }}</span>
                <span v-if="item.repair > 0">🔧 (Use "Fix Shelter")</span>
              </span>
            </div>
          </div>
          <div v-if="playerState.inventory.length === 0" class="no-items">
            No items to consume. Rest will still pass time.
          </div>
          <div class="modal-actions">
            <button @click="confirmRest" class="confirm-btn">Confirm Rest</button>
            <button @click="cancelRest" class="cancel-btn">Cancel</button>
          </div>
        </div>
      </div>

      <!-- Fix Shelter Button (Extra action, doesn't consume turn) -->
      <div class="fix-shelter-section" v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal && !isCataclysmDay">
        <button @click="fixShelter" class="fix-shelter-btn" :disabled="!hasRepairKit">
          🔧 Fix Shelter ({{ repairKitCount }} kits)
        </button>
        <span class="fix-shelter-hint">Extra action - doesn't consume your turn</span>
      </div>

      <!-- Low confidence warning -->
      <div v-if="warning" class="warning-box">
        <p v-html="warning"></p>
      </div>

      <!-- Text input (only when game not over) -->
      <div class="input-section" v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal">
        <input
          v-model="userInput"
          placeholder="Enter your action (e.g., I want to explore)"
          @keyup.enter="submitAction"
          type="text"
          class="action-input"
        />
        <button @click="submitAction" class="submit-btn">Submit</button>
      </div>

      <!-- Preset buttons (only when game not over) -->
      <div class="or-divider" v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal">OR</div>

      <div class="actions" v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal">
        <button v-for="a in nextActions" :key="a" @click="takeAction(a)" class="preset-btn">
          {{ a }}
        </button>
      </div>

      <!-- Game over: restart button -->
      <div v-if="playerState.health <= 0 || playerState.day >= 100" style="text-align: center; margin-top: 20px;">
        <button @click="restartGame" style="background-color: #f44336; padding: 12px 24px; font-size: 16px;">Restart Game</button>
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
      apocalypseThemes: {
        "Aries": "Massive Flooding - Rising waters and flash floods have submerged the world.",
        "Taurus": "Acid Rain - Toxic precipitation falls from the sky, corroding everything it touches.",
        "Gemini": "Zombie Outbreak - The dead have risen and roam the wasteland hunting the living.",
        "Cancer": "Extreme Heat - Record-breaking temperatures turn the world into an inferno.",
        "Leo": "Extreme Drought - All water sources have vanished. The land is barren.",
        "Virgo": "Solar Collapse - The Sun's radiation has intensified, scorching the surface.",
        "Libra": "Alien Invasion - Extraterrestrial forces have arrived and are harvesting Earth's resources.",
        "Scorpio": "Dinosaur Revival - Prehistoric creatures have been cloned and released into the world.",
        "Sagittarius": "Cockroach Plague - Mutant insects have overrun civilization everywhere.",
        "Capricorn": "New Ice Age - Temperatures have plummeted and glaciers spread. Eternal winter.",
        "Aquarius": "Mega Tsunami - Colossal waves triggered by earthquakes have devastated coastal areas.",
        "Pisces": "Biological Disaster - A genetically engineered virus has mutated the world's population."
      },
      playerState: {
        starSign: null,
        shelter: {},
        resources: { food:5, water:5, tools:3 },
        health: 100,
        day: 1,
        actionCount: 0,
        history: [],
        longTermMemory: [],
        epicMemory: [],
        inventory: [],
        atShelter: true,
        apocalypseTheme: null
      },
      currentEvent: "Please choose your Zodiac sign to begin.",
      nextActions: [],
      userInput: "",
      loading: false,
      warning: "",
      showRestModal: false,
      selectedItems: [],
      showInventory: false,
      MAX_INVENTORY_SLOTS: 10
    };
  },
  computed: {
    isCataclysmDay() {
      return this.playerState.day % 7 === 0;
    },
    hasRepairKit() {
      return this.playerState.inventory.some(item => item.repair && item.repair > 0);
    },
    repairKitCount() {
      return this.playerState.inventory.filter(item => item.repair && item.repair > 0).length;
    }
  },
  watch: {
    'playerState.day': function(newVal, oldVal) {
      console.log(`🔔 Day Watcher: Day changed from ${oldVal} to ${newVal}`);
    }
  },
  methods: {
    selectStar(sign) {
      this.playerState.starSign = sign;
      this.playerState.shelter = { type: "Basic Shelter", durability: 100 };
      this.playerState.inventory = [];
      this.playerState.atShelter = true;
      this.playerState.apocalypseTheme = this.apocalypseThemes[sign];
      this.playerState.day = 1;  // Ensure day is initialized to 1
      this.playerState.actionCount = 0;
      this.currentEvent = `You selected ${sign}. Shelter has been established. Your journey begins in a world ravaged by ${this.apocalypseThemes[sign].split(' - ')[0]}...`;
      this.nextActions = ["Explore Ruins", "Search for Water", "Rest"];
      this.warning = "";
      console.log(`🎮 Game Started with ${sign}. Day initialized to: ${this.playerState.day}`);
    },

    restartGame() {
      this.playerState = {
        starSign: null,
        shelter: {},
        resources: { food:5, water:5, tools:3 },
        health: 100,
        day: 1,
        actionCount: 0,
        history: [],
        longTermMemory: [],
        epicMemory: [],
        inventory: [],
        atShelter: true,
        apocalypseTheme: null
      };
      this.currentEvent = "Please choose your Zodiac sign to begin.";
      this.nextActions = [];
      this.userInput = "";
      this.warning = "";
      this.showRestModal = false;
      this.selectedItems = [];
      this.showInventory = false;
    },

    returnToShelter() {
      this.playerState.atShelter = true;
      this.currentEvent += "<br><br><strong>You rushed back to your shelter just in time before the cataclysm hits!</strong>";
    },

    toggleItemSelection(index) {
      // Don't allow selecting repair items (they can't be consumed)
      const item = this.playerState.inventory[index];
      if (item.repair && item.repair > 0) {
        return;
      }

      const idx = this.selectedItems.indexOf(index);
      if (idx > -1) {
        this.selectedItems.splice(idx, 1);
      } else {
        this.selectedItems.push(index);
      }
    },

    confirmRest() {
      let totalFood = 0;
      let totalWater = 0;
      let totalHealth = 0;
      const consumedItems = [];

      this.selectedItems.sort((a, b) => b - a).forEach(index => {
        const item = this.playerState.inventory[index];
        totalFood += item.food || 0;
        totalWater += item.water || 0;
        totalHealth += item.health || 0;
        consumedItems.push(item.name);
        this.playerState.inventory.splice(index, 1);
      });

      this.playerState.resources.food += totalFood;
      this.playerState.resources.water += totalWater;
      this.playerState.health = Math.min(100, this.playerState.health + totalHealth);

      let restMessage = "You take a moment to rest.";
      if (consumedItems.length > 0) {
        restMessage += ` You consumed: ${consumedItems.join(", ")}.`;
        if (totalFood > 0) restMessage += ` Food +${totalFood}.`;
        if (totalWater > 0) restMessage += ` Water +${totalWater}.`;
        if (totalHealth > 0) restMessage += ` Health +${totalHealth}.`;
      }

      // Apply daily consumption BEFORE incrementing day
      this.applyDailyConsumption();

      // CRITICAL: Increment day to progress the game
      const oldDay = this.playerState.day;
      this.playerState.day += 1;
      console.log(`✅ confirmRest: Day updated from ${oldDay} to ${this.playerState.day}`);
      console.log(`📊 Current playerState.day: ${this.playerState.day}`);
      this.$nextTick(() => {
        console.log(`✅ Vue tick after Rest: Day is now ${this.playerState.day}`);
      });

      // Check if it's a cataclysm day (after day increment)
      if (this.isCataclysmDay) {
        this.applyCataclysmEffects();
      }

      this.currentEvent = restMessage;
      this.showRestModal = false;
      this.selectedItems = [];
      this.playerState.atShelter = true;

      this.checkGameOver();
    },

    cancelRest() {
      this.showRestModal = false;
      this.selectedItems = [];
    },

    fixShelter() {
      // Can't fix shelter on cataclysm day
      if (this.isCataclysmDay) {
        this.warning = "<strong>⚠️ Cataclysm Day!</strong><br>You cannot repair shelter during a cataclysm. Survive first!";
        return;
      }

      // Find a repair tool in inventory
      const repairToolIndex = this.playerState.inventory.findIndex(
        item => item.repair && item.repair > 0
      );

      if (repairToolIndex === -1) {
        this.warning = "<strong>⚠️ No Repair Tools!</strong><br>You need a Repair Kit to fix the shelter. Explore to find one.";
        return;
      }

      // Consume the repair tool
      const repairTool = this.playerState.inventory[repairToolIndex];
      const repairAmount = repairTool.repair || 30;
      this.playerState.inventory.splice(repairToolIndex, 1);

      // Restore shelter durability (max 100)
      const oldDurability = this.playerState.shelter.durability;
      this.playerState.shelter.durability = Math.min(100, this.playerState.shelter.durability + repairAmount);
      const actualRepair = this.playerState.shelter.durability - oldDurability;

      // This is an extra action - does NOT consume turn, day does NOT advance
      this.currentEvent += `<br><br><strong style='color: green;'>🔧 You used a ${repairTool.name} to repair your shelter. Durability +${actualRepair} (now ${this.playerState.shelter.durability}).</strong>`;
      this.warning = "";
    },

    applyDailyConsumption() {
      const multiplier = this.isCataclysmDay ? 5 : 1;
      this.playerState.resources.food -= 1 * multiplier;
      this.playerState.resources.water -= 1 * multiplier;

      if (this.playerState.resources.food < 0) {
        this.playerState.health += this.playerState.resources.food * 5;
        this.playerState.resources.food = 0;
      }
      if (this.playerState.resources.water < 0) {
        this.playerState.health += this.playerState.resources.water * 5;
        this.playerState.resources.water = 0;
      }
    },

    applyCataclysmEffects() {
      const damage = Math.floor(Math.random() * 20) + 20;
      this.playerState.shelter.durability -= damage;
      if (this.playerState.shelter.durability < 0) {
        this.playerState.shelter.durability = 0;
      }

      if (!this.playerState.atShelter) {
        const healthLoss = Math.floor(Math.random() * 30) + 20;
        this.playerState.health -= healthLoss;
        this.currentEvent += `<br><br><strong style='color: red;'>☠️ CATACLYSM! You were caught outside the shelter! You took ${healthLoss} damage!</strong>`;
      } else {
        this.currentEvent += `<br><br><strong style='color: orange;'>⚡ CATACLYSM! The shelter protected you, but took ${damage} durability damage.</strong>`;
      }
    },

    checkGameOver() {
      if (this.playerState.health <= 0) {
        this.playerState.health = 0;
        this.currentEvent += "<br><br><strong style='color: red; font-size: 1.2em;'>💀 Game Over: You have failed to survive.</strong>";
        this.nextActions = [];
      } else if (this.playerState.day >= 100) {
        this.currentEvent += "<br><br><strong style='color: green; font-size: 1.2em;'>🏆 Game Over: You have successfully survived 100 days!</strong>";
        this.nextActions = [];
      }
    },
    
    submitAction() {
      if (!this.userInput.trim()) {
        alert("Please enter your action");
        return;
      }
      this.takeAction(this.userInput.trim());
      this.userInput = "";
    },

    async takeAction(action) {
      if (this.loading) return;

      // Handle Rest action specially - open modal
      if (action.toLowerCase() === "rest" || action.toLowerCase().includes("rest")) {
        this.showRestModal = true;
        return;
      }

      // Mark player as leaving shelter when exploring
      if (action.toLowerCase().includes("explore") || action.toLowerCase().includes("search") ||
          action.toLowerCase().includes("hunt") || action.toLowerCase().includes("scavenge")) {
        this.playerState.atShelter = false;
      }

      this.loading = true;
      try {
        const response = await axios.post("http://localhost:8000/api/play", {
          playerState: this.playerState,
          action
        });

        const data = response.data;

        if (data.error) {
          console.warn("NLU rejected the input:", data);

          if (data.type === "low_confidence") {
            this.warning = `<strong>❌ Unclear Input</strong><br>${data.hint}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
          } else if (data.type === "nlu_error") {
            this.warning = `<strong>⚠️ Processing Error</strong><br>${data.hint}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
          } else {
            this.warning = `<strong>⚠️ Input Error</strong><br>${data.message || "Please try again."}<br><strong>Please type again, or select one of the suggested actions below.</strong>`;
          }

          return;
        }

        this.warning = "";

        // Add new items to inventory (instead of directly changing resources)
        if (data.newItems && data.newItems.length > 0) {
          let addedItems = [];
          let rejectedItems = [];

          data.newItems.forEach(item => {
            // Check if backpack is full (max 10 items)
            if (this.playerState.inventory.length < this.MAX_INVENTORY_SLOTS) {
              this.playerState.inventory.push(item);
              addedItems.push(item.name);
            } else {
              rejectedItems.push(item.name);
            }
          });

          // Show warning if backpack is full
          if (rejectedItems.length > 0) {
            this.warning = `<strong>⚠️ Backpack Full!</strong><br>Could not pick up: ${rejectedItems.join(", ")}<br>Your backpack can only hold ${this.MAX_INVENTORY_SLOTS} items max.`;
          }
        }

        // Only apply tool changes directly (tools are not consumable items)
        if (data.resourceChanges && data.resourceChanges.tools) {
          this.playerState.resources.tools += data.resourceChanges.tools;
        }

        // Apply state changes (health from combat, etc. - not from items)
        if (data.stateChanges) {
          for (const key in data.stateChanges) {
            if (this.playerState[key] !== undefined) {
              this.playerState[key] += data.stateChanges[key];
              if (key === 'health' && this.playerState[key] > 100) {
                this.playerState[key] = 100;
              }
            }
          }
        }

        this.playerState.actionCount = (this.playerState.actionCount || 0) + 1;

        if (data._memoryUpdates) {
          if (data._memoryUpdates.newEpicChapters) {
            this.playerState.epicMemory.push(...data._memoryUpdates.newEpicChapters);
            this.playerState.longTermMemory = [];
          }
          if (data._memoryUpdates.newSummary) {
            this.playerState.longTermMemory.push(data._memoryUpdates.newSummary);
          }
        }

        this.playerState.history.push({
          action: action,
          result: data.eventText
        });
        if (this.playerState.history.length > 5) {
          this.playerState.history.shift();
        }

        // Apply daily consumption
        this.applyDailyConsumption();

        // CRITICAL: Increment day and force Vue reactivity
        this.playerState.day += 1;
        console.log(`✅ takeAction: Day updated to ${this.playerState.day}`);
        this.$nextTick(() => {
          console.log(`✅ Vue tick: Day is now ${this.playerState.day}`);
        });

        // Check if it's cataclysm day
        if (this.isCataclysmDay) {
          this.applyCataclysmEffects();
        }

        this.currentEvent = data.eventText;
        this.nextActions = data.nextActions || ["Explore Ruins", "Search for Water", "Rest"];

        this.checkGameOver();

      } catch (err) {
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

.cataclysm-warning {
  color: #ff4444;
  font-weight: bold;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.apocalypse-theme {
  color: #d32f2f;
  font-style: italic;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
}

/* Inventory Toggle Button */
.inventory-toggle-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
}

.backpack-btn {
  padding: 10px 15px;
  background-color: #FF9800;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.3s ease;
}

.backpack-btn:hover {
  background-color: #F57C00;
  transform: scale(1.05);
}

.backpack-btn:active {
  transform: scale(0.98);
}

/* Inventory Section */
.inventory-section {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #e8f5e9;
  border-radius: 5px;
  border: 2px solid #4CAF50;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.inventory-section h4 {
  margin: 0 0 10px 0;
  color: #2e7d32;
}

.empty-inventory {
  color: #888;
  font-style: italic;
}

.inventory-full-warning {
  margin-top: 10px;
  padding: 8px;
  background-color: #fff3cd;
  border-left: 3px solid #FF9800;
  color: #856404;
  font-size: 13px;
  border-radius: 3px;
}

.inventory-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.inventory-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background-color: #fff;
  border: 1px solid #4CAF50;
  border-radius: 5px;
  font-size: 12px;
}

.item-name {
  font-weight: bold;
  color: #333;
}

.item-effect {
  color: #666;
  font-size: 11px;
}

.item-effect span {
  margin-right: 5px;
}

/* Cataclysm Warning Box */
.cataclysm-box {
  margin: 15px 0;
  padding: 15px;
  background-color: #ffebee;
  border: 2px solid #f44336;
  border-radius: 5px;
  text-align: center;
}

.cataclysm-box p {
  margin: 5px 0;
  color: #c62828;
}

.shelter-btn {
  margin-top: 10px;
  padding: 10px 20px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}

.shelter-btn:hover {
  background-color: #d32f2f;
}

/* Rest Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  color: #333;
}

.rest-inventory {
  margin: 15px 0;
  max-height: 300px;
  overflow-y: auto;
}

.rest-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin: 5px 0;
  background-color: #f5f5f5;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.rest-item:hover {
  background-color: #e0e0e0;
}

.rest-item.selected {
  background-color: #c8e6c9;
  border: 2px solid #4CAF50;
}

.rest-item.repair-item {
  background-color: #e3f2fd;
  border: 1px dashed #2196F3;
  cursor: not-allowed;
  opacity: 0.7;
}

.rest-item input[type="checkbox"] {
  pointer-events: none;
}

.no-items {
  color: #888;
  font-style: italic;
  text-align: center;
  padding: 20px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 15px;
}

.confirm-btn {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.confirm-btn:hover {
  background-color: #45a049;
}

.cancel-btn {
  padding: 10px 20px;
  background-color: #9e9e9e;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.cancel-btn:hover {
  background-color: #757575;
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

.or-divider {
  text-align: center;
  margin: 10px 0;
  color: #888;
  font-size: 12px;
}

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

/* Fix Shelter Section */
.fix-shelter-section {
  margin: 15px 0;
  padding: 10px;
  background-color: #e3f2fd;
  border: 1px solid #2196F3;
  border-radius: 5px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.fix-shelter-btn {
  padding: 8px 16px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  font-size: 14px;
}

.fix-shelter-btn:hover:not(:disabled) {
  background-color: #1976D2;
}

.fix-shelter-btn:disabled {
  background-color: #bdbdbd;
  cursor: not-allowed;
}

.fix-shelter-hint {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

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