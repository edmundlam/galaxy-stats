<!-- src/components/dashboard/CaptainChart.vue -->
<script setup lang="ts">
import { computed } from 'vue';
import type { CaptainStats } from '../../utils/event-stats';

interface Props {
  stats: CaptainStats[];
  limit?: number;
}

const props = withDefaults(defineProps<Props>(), {
  limit: 10,
});

// Get top N captains
const topCaptains = computed(() => props.stats.slice(0, props.limit));

// Find max count for scaling bars
const maxCount = computed(() =>
  Math.max(...topCaptains.value.map(s => s.count))
);
</script>

<template>
  <div class="dashboard-section">
    <h2 class="dashboard-section__title">Top {{ limit }} Captains by Usage</h2>
    <div class="chart">
      <div
        v-for="captain in topCaptains"
        :key="captain.slug"
        class="chart-bar"
      >
        <div class="chart-bar__label" :title="captain.name">
          {{ captain.name }}
        </div>
        <div class="chart-bar__track">
          <div
            class="chart-bar__fill"
            :style="{ width: `${(captain.count / maxCount) * 100}%` }"
          >
            <span class="chart-bar__value">{{ captain.count }} ({{ captain.percentage.toFixed(1) }}%)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
  import '../../styles/dashboard.css';
</style>
