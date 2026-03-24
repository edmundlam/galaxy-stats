<!-- src/components/dashboard/CardTable.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue';
import type { CardStats } from '../../utils/event-stats';

interface Props {
  stats: CardStats[];
  initialLimit?: number;
}

const props = withDefaults(defineProps<Props>(), {
  initialLimit: 10,
});

const expanded = ref(false);
const searchQuery = ref('');
const sortColumn = ref<'name' | 'count' | 'percentage'>('count');
const sortDirection = ref<'asc' | 'desc'>('desc');

// Filter by search query
const filteredStats = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.stats;
  }

  const query = searchQuery.value.toLowerCase();
  return props.stats.filter(s =>
    s.name.toLowerCase().includes(query) ||
    s.slug.toLowerCase().includes(query)
  );
});

// Sort by column
const sortedStats = computed(() => {
  const stats = [...filteredStats.value];
  stats.sort((a, b) => {
    let aVal: string | number;
    let bVal: string | number;

    switch (sortColumn.value) {
      case 'name':
        aVal = a.name;
        bVal = b.name;
        break;
      case 'count':
        aVal = a.count;
        bVal = b.count;
        break;
      case 'percentage':
        aVal = a.percentage;
        bVal = b.percentage;
        break;
    }

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    return sortDirection.value === 'asc'
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number);
  });

  return stats;
});

// Apply limit unless expanded
const displayStats = computed(() => {
  return expanded.value ? sortedStats.value : sortedStats.value.slice(0, props.initialLimit);
});

// Toggle sort
function handleSort(column: 'name' | 'count' | 'percentage') {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortDirection.value = 'desc';
  }
}

// Get sort class for header
function getSortClass(column: 'name' | 'count' | 'percentage'): string {
  if (sortColumn.value !== column) {
    return 'sortable';
  }

  return sortDirection.value === 'asc' ? 'sortable asc' : 'sortable desc';
}

// Toggle expanded state
function toggleExpanded() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <div class="dashboard-section">
    <h2 class="dashboard-section__title">Most Played Cards</h2>

    <input
      v-model="searchQuery"
      type="text"
      placeholder="Search cards..."
      class="table-search"
    />

    <table class="data-table">
      <thead>
        <tr>
          <th
            :class="getSortClass('name')"
            @click="handleSort('name')"
          >
            Card Name
          </th>
          <th
            :class="getSortClass('count')"
            @click="handleSort('count')"
          >
            Count
          </th>
          <th
            :class="getSortClass('percentage')"
            @click="handleSort('percentage')"
          >
            Percentage
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="card in displayStats" :key="card.slug">
          <td>{{ card.name }}</td>
          <td>{{ card.count }}</td>
          <td data-col="percentage">{{ card.percentage.toFixed(2) }}%</td>
        </tr>
      </tbody>
    </table>

    <button
      v-if="sortedStats.length > initialLimit"
      class="expand-button"
      @click="toggleExpanded"
    >
      {{ expanded ? 'Show Less' : `Show All ${sortedStats.length} Cards` }}
    </button>
  </div>
</template>
