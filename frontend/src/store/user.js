import { defineStore } from 'pinia';

const defaultProfile = {
  age: 25,
  gender: 'male',
  height: 170,
  weight: 65,
  activity_level: 'sedentary',
  goal: 'muscle_gain', // muscle_gain, weight_loss, healthy_eat
  health_conditions: []
};

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: { ...defaultProfile, ...uni.getStorageSync('user_profile') },
    history: uni.getStorageSync('diet_history') || []
  }),
  getters: {
    weeklyStats: (state) => {
      const days = [];
      const now = new Date();

      // Generate last 7 days
      for (let i = 6; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        // Handle timezone offset simply by using local date strings for comparison if needed,
        // but toISOString is UTC. Let's use local date components for simplicity in this context
        // as the app seems local-first.
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;
        const label = `${d.getMonth() + 1}/${d.getDate()}`;
        days.push({ fullDate: dateStr, label, calories: 0 });
      }

      // Aggregate history
      state.history.forEach(entry => {
        // Assuming timestamp is ISO string, we need to convert to local date string to match
        const entryTime = new Date(entry.timestamp);
        const year = entryTime.getFullYear();
        const month = String(entryTime.getMonth() + 1).padStart(2, '0');
        const day = String(entryTime.getDate()).padStart(2, '0');
        const entryDateStr = `${year}-${month}-${day}`;

        const dayStat = days.find(d => d.fullDate === entryDateStr);
        if (dayStat && entry.result) {
          if (entry.result.total_calories) {
             dayStat.calories += (parseInt(entry.result.total_calories) || 0);
          } else if (entry.result.items) {
             entry.result.items.forEach(item => {
               dayStat.calories += (parseInt(item.calories) || 0);
             });
          }
        }
      });
      return days;
    }
  },
  actions: {
    updateProfile(newProfile) {
      this.profile = { ...this.profile, ...newProfile };
      uni.setStorageSync('user_profile', this.profile);
    },
    addHistoryEntry(entry) {
      const newEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        ...entry
      };
      this.history.unshift(newEntry);
      // Keep only last 50 entries
      if (this.history.length > 50) {
        this.history.pop();
      }
      uni.setStorageSync('diet_history', this.history);
    },
    clearHistory() {
      this.history = [];
      uni.setStorageSync('diet_history', []);
    },
    deleteHistoryEntry(id) {
      const index = this.history.findIndex(entry => entry.id === id);
      if (index !== -1) {
        this.history.splice(index, 1);
        uni.setStorageSync('diet_history', this.history);
      }
    }
  }
});
