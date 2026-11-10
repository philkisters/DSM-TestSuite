import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { runInNewContext } from 'node:vm'
import { compileScript, parse } from '@vue/compiler-sfc'
import ts from 'typescript'
import * as vue from 'vue'
import { sumPlaces } from '../app/utils/groupChallengeOverview.ts'

test('place totals sum all three categories, including zeroes', () => {
  assert.equal(sumPlaces({ time: 2, duration: 3, messages: 4 }), 9)
  assert.equal(sumPlaces({ time: 0, duration: 0, messages: 0 }), 0)
})

test('summary loads, renders counts, reports errors and ignores stale requests', async () => {
  const pending = new Map()
  const getOverview = id => new Promise((resolve, reject) => pending.set(id, { resolve, reject }))
  const source = readFileSync(new URL('../app/components/Group/ChallengeSummary.vue', import.meta.url), 'utf8')
  const descriptor = parse(source).descriptor
  const compiled = compileScript(descriptor, { id: 'group-summary', inlineTemplate: true }).content
  const javascript = ts.transpileModule(compiled, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText
  const exports = {}
  const modules = {
    vue,
    '~~/app/services/backend/group.service': { getGroupChallengeOverview: getOverview },
    '~~/app/utils/groupChallengeOverview': { sumPlaces }
  }
  runInNewContext(javascript, {
    exports,
    Error,
    require: (name) => {
      assert.ok(name in modules, `Unexpected import: ${name}`)
      return modules[name]
    }
  })

  const renderer = vue.createRenderer({
    createElement: tag => ({ tag, children: [], props: {} }),
    createText: text => ({ text }),
    createComment: text => ({ text: '', comment: text }),
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.children = [{ text, parent: node }] },
    patchProp: (node, key, _old, value) => { node.props[key] = value },
    insert: (node, parent, anchor) => {
      if (node.parent) {
        const oldIndex = node.parent.children.indexOf(node)
        if (oldIndex >= 0) node.parent.children.splice(oldIndex, 1)
      }
      node.parent = parent
      const index = anchor ? parent.children.indexOf(anchor) : -1
      parent.children.splice(index < 0 ? parent.children.length : index, 0, node)
    },
    remove: (node) => {
      const index = node.parent?.children.indexOf(node) ?? -1
      if (index >= 0) node.parent.children.splice(index, 1)
    },
    parentNode: node => node.parent,
    nextSibling: (node) => {
      const siblings = node.parent?.children ?? []
      return siblings[siblings.indexOf(node) + 1] ?? null
    }
  })
  const groupId = vue.ref(1)
  const app = renderer.createApp({ render: () => vue.h(exports.default, { groupId: groupId.value }) })
  app.component('UIcon', {
    props: ['name'],
    render() {
      return vue.h('i', { 'data-icon': this.name })
    }
  })
  const root = { children: [] }
  app.mount(root)

  const text = node => node.text ?? (node.children ?? []).map(text).join('')
  assert.match(text(root), /Loading challenge results/)
  groupId.value = 2
  await vue.nextTick()
  pending.get(1).resolve({ totalPassedChallenges: 99 })
  pending.get(2).resolve({
    totalPassedChallenges: 2,
    challengesByStatus: [{}, {}, {}],
    firstPlaces: { time: 1, duration: 2, messages: 3 },
    secondPlaces: { time: 0, duration: 1, messages: 0 },
    thirdPlaces: { time: 0, duration: 0, messages: 2 }
  })
  await new Promise(resolve => setImmediate(resolve))
  assert.match(text(root), /2 \/ 3 passed/)
  assert.match(text(root), /6\s+1\s+2/)
  assert.doesNotMatch(text(root), /99/)
  const icons = node => [
    ...(node.props?.['data-icon'] ? [node.props['data-icon']] : []),
    ...(node.children ?? []).flatMap(icons)
  ]
  assert.deepEqual(icons(root), ['lucide-trophy', 'lucide-star', 'lucide-star'])

  groupId.value = 3
  await vue.nextTick()
  assert.match(text(root), /Loading challenge results/)
  pending.get(3).reject(new Error('Server error'))
  await new Promise(resolve => setImmediate(resolve))
  assert.match(text(root), /Couldn't load challenge results: Server error/)
  app.unmount()
})
