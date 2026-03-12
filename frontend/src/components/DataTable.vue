<template>
  <div>
    <!-- Search and toolbar -->
    <div v-if="searchable || $slots.toolbar" class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div v-if="searchable" class="relative max-w-xs flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          :value="searchQuery"
          @input="$emit('update:searchQuery', $event.target.value)"
          type="text"
          :placeholder="searchPlaceholder"
          class="input-field pl-9"
        />
      </div>
      <div class="flex items-center gap-2">
        <slot name="toolbar" />
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-slate-100 bg-slate-50/70">
            <th
              v-for="col in columns"
              :key="col.key"
              class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500"
              :class="col.class"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="(row, idx) in paginatedData"
            :key="row.id || idx"
            class="transition hover:bg-slate-50/50"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              class="whitespace-nowrap px-4 py-3 text-slate-700"
              :class="col.cellClass"
            >
              <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
                {{ row[col.key] }}
              </slot>
            </td>
          </tr>
          <tr v-if="!paginatedData.length">
            <td :colspan="columns.length" class="px-4 py-12 text-center">
              <slot name="empty">
                <EmptyState :title="emptyTitle" :message="emptyMessage" />
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="mt-4 flex items-center justify-between text-sm text-slate-500">
      <span>{{ paginationLabel }}</span>
      <div class="flex items-center gap-1">
        <button
          @click="currentPage > 1 && $emit('update:page', currentPage - 1)"
          :disabled="currentPage <= 1"
          class="btn-icon disabled:opacity-30"
        >
          <ChevronLeft class="h-4 w-4" />
        </button>
        <template v-for="p in pageNumbers" :key="p">
          <button
            v-if="p !== '...'"
            @click="$emit('update:page', p)"
            :class="p === currentPage ? 'bg-primary-600 text-white' : 'hover:bg-slate-100 text-slate-700'"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-medium transition"
          >
            {{ p }}
          </button>
          <span v-else class="px-1 text-slate-400">...</span>
        </template>
        <button
          @click="currentPage < totalPages && $emit('update:page', currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="btn-icon disabled:opacity-30"
        >
          <ChevronRight class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Search, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  columns: { type: Array, required: true },
  data: { type: Array, required: true },
  searchable: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  searchPlaceholder: { type: String, default: 'Search...' },
  pageSize: { type: Number, default: 10 },
  page: { type: Number, default: 1 },
  emptyTitle: { type: String, default: 'No records found' },
  emptyMessage: { type: String, default: '' },
})

defineEmits(['update:searchQuery', 'update:page'])

const currentPage = computed(() => props.page)

const totalPages = computed(() => Math.max(1, Math.ceil(props.data.length / props.pageSize)))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  return props.data.slice(start, start + props.pageSize)
})

const paginationLabel = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize + 1
  const end = Math.min(currentPage.value * props.pageSize, props.data.length)
  return `Showing ${start}-${end} of ${props.data.length}`
})

const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  pages.push(1)
  if (cur > 3) pages.push('...')
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
  if (cur < total - 2) pages.push('...')
  pages.push(total)
  return pages
})
</script>
