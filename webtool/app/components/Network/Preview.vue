<template>
  <div
    ref="container"
    class="w-full h-full min-h-0 rounded-md overflow-hidden border border-default"
  />
</template>

<script setup lang="ts">
import type { Core, ElementDefinition } from 'cytoscape'
import { shortHash, hashId } from '~/composables/useHash'
import type { TopologyPeer } from '~/composables/useNetworkTopology'

const props = withDefaults(defineProps<{
  peers: TopologyPeer[]
  highlight?: string | null
  fingers?: string[]
  imageCounts?: ReadonlyMap<string, number>
}>(), { highlight: null, fingers: () => [], imageCounts: () => new Map() })

const emit = defineEmits<{
  (e: 'select', peerId: string | null): void
}>()

const container = ref<HTMLElement | null>(null)
let cy: Core | null = null

function imageBadge(count: number | undefined): string {
  const text = count === undefined ? '?' : String(count)
  const width = 30 + text.length * 14
  // Lucide's image icon, rendered with the count as a Cytoscape node background.
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="24" viewBox="0 0 ${width} 24"><g fill="none" stroke="white" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15l-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></g><text x="30" y="18" fill="white" font-family="sans-serif" font-size="18">${text}</text></svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

// Peers that are referenced but not (yet) registered are shown as "unknown".
function buildElements(peers: TopologyPeer[], highlight: string | null, fingers: string[]): ElementDefinition[] {
  const nodes = new Map<string, ElementDefinition>()
  const edges = new Map<string, ElementDefinition>()

  const addNode = (peerId: string, known: boolean) => {
    const label = `${peerId}\n${shortHash(peerId)}`
    const existing = nodes.get(peerId)
    if (existing && !known) return
    nodes.set(peerId, {
      group: 'nodes',
      data: { id: peerId, label, hash: hashId(peerId), imageBadge: imageBadge(props.imageCounts.get(peerId)) },
      classes: known ? '' : 'unknown'
    })
  }
  const addEdge = (peerId: string, neighborId: string, relation: 'successor' | 'predecessor' | 'finger') => {
    const id = `${peerId}->${neighborId}:${relation}`
    edges.set(id, {
      group: 'edges',
      data: { id, source: peerId, target: neighborId },
      classes: relation
    })
  }

  for (const p of peers) addNode(p.peerId, true)
  for (const p of peers) {
    if (p.successor) {
      addNode(p.successor, false)
      addEdge(p.peerId, p.successor, 'successor')
    }
    if (p.predecessor) {
      addNode(p.predecessor, false)
      addEdge(p.peerId, p.predecessor, 'predecessor')
    }
  }
  if (highlight && fingers.length) {
    addNode(highlight, peers.some(p => p.peerId === highlight))
    for (const finger of fingers) {
      addNode(finger, false)
      addEdge(highlight, finger, 'finger')
    }
  }
  return [...nodes.values(), ...edges.values()]
}

// ordered by hash (hex: 0-9 < a-f).
function ringLayout() {
  const sorted = cy!.nodes().toArray().sort((a, b) => {
    const x = a.data('hash') as string
    const y = b.data('hash') as string
    return x < y ? -1 : x > y ? 1 : 0
  })
  const index = new Map(sorted.map((n, i) => [n.id(), i]))
  const radius = Math.max(120, sorted.length * 20)
  return {
    name: 'preset',
    animate: true,
    animationDuration: 300,
    fit: true,
    padding: 40,
    positions: (n: { id: () => string }) => {
      const theta = -Math.PI / 2 + 2 * Math.PI * (index.get(n.id()) ?? 0) / sorted.length
      return { x: radius * Math.cos(theta), y: radius * Math.sin(theta) }
    }
  }
}

// Diff against the current graph so existing nodes keep their state and animate.
function sync() {
  if (!cy) return
  const elements = buildElements(props.peers, props.highlight, props.fingers)
  const wanted = new Set(elements.map(e => e.data.id as string))
  let changed = false

  cy.batch(() => {
    cy!.elements().filter(el => !wanted.has(el.id())).forEach((el) => {
      el.remove()
      changed = true
    })
    for (const def of elements) {
      const existing = cy!.getElementById(def.data.id as string)
      if (existing.empty()) {
        cy!.add(def)
        changed = true
      } else if (def.group === 'nodes') {
        existing.data(def.data)
        existing.classes(def.classes ?? '')
      }
    }
  })

  if (changed) cy.layout(ringLayout()).run()
  applyHighlight()
}

function applyHighlight() {
  if (!cy) return
  cy.nodes().removeClass('highlight')
  if (props.highlight) cy.getElementById(props.highlight).addClass('highlight')
}

onMounted(async () => {
  const cytoscape = (await import('cytoscape')).default
  if (!container.value) return

  cy = cytoscape({
    container: container.value,
    elements: buildElements(props.peers, props.highlight, props.fingers),
    minZoom: 0.3,
    maxZoom: 3,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-wrap': 'wrap',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-margin-y': -8,
          'font-size': 10,
          'color': '#fff',
          'background-color': '#16a34a',
          'background-image': 'data(imageBadge)',
          'background-width': 40,
          'background-height': 14,
          'background-position-y': '84%',
          'width': 64,
          'height': 64
        }
      },
      {
        selector: 'node.unknown',
        style: { 'background-color': '#6b7280', 'border-style': 'dashed', 'border-width': 2, 'border-color': '#d1d5db' }
      },
      { selector: 'node.highlight', style: { 'border-width': 4, 'border-color': '#f59e0b' } },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#9ca3af',
          'target-arrow-color': '#9ca3af',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'control-point-step-size': 40
        }
      },
      { selector: 'edge.finger', style: { 'line-color': '#3b82f6', 'target-arrow-color': '#3b82f6' } }
    ]
  })

  cy.on('tap', 'node', evt => emit('select', evt.target.id()))
  cy.on('tap', (evt) => {
    if (evt.target === cy) emit('select', null)
  })
  cy.layout(ringLayout()).run()
  applyHighlight()
})

watch([() => props.peers, () => props.highlight, () => props.fingers, () => props.imageCounts], sync)

onBeforeUnmount(() => {
  cy?.destroy()
  cy = null
})
</script>
