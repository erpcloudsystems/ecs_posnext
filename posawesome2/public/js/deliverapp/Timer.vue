<template>
  <p style="margin: 0;" v-if="formattedTime">{{ formattedTime }}</p>
</template>

<script>
export default {
  props: {
    inputTime: {
      type: Number,
      required: true,
    },
    id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      timeInSeconds: this.inputTime,
      countdownInterval: null,
    };
  },
  computed: {
    formattedTime() {
      const hours = Math.floor(Math.abs(this.timeInSeconds) / 3600)
        .toString()
        .padStart(2, "0");
      const minutes = Math.floor((Math.abs(this.timeInSeconds) % 3600) / 60)
        .toString()
        .padStart(2, "0");
      const seconds = (Math.abs(this.timeInSeconds) % 60)
        .toString()
        .padStart(2, "0");
      const prefix = this.timeInSeconds < 0 ? "-" : "";
      return `${prefix}${hours}:${minutes}:${seconds}`;
    },
  },
  watch: {
    inputTime(newTime) {
      this.timeInSeconds = newTime;
      this.restartCountdown();
    },
  },
  methods: {
    startCountdown() {
      this.stopCountdown(); // Ensure no duplicate intervals
      this.countdownInterval = setInterval(() => {
        if (this.timeInSeconds === 0) {
          // Optional: Stop timer at zero (remove if negative time is needed)
          this.stopCountdown();
        }
        this.timeInSeconds--;
      }, 1000);
    },
    stopCountdown() {
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
      }
    },
    saveTime() {
      localStorage.setItem(
        `timer_${this.id}`,
        JSON.stringify({ remainingTime: this.timeInSeconds })
      );
    },
    loadTime() {
      const savedTime = localStorage.getItem(`timer_${this.id}`);
      if (savedTime) {
        const { remainingTime } = JSON.parse(savedTime);
        this.timeInSeconds = remainingTime || this.inputTime;
      }
    },
    restartCountdown() {
      this.stopCountdown();
      this.startCountdown();
    },
  },
  created() {
    this.loadTime();
    this.startCountdown();
  },
  mounted() {
    window.addEventListener("online", this.saveTime);
    window.addEventListener("offline", this.saveTime);
    window.addEventListener("beforeunload", this.saveTime);
  },
  beforeDestroy() {
    this.saveTime();
    this.stopCountdown();
    window.removeEventListener("online", this.saveTime);
    window.removeEventListener("offline", this.saveTime);
    window.removeEventListener("beforeunload", this.saveTime);
  },
};
</script>
