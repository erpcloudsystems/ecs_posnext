<template>
  <p style="margin: 0;" v-if="formattedTime">{{ formattedTime }}</p>
  <!-- <p v-if="soType">{{ soType }}</p> -->
</template>

<script>
export default {
props: {
  inputTime: {
    type: Number,
    required: true,
  },
  id: { type: String, required: true },
  // inputSoType: {
  //   type: String,
  //   required: true,
  // },
},
data() {
  return {
    timeInSeconds: this.inputTime,
    // soType: this.inputSoType,
  };
},
computed: {
  formattedTime() {
    const hours = Math.floor(this.timeInSeconds / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((this.timeInSeconds % 3600) / 60).toString().padStart(2, '0');
    const seconds = (this.timeInSeconds % 60).toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  },
  
},
watch: {
  // Watch for changes to inputTime prop and update the countdown timer accordingly
  inputTime(newTime) {
    this.timeInSeconds = newTime;
    this.startCountdown(); // Restart countdown when inputTime changes
  },
},
methods: {
  startCountdown() {
    // if (this.timeInSeconds <= 0) return;
    
        
        const countdownInterval = setInterval(() => {
            this.timeInSeconds--;
          
        }, 1000); // Update every second
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
        if(remainingTime)
          this.timeInSeconds = remainingTime;
      }
},
},
beforeDestroy() {
this.saveTime();
clearInterval(this.timeInSeconds);
},
created() {
  this.loadTime();
  // Start countdown immediately when the component is created
  this.startCountdown();
},
mounted() {
  window.addEventListener("online", this.saveTime);
  window.addEventListener("offline", this.saveTime);
  window.addEventListener("beforeunload", this.saveTime);
},
};
</script>
