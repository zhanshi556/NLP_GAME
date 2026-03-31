<template>
  <div class="ta-page">
    <div class="ta-shell">
      <header class="ta-header">
        <p class="ta-kicker">Interactive fiction</p>
        <h1 class="ta-title">
          Post-Apocalyptic Zodiac Survival
          <span v-if="playerState.starSign" class="ta-title-sign">{{ playerState.starSign }}</span>
        </h1>
        <p class="ta-sub">Type a command or choose a path—each action advances the day.</p>
      </header>

      <div v-if="!playerState.starSign" class="ta-block ta-intro">
        <h2 class="ta-section-label">Begin your story</h2>
        <p class="ta-lead">Select your sign. The wasteland’s fate shifts with the stars.</p>
        <div class="ta-sign-grid">
          <button
            v-for="s in starSigns"
            :key="s"
            type="button"
            class="ta-sign-card"
            :title="zodiacProfiles[s]?.personality || ''"
            @click="selectStar(s)"
          >
            <span class="ta-sign-element">{{ zodiacProfiles[s]?.element || "—" }}</span>
            <span class="ta-sign-name">{{ s }}</span>
            <span v-if="zodiacProfiles[s]" class="ta-sign-stats">
              HP {{ zodiacProfiles[s].startingHealth }} · F{{ zodiacProfiles[s].resources.food }}
              W{{ zodiacProfiles[s].resources.water }} T{{ zodiacProfiles[s].resources.tools }}
            </span>
          </button>
        </div>
      </div>

      <div v-else class="ta-play">
        <div
          v-if="loading"
          class="ta-loading-overlay"
          aria-busy="true"
          aria-live="polite"
        >
          <div class="ta-loading-card">
            <div class="ta-loading-spinner" aria-hidden="true" />
            <p class="ta-loading-title">The wasteland thinks…</p>
            <p class="ta-loading-tip" :key="loadingTipIndex">{{ loadingTips[loadingTipIndex] }}</p>
          </div>
        </div>

        <div class="ta-hud" aria-label="Survival status">
          <div class="ta-hud-item">
            <span class="ta-hud-label">Day</span>
            <span class="ta-hud-value">{{ playerState.day }}</span>
            <span v-if="isCataclysmDay" class="ta-hud-badge ta-hud-badge--danger">Cataclysm</span>
          </div>
          <div class="ta-hud-item">
            <span class="ta-hud-label">Health</span>
            <span class="ta-hud-value">{{ playerState.health }}</span>
          </div>
          <div class="ta-hud-item">
            <span class="ta-hud-label">Food</span>
            <span class="ta-hud-value">{{ playerState.resources.food }}</span>
          </div>
          <div class="ta-hud-item">
            <span class="ta-hud-label">Water</span>
            <span class="ta-hud-value">{{ playerState.resources.water }}</span>
          </div>
          <div class="ta-hud-item">
            <span class="ta-hud-label">Tools</span>
            <span class="ta-hud-value">{{ playerState.resources.tools }}</span>
          </div>
          <div class="ta-hud-item ta-hud-item--wide">
            <span class="ta-hud-label">Shelter</span>
            <span class="ta-hud-value">{{ playerState.shelter.durability }}</span>
          </div>
        </div>

        <p v-if="playerState.apocalypseTheme" class="ta-worldline">
          <span class="ta-worldline-label">World state</span>
          {{ playerState.apocalypseTheme }}
        </p>

        <div class="ta-toolbar">
          <button
            type="button"
            class="ta-btn ta-btn--ghost"
            @click="showInventory = !showInventory"
          >
            Backpack
            <span class="ta-muted">{{ playerState.inventory.length }}/{{ MAX_INVENTORY_SLOTS }}</span>
          </button>
          <span class="ta-toolbar-spacer" aria-hidden="true" />
          <button
            type="button"
            class="ta-btn ta-btn--ghost"
            title="Reset day, stats, and story; keep the same sign"
            @click="restartAdventure"
          >
            Restart adventure
          </button>
          <button
            type="button"
            class="ta-btn ta-btn--ghost"
            title="Return to sign selection"
            @click="reselectZodiac"
          >
            Reselect zodiac
          </button>
        </div>

        <div v-if="showInventory" class="ta-panel ta-inventory">
          <h3 class="ta-panel-title">Inventory</h3>
          <div v-if="playerState.inventory.length === 0" class="ta-empty">
            Your pack is empty. Explore to fill it.
          </div>
          <div v-else class="inventory-grid">
            <div
              v-for="(item, index) in playerState.inventory"
              :key="index"
              class="inventory-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-effect">
                <span v-if="item.food > 0">🍖+{{ item.food }}</span>
                <span v-if="item.water > 0">💧+{{ item.water }}</span>
                <span v-if="item.health > 0">❤️+{{ item.health }}</span>
                <span v-if="item.repair > 0">🔧+{{ item.repair }}</span>
              </span>
            </div>
          </div>
          <p v-if="playerState.inventory.length >= MAX_INVENTORY_SLOTS" class="inventory-full-warning">
            Backpack full ({{ MAX_INVENTORY_SLOTS }} items max).
          </p>
        </div>

        <section class="ta-narrative" aria-live="polite">
          <div class="ta-narrative-inner">
            <p class="ta-narrative-label">The story so far</p>

            <article class="ta-story-beat ta-story-beat--latest">
              <p class="ta-story-beat-label">Latest · {{ storyLatestLabel }}</p>
              <div class="event-text">
                <p v-html="currentEvent"></p>
              </div>
            </article>

            <div v-if="storyPastSnapshots.length" class="ta-story-earlier">
              <button
                type="button"
                class="ta-btn ta-btn--ghost ta-story-toggle"
                @click="expandedEarlierStories = !expandedEarlierStories"
              >
                {{
                  expandedEarlierStories
                    ? "Hide earlier story"
                    : `Show earlier story (${storyPastSnapshots.length})`
                }}
              </button>
              <transition name="ta-collapse">
                <div v-show="expandedEarlierStories" class="ta-story-earlier-list">
                  <article
                    v-for="beat in storyPastSnapshots"
                    :key="beat.id"
                    class="ta-story-beat ta-story-beat--past"
                  >
                    <p class="ta-story-beat-label">{{ beat.label }}</p>
                    <div class="event-text">
                      <p v-html="beat.html"></p>
                    </div>
                  </article>
                </div>
              </transition>
            </div>
          </div>
        </section>

        <div
          v-if="isCataclysmDay && !playerState.atShelter"
          class="ta-panel ta-panel--danger cataclysm-box"
        >
          <p class="ta-panel-lead"><strong>Cataclysm approaching</strong></p>
          <p class="ta-panel-copy">
            Return to shelter before the day ends. Resource drain is fivefold today.
          </p>
          <button type="button" class="ta-btn ta-btn--danger shelter-btn" @click="returnToShelter">
            Return to shelter
          </button>
        </div>

        <div
          v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal && !isCataclysmDay"
          class="ta-panel ta-panel--subtle fix-shelter-section"
        >
          <button
            type="button"
            class="ta-btn ta-btn--secondary fix-shelter-btn"
            :disabled="!hasRepairKit"
            @click="fixShelter"
          >
            Fix shelter
            <span class="ta-muted">({{ repairKitCount }} kits)</span>
          </button>
          <span class="fix-shelter-hint">Free action — does not spend your turn.</span>
        </div>

        <div v-if="warning" class="warning-box">
          <p v-html="warning"></p>
        </div>

        <div
          v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal"
          class="ta-command"
        >
          <label class="ta-command-label" for="action-input">Your command</label>
          <div class="input-section">
            <span class="ta-prompt" aria-hidden="true">&gt;</span>
            <input
              id="action-input"
              v-model="userInput"
              type="text"
              class="action-input"
              placeholder="Describe what you do…"
              autocomplete="off"
              :disabled="loading"
              @keyup.enter="submitAction"
            />
            <button
              type="button"
              class="ta-btn ta-btn--primary submit-btn"
              :disabled="loading"
              @click="submitAction"
            >
              {{ loading ? '…' : 'Enter' }}
            </button>
          </div>
        </div>

        <div
          v-if="playerState.health > 0 && playerState.day < 100 && !showRestModal && nextActions.length"
          class="ta-choices-wrap"
        >
          <p class="ta-choices-kicker">Or choose</p>
          <div class="actions">
            <button
              v-for="(a, i) in nextActions"
              :key="a"
              type="button"
              class="preset-btn"
              :disabled="loading"
              @click="takeAction(a)"
            >
              <span class="ta-choice-num">{{ i + 1 }}</span>
              <span class="ta-choice-text">{{ a }}</span>
            </button>
          </div>
        </div>

        <div
          v-if="playerState.health <= 0 || playerState.day >= 100"
          class="ta-gameover"
        >
          <button type="button" class="ta-btn ta-btn--danger ta-btn--wide" @click="restartGame">
            Play again
          </button>
        </div>
      </div>
    </div>

    <div v-if="showRestModal" class="modal-overlay" @click.self="cancelRest">
      <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="rest-title">
        <h3 id="rest-title" class="ta-modal-title">Rest & recover</h3>
        <p class="ta-modal-hint">Toggle supplies to consume; rest still advances the day.</p>
        <div class="rest-inventory">
          <div
            v-for="(item, index) in playerState.inventory"
            :key="index"
            class="rest-item"
            :class="{
              selected: selectedItems.includes(index),
              'repair-item': item.repair > 0
            }"
            @click="toggleItemSelection(index)"
          >
            <input
              type="checkbox"
              :checked="selectedItems.includes(index)"
              :disabled="item.repair > 0"
            />
            <span class="item-name">{{ item.name }}</span>
            <span class="item-effect">
              <span v-if="item.food > 0">🍖+{{ item.food }}</span>
              <span v-if="item.water > 0">💧+{{ item.water }}</span>
              <span v-if="item.health > 0">❤️+{{ item.health }}</span>
              <span v-if="item.repair > 0">🔧 (use Fix shelter)</span>
            </span>
          </div>
        </div>
        <div v-if="playerState.inventory.length === 0" class="no-items">
          Nothing to consume—you may still confirm rest to pass time.
        </div>
        <div class="modal-actions">
          <button type="button" class="ta-btn ta-btn--ghost cancel-btn" @click="cancelRest">
            Cancel
          </button>
          <button type="button" class="ta-btn ta-btn--primary confirm-btn" @click="confirmRest">
            Confirm rest
          </button>
        </div>
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
      zodiacProfiles: {},
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
        apocalypseTheme: null,
        zodiacElement: null,
        zodiacPersonality: null
      },
      currentEvent: "Please choose your Zodiac sign to begin.",
      nextActions: [],
      userInput: "",
      loading: false,
      warning: "",
      showRestModal: false,
      selectedItems: [],
      showInventory: false,
      MAX_INVENTORY_SLOTS: 10,
      storyPastSnapshots: [],
      expandedEarlierStories: false,
      storyLatestLabel: "Awakening",
      loadingTipIndex: 0,
      loadingTipTimer: null,
      loadingTips: [
        "If your health drops to 0, the run ends.",
        "Use “Restart adventure” to reset day and supplies while keeping the same zodiac.",
        "“Reselect zodiac” returns you to the sign selection screen.",
        "On cataclysm days, food and water drain much faster—get back to shelter if you can.",
        "Your backpack holds a limited number of items; use or abandon gear to make room.",
        "Fixing the shelter does not spend a turn if you have a repair kit.",
        "Typing a command and choosing a preset both advance the day—plan around daily hunger and thirst."
      ]
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
    },
    loading(isBusy) {
      const LOADING_TIP_MS = 5800;
      if (isBusy) {
        if (this.loadingTipTimer) clearInterval(this.loadingTipTimer);
        this.pickRandomLoadingTip();
        this.loadingTipTimer = setInterval(() => {
          this.pickRandomLoadingTip();
        }, LOADING_TIP_MS);
      } else if (this.loadingTipTimer) {
        clearInterval(this.loadingTipTimer);
        this.loadingTipTimer = null;
      }
    }
  },
  mounted() {
    this.loadZodiacProfiles();
  },
  beforeUnmount() {
    if (this.loadingTipTimer) {
      clearInterval(this.loadingTipTimer);
      this.loadingTipTimer = null;
    }
  },
  methods: {
    async loadZodiacProfiles() {
      try {
        const { data } = await axios.get("http://localhost:8000/api/zodiac-signs");
        const map = {};
        for (const row of data) {
          map[row.sign] = row;
        }
        this.zodiacProfiles = map;
      } catch (e) {
        console.warn("Zodiac API unavailable — selection will use fallback stats.", e);
      }
    },

    resetStoryArchive() {
      this.storyPastSnapshots = [];
      this.expandedEarlierStories = false;
      this.storyLatestLabel = "Awakening";
    },

    pickRandomLoadingTip() {
      const n = this.loadingTips.length;
      if (n <= 1) {
        this.loadingTipIndex = 0;
        return;
      }
      let next = this.loadingTipIndex;
      for (let i = 0; i < 12 && next === this.loadingTipIndex; i++) {
        next = Math.floor(Math.random() * n);
      }
      this.loadingTipIndex = next;
    },

    snapshotPreviousStoryBeat(label) {
      if (!this.playerState.starSign) return;
      const html = this.currentEvent;
      if (!html || html === "Please choose your Zodiac sign to begin.") return;
      const text =
        typeof label === "string" && label.length > 48 ? `${label.slice(0, 48)}…` : label || "Beat";
      this.storyPastSnapshots.push({
        id: `b-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        label: text,
        html
      });
      while (this.storyPastSnapshots.length > 4) {
        this.storyPastSnapshots.shift();
      }
    },

    applyStartingStateForSign(sign) {
      const p = this.zodiacProfiles[sign];
      this.playerState.shelter = {
        type: p?.shelterType || "Basic Shelter",
        durability: 100
      };
      this.playerState.resources = p?.resources
        ? { ...p.resources }
        : { food: 5, water: 5, tools: 3 };
      this.playerState.health = p?.startingHealth ?? 100;
      this.playerState.zodiacElement = p?.element ?? null;
      this.playerState.zodiacPersonality = p?.personality ?? null;
      this.playerState.inventory = [];
      this.playerState.atShelter = true;
      const theme =
        p?.apocalypse ||
        this.apocalypseThemes[sign] ||
        "An unknown cataclysm has ended the old world.";
      this.playerState.apocalypseTheme = theme;
      this.playerState.day = 1;
      this.playerState.actionCount = 0;
      this.playerState.history = [];
      this.playerState.longTermMemory = [];
      this.playerState.epicMemory = [];
    },

    openingNarrativeForSign(sign) {
      const p = this.zodiacProfiles[sign];
      const theme =
        p?.apocalypse ||
        this.apocalypseThemes[sign] ||
        "An unknown cataclysm has ended the old world.";
      const worldName = theme.includes(" - ") ? theme.split(" - ")[0] : theme.split(".")[0];
      const res = this.playerState.resources;
      const shelterLabel = (p?.shelterType || "shelter").toLowerCase();
      return (
        `Morning finds your <strong>${shelterLabel}</strong> at the edge of what’s left of the world. ` +
        `<strong>${worldName}</strong> has stripped the old maps bare. ` +
        `You tally supplies: <strong>${res.food} food</strong>, <strong>${res.water} water</strong>, ` +
        `<strong>${res.tools} tools</strong>; you estimate roughly <strong>${this.playerState.health}%</strong> vigor. ` +
        `The wasteland offers nothing for free—choose your next move.`
      );
    },

    selectStar(sign) {
      this.playerState.starSign = sign;
      this.applyStartingStateForSign(sign);
      this.resetStoryArchive();
      this.currentEvent = this.openingNarrativeForSign(sign);
      this.nextActions = ["Explore Ruins", "Search for Water", "Rest"];
      this.warning = "";
      console.log(`🎮 Game Started with ${sign}. Day initialized to: ${this.playerState.day}`);
    },

    restartAdventure() {
      const sign = this.playerState.starSign;
      if (!sign) return;
      this.applyStartingStateForSign(sign);
      this.resetStoryArchive();
      this.currentEvent = this.openingNarrativeForSign(sign);
      this.nextActions = ["Explore Ruins", "Search for Water", "Rest"];
      this.userInput = "";
      this.warning = "";
      this.showRestModal = false;
      this.selectedItems = [];
      this.showInventory = false;
    },

    reselectZodiac() {
      this.restartGame();
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
        apocalypseTheme: null,
        zodiacElement: null,
        zodiacPersonality: null
      };
      this.resetStoryArchive();
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
      this.snapshotPreviousStoryBeat(this.storyLatestLabel);

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
      this.storyLatestLabel = "Rest";
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

        this.snapshotPreviousStoryBeat(this.storyLatestLabel);

        // Apply daily consumption
        this.applyDailyConsumption();

        // CRITICAL: Increment day and force Vue reactivity
        this.playerState.day += 1;
        console.log(`✅ takeAction: Day updated to ${this.playerState.day}`);
        this.$nextTick(() => {
          console.log(`✅ Vue tick: Day is now ${this.playerState.day}`);
        });

        this.currentEvent = data.eventText;
        if (this.isCataclysmDay) {
          this.applyCataclysmEffects();
        }

        this.nextActions = data.nextActions || ["Explore Ruins", "Search for Water", "Rest"];

        this.checkGameOver();

        this.storyLatestLabel = action;

        this.playerState.history.push({
          action: action,
          result: this.currentEvent
        });
        if (this.playerState.history.length > 5) {
          this.playerState.history.shift();
        }

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
/* Classic parser + ink-on-parchment mood; fonts loaded in index.html */
.ta-page {
  --ta-bg: #0c0e0a;
  --ta-bg-elevated: #141812;
  --ta-border: rgba(201, 162, 39, 0.35);
  --ta-border-strong: rgba(201, 162, 39, 0.55);
  --ta-text: #e8e4dc;
  --ta-muted: #9a958a;
  --ta-accent: #c9a227;
  --ta-accent-dim: rgba(201, 162, 39, 0.2);
  --ta-green: #6a9f6e;
  --ta-green-dim: rgba(106, 159, 110, 0.18);
  --ta-red: #c94c4c;
  --ta-red-dim: rgba(201, 76, 76, 0.15);
  --ta-mono: 'JetBrains Mono', ui-monospace, monospace;
  --ta-serif: 'Crimson Pro', Georgia, serif;
  --ta-radius: 6px;
  --ta-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);

  min-height: 100vh;
  padding: clamp(1rem, 4vw, 2.5rem);
  font-family: var(--ta-serif);
  color: var(--ta-text);
  background:
    radial-gradient(ellipse 120% 80% at 50% -20%, rgba(201, 162, 39, 0.08), transparent 50%),
    var(--ta-bg);
  position: relative;
}

.ta-page::before {
  content: '';
  pointer-events: none;
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );
  z-index: 0;
}

.ta-shell {
  position: relative;
  z-index: 1;
  max-width: 44rem;
  margin: 0 auto;
  padding: clamp(1.25rem, 3vw, 2rem);
  background: var(--ta-bg-elevated);
  border: 1px solid var(--ta-border);
  border-radius: calc(var(--ta-radius) + 2px);
  box-shadow: var(--ta-shadow);
}

.ta-shell::before {
  content: '';
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(201, 162, 39, 0.12);
  border-radius: var(--ta-radius);
  pointer-events: none;
}

.ta-header {
  text-align: center;
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid rgba(201, 162, 39, 0.2);
}

.ta-kicker {
  font-family: var(--ta-mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ta-accent);
  margin: 0 0 0.5rem;
  opacity: 0.9;
}

.ta-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  font-size: clamp(1.5rem, 4vw, 2rem);
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 0.5rem;
  letter-spacing: 0.02em;
}

.ta-title-sign {
  font-family: var(--ta-mono);
  font-size: clamp(0.8rem, 2.2vw, 1rem);
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ta-accent);
}

.ta-sub {
  margin: 0;
  font-size: 1.05rem;
  color: var(--ta-muted);
  line-height: 1.45;
}

.ta-block {
  position: relative;
  z-index: 1;
}

.ta-section-label {
  font-family: var(--ta-mono);
  font-size: 0.75rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ta-muted);
  margin: 0 0 0.35rem;
  text-align: center;
}

.ta-lead {
  text-align: center;
  margin: 0 0 1.25rem;
  font-size: 1.15rem;
  color: var(--ta-text);
}

.ta-sign-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(7.5rem, 1fr));
  gap: 0.65rem;
}

.ta-sign-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.35rem;
  text-align: left;
  font-family: var(--ta-serif);
  font-size: 0.95rem;
  font-weight: 600;
  padding: 0.7rem 0.55rem;
  margin: 0;
  border-radius: var(--ta-radius);
  border: 1px solid var(--ta-border);
  background: rgba(20, 24, 18, 0.85);
  color: var(--ta-text);
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    transform 0.12s ease;
}

.ta-sign-element {
  font-family: var(--ta-mono);
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ta-accent);
}

.ta-sign-name {
  font-size: 1rem;
  line-height: 1.2;
}

.ta-sign-stats {
  font-family: var(--ta-mono);
  font-size: 0.62rem;
  font-weight: 500;
  color: var(--ta-muted);
  line-height: 1.3;
}

.ta-sign-card:hover {
  border-color: var(--ta-accent);
  background: var(--ta-accent-dim);
  transform: translateY(-1px);
}

.ta-sign-card:focus-visible {
  outline: 2px solid var(--ta-accent);
  outline-offset: 2px;
}

.ta-play {
  position: relative;
  z-index: 1;
}

.ta-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(7, 8, 6, 0.78);
  backdrop-filter: blur(6px);
  border-radius: var(--ta-radius);
  padding: 1rem;
}

.ta-loading-card {
  text-align: center;
  max-width: 22rem;
  padding: 1.25rem 1.5rem;
  border: 1px solid var(--ta-border);
  border-radius: var(--ta-radius);
  background: var(--ta-bg-elevated);
  box-shadow: var(--ta-shadow);
}

.ta-loading-spinner {
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto 1rem;
  border: 3px solid rgba(201, 162, 39, 0.22);
  border-top-color: var(--ta-accent);
  border-radius: 50%;
  animation: ta-spin 0.8s linear infinite;
}

@keyframes ta-spin {
  to {
    transform: rotate(360deg);
  }
}

.ta-loading-title {
  font-family: var(--ta-serif);
  font-size: 1.12rem;
  margin: 0 0 0.65rem;
}

.ta-loading-tip {
  font-family: var(--ta-mono);
  font-size: 0.74rem;
  line-height: 1.55;
  color: var(--ta-muted);
  margin: 0;
  min-height: 3.25rem;
}

.ta-hud {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(5.5rem, 1fr));
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.ta-hud-item {
  font-family: var(--ta-mono);
  font-size: 0.72rem;
  padding: 0.55rem 0.6rem;
  border-radius: var(--ta-radius);
  border: 1px solid rgba(154, 149, 138, 0.25);
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.5rem;
}

.ta-hud-item--wide {
  grid-column: 1 / -1;
}

.ta-hud-label {
  color: var(--ta-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  width: 100%;
}

.ta-hud-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ta-text);
}

.ta-hud-badge {
  font-size: 0.65rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ta-hud-badge--danger {
  background: var(--ta-red-dim);
  color: #f0a8a8;
  animation: ta-pulse 1.2s ease-in-out infinite;
}

@keyframes ta-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.65;
  }
}

.ta-worldline {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  font-size: 0.98rem;
  font-style: italic;
  line-height: 1.5;
  color: #dcc8a8;
  border-left: 3px solid var(--ta-accent);
  background: rgba(201, 162, 39, 0.06);
  border-radius: 0 var(--ta-radius) var(--ta-radius) 0;
}

.ta-worldline-label {
  font-family: var(--ta-mono);
  font-size: 0.65rem;
  font-style: normal;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--ta-accent);
  display: block;
  margin-bottom: 0.35rem;
}

.ta-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.ta-toolbar-spacer {
  flex: 1;
  min-width: 0.75rem;
}

.ta-btn {
  font-family: var(--ta-mono);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.55rem 1rem;
  margin: 0;
  border-radius: var(--ta-radius);
  border: 1px solid transparent;
  cursor: pointer;
  color: var(--ta-text);
  background: rgba(255, 255, 255, 0.06);
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    opacity 0.15s ease;
}

.ta-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ta-btn--primary {
  background: var(--ta-green-dim);
  border-color: rgba(106, 159, 110, 0.45);
  color: #c8e6ca;
}

.ta-btn--primary:hover:not(:disabled) {
  background: rgba(106, 159, 110, 0.28);
  border-color: var(--ta-green);
}

.ta-btn--ghost {
  border-color: var(--ta-border);
  background: transparent;
}

.ta-btn--ghost:hover:not(:disabled) {
  border-color: var(--ta-border-strong);
  background: var(--ta-accent-dim);
}

.ta-btn--secondary {
  background: rgba(100, 149, 200, 0.12);
  border-color: rgba(100, 149, 200, 0.35);
  color: #b8d0ee;
}

.ta-btn--secondary:hover:not(:disabled) {
  background: rgba(100, 149, 200, 0.22);
}

.ta-btn--danger {
  background: var(--ta-red-dim);
  border-color: rgba(201, 76, 76, 0.45);
  color: #f0c4c4;
}

.ta-btn--danger:hover:not(:disabled) {
  background: rgba(201, 76, 76, 0.28);
}

.ta-btn--wide {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
}

.ta-muted {
  opacity: 0.75;
  font-weight: 400;
  margin-left: 0.35rem;
}

.ta-panel {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: var(--ta-radius);
  border: 1px solid var(--ta-border);
  background: rgba(0, 0, 0, 0.18);
  animation: ta-slide 0.28s ease-out;
}

.ta-panel--danger {
  border-color: rgba(201, 76, 76, 0.5);
  background: var(--ta-red-dim);
  text-align: center;
}

.ta-panel--subtle {
  border-color: rgba(100, 149, 200, 0.25);
  background: rgba(100, 149, 200, 0.06);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
}

.ta-panel-title {
  font-family: var(--ta-mono);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 0 0 0.75rem;
  color: var(--ta-muted);
}

.ta-panel-lead {
  margin: 0 0 0.35rem;
  font-size: 1.1rem;
}

.ta-panel-copy {
  margin: 0 0 1rem;
  font-size: 0.98rem;
  opacity: 0.92;
  line-height: 1.5;
}

.ta-inventory .ta-panel-title {
  color: #a8c9aa;
}

@keyframes ta-slide {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ta-empty {
  color: var(--ta-muted);
  font-style: italic;
  font-size: 0.98rem;
}

.inventory-full-warning {
  margin: 0.75rem 0 0;
  padding: 0.6rem 0.75rem;
  font-family: var(--ta-mono);
  font-size: 0.72rem;
  background: var(--ta-accent-dim);
  border: 1px solid rgba(201, 162, 39, 0.35);
  border-radius: var(--ta-radius);
  color: #e8d9a8;
}

.inventory-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.inventory-item {
  display: flex;
  flex-direction: column;
  padding: 0.55rem 0.75rem;
  background: rgba(106, 159, 110, 0.1);
  border: 1px solid rgba(106, 159, 110, 0.35);
  border-radius: var(--ta-radius);
  font-family: var(--ta-mono);
  font-size: 0.72rem;
}

.item-name {
  font-weight: 600;
  color: var(--ta-text);
  font-size: 0.8rem;
}

.item-effect {
  color: var(--ta-muted);
  margin-top: 0.25rem;
}

.item-effect span {
  margin-right: 0.35rem;
}

.cataclysm-box .shelter-btn {
  margin-top: 0;
}

.fix-shelter-section .fix-shelter-btn {
  margin: 0;
}

.fix-shelter-hint {
  font-size: 0.85rem;
  color: var(--ta-muted);
  font-style: italic;
}

.ta-narrative {
  margin-bottom: 1.25rem;
  border: 1px solid var(--ta-border);
  border-radius: var(--ta-radius);
  background: linear-gradient(165deg, rgba(48, 42, 34, 0.5) 0%, rgba(20, 24, 18, 0.9) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.ta-narrative-inner {
  padding: 1rem 1.1rem 1.15rem;
}

.ta-narrative-label {
  font-family: var(--ta-mono);
  font-size: 0.65rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ta-accent);
  margin: 0 0 0.6rem;
}

.ta-story-beat {
  margin-bottom: 0.85rem;
}

.ta-story-beat--latest {
  padding-bottom: 0.65rem;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid rgba(201, 162, 39, 0.18);
}

.ta-story-beat-label {
  font-family: var(--ta-mono);
  font-size: 0.66rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ta-muted);
  margin: 0 0 0.45rem;
}

.ta-story-beat--past .event-text {
  font-size: 0.98rem;
  line-height: 1.58;
  color: #e4dfd6;
}

.ta-story-beat--past .event-text :deep(strong) {
  color: #ebe4d4;
}

.ta-story-earlier {
  margin-top: 0.15rem;
}

.ta-story-toggle {
  width: 100%;
  justify-content: center;
  margin-bottom: 0.45rem;
}

.ta-story-earlier-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: min(55vh, 28rem);
  overflow-y: auto;
  padding-right: 0.2rem;
}

.ta-collapse-enter-active,
.ta-collapse-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.ta-collapse-enter-from,
.ta-collapse-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.event-text {
  margin: 0;
  padding: 0;
  min-height: 3.5rem;
  font-size: 1.08rem;
  line-height: 1.65;
  color: #f0ebe3;
}

.event-text :deep(p) {
  margin: 0;
}

.event-text :deep(strong) {
  color: #f5ecd4;
  font-weight: 700;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 6, 4, 0.72);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--ta-bg-elevated);
  border: 1px solid var(--ta-border-strong);
  border-radius: calc(var(--ta-radius) + 4px);
  padding: 1.25rem 1.35rem;
  max-width: 28rem;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--ta-shadow);
}

.ta-modal-title {
  font-family: var(--ta-serif);
  font-size: 1.35rem;
  margin: 0 0 0.35rem;
}

.ta-modal-hint {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  color: var(--ta-muted);
  line-height: 1.45;
}

.rest-inventory {
  margin: 0 0 0.5rem;
  max-height: 16rem;
  overflow-y: auto;
}

.rest-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 0.75rem;
  margin: 0.35rem 0;
  border-radius: var(--ta-radius);
  border: 1px solid rgba(154, 149, 138, 0.2);
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  font-family: var(--ta-mono);
  font-size: 0.78rem;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.rest-item:hover {
  border-color: var(--ta-border);
}

.rest-item.selected {
  border-color: var(--ta-green);
  background: var(--ta-green-dim);
}

.rest-item.repair-item {
  border-style: dashed;
  border-color: rgba(100, 149, 200, 0.4);
  cursor: not-allowed;
  opacity: 0.65;
}

.rest-item input[type='checkbox'] {
  pointer-events: none;
  accent-color: var(--ta-green);
}

.no-items {
  color: var(--ta-muted);
  font-style: italic;
  text-align: center;
  padding: 1rem;
  font-size: 0.95rem;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.modal-actions .ta-btn {
  min-width: 6.5rem;
}

.ta-command {
  margin-bottom: 1rem;
}

.ta-command-label {
  font-family: var(--ta-mono);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ta-muted);
  display: block;
  margin-bottom: 0.4rem;
}

.input-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ta-prompt {
  font-family: var(--ta-mono);
  font-weight: 600;
  color: var(--ta-accent);
  flex-shrink: 0;
}

.action-input {
  flex: 1;
  min-width: 0;
  font-family: var(--ta-mono);
  font-size: 0.88rem;
  padding: 0.65rem 0.85rem;
  border-radius: var(--ta-radius);
  border: 1px solid var(--ta-border);
  background: rgba(0, 0, 0, 0.35);
  color: var(--ta-text);
}

.action-input::placeholder {
  color: rgba(154, 149, 138, 0.65);
}

.action-input:focus {
  outline: none;
  border-color: var(--ta-accent);
  box-shadow: 0 0 0 2px var(--ta-accent-dim);
}

.action-input:disabled {
  opacity: 0.55;
}

.submit-btn {
  flex-shrink: 0;
}

.ta-choices-wrap {
  margin-bottom: 1.25rem;
}

.ta-choices-kicker {
  font-family: var(--ta-mono);
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ta-muted);
  margin: 0 0 0.5rem;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.preset-btn {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  width: 100%;
  text-align: left;
  font-family: var(--ta-serif);
  font-size: 1.02rem;
  font-weight: 500;
  padding: 0.7rem 0.9rem;
  margin: 0;
  border-radius: var(--ta-radius);
  border: 1px solid rgba(100, 149, 200, 0.35);
  background: rgba(100, 149, 200, 0.08);
  color: #dbe8f7;
  cursor: pointer;
  line-height: 1.4;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.preset-btn:hover:not(:disabled) {
  border-color: rgba(147, 190, 230, 0.65);
  background: rgba(100, 149, 200, 0.18);
}

.preset-btn:focus-visible {
  outline: 2px solid var(--ta-accent);
  outline-offset: 2px;
}

.ta-choice-num {
  font-family: var(--ta-mono);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--ta-accent);
  min-width: 1.25rem;
  padding-top: 0.2rem;
}

.ta-choice-text {
  flex: 1;
}

.ta-gameover {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--ta-border);
}

.warning-box {
  margin: 0 0 1rem;
  padding: 0.85rem 1rem;
  font-size: 0.98rem;
  line-height: 1.55;
  color: #e8dcc8;
  background: var(--ta-accent-dim);
  border: 1px solid rgba(201, 162, 39, 0.4);
  border-radius: var(--ta-radius);
}

.warning-box :deep(p) {
  margin: 0;
}

.warning-box :deep(strong) {
  color: #fff4dd;
}
</style>