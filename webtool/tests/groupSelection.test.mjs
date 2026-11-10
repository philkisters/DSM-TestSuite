import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createRequire, registerHooks } from 'node:module'
import test from 'node:test'
import { pathToFileURL } from 'node:url'
import { runInNewContext } from 'node:vm'
import { compileScript, parse } from '@vue/compiler-sfc'
import { createPinia, defineStore, setActivePinia } from 'pinia'
import ts from 'typescript'

const piniaRequire = createRequire(import.meta.resolve('pinia'))
const vue = await import(new URL('./index.mjs', pathToFileURL(piniaRequire.resolve('vue/package.json'))))

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith('~~/')) {
      return nextResolve(new URL(`../${specifier.slice(3)}.ts`, import.meta.url).href, context)
    }
    return nextResolve(specifier, context)
  }
})

globalThis.defineStore = defineStore
globalThis.defineNuxtPlugin = plugin => plugin
const { useSettingsStore } = await import('../app/stores/settings.ts')
globalThis.useSettingsStore = useSettingsStore
const { useGroupStore } = await import('../app/stores/group.ts')
const { default: loadSettings } = await import('../app/plugins/settings.client.ts')

const group = (id, name = `Group ${id}`) => ({ id, name, vm_ip: '127.0.0.1' })

function setup(saved) {
  const data = new Map(saved === undefined ? [] : [['dsm-settings', JSON.stringify(saved)]])
  globalThis.localStorage = {
    getItem: key => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
    removeItem: key => data.delete(key)
  }
  globalThis.useToast = () => ({ add: () => {} })
  setActivePinia(createPinia())
  loadSettings()
  return { store: useGroupStore(), data }
}

function mockResponses(t, groups, health = []) {
  return t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === '/testsuite/groups') return Response.json(groups)
    if (url === '/testsuite/groups/health') return Response.json(health)
    throw new Error(`Unexpected request: ${url}`)
  })
}

test('restores a saved group and rebinds it to the latest returned group', async (t) => {
  const { store, data } = setup({ activeGroupId: 2 })
  const fetchMock = mockResponses(t, [group(1), group(2)])
  await store.fetchGroups()
  assert.equal(store.initialized, true)
  assert.strictEqual(store.activeGroup, store.groups[1])

  fetchMock.mock.mockImplementation(async url => Response.json(
    url === '/testsuite/groups' ? [group(2, 'Updated group')] : []
  ))
  await store.fetchGroups()
  assert.strictEqual(store.activeGroup, store.groups[0])
  assert.equal(store.activeGroup.name, 'Updated group')

  store.removeActiveGroup()
  await vue.nextTick()
  assert.equal(store.activeGroup, null)
  assert.equal(JSON.parse(data.get('dsm-settings')).activeGroupId, null)
  store.setActiveGroup(2)
  await vue.nextTick()
  assert.equal(JSON.parse(data.get('dsm-settings')).activeGroupId, 2)
})

test('clears a saved or previously active group absent from the returned list', async (t) => {
  const { store, data } = setup({ activeGroupId: 2 })
  const fetchMock = mockResponses(t, [group(2)])
  await store.fetchGroups()
  fetchMock.mock.mockImplementation(async url => Response.json(
    url === '/testsuite/groups' ? [group(1)] : []
  ))
  await store.fetchGroups()
  await vue.nextTick()
  assert.equal(store.activeGroup, null)
  assert.equal(JSON.parse(data.get('dsm-settings')).activeGroupId, null)
})

test('group initialization does not depend on health status, and group fetch failures do not initialize', async (t) => {
  const { store } = setup({ activeGroupId: 2 })
  t.mock.method(console, 'error', () => {})
  const fetchMock = t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === '/testsuite/groups') return Response.json([group(2)])
    throw new Error('Health unavailable')
  })
  await store.fetchGroups()
  assert.equal(store.initialized, true)
  assert.equal(store.activeGroup.id, 2)

  const fresh = setup({ activeGroupId: 2 }).store
  fetchMock.mock.mockImplementation(async () => {
    throw new Error('Groups unavailable')
  })
  await fresh.fetchGroups()
  assert.equal(fresh.initialized, false)
  assert.equal(useSettingsStore().activeGroupId, 2)
})

test('selector waits for group initialization and only opens when no valid selection exists', async (t) => {
  const source = readFileSync(new URL('../app/app.vue', import.meta.url), 'utf8')
  const compiled = compileScript(parse(source).descriptor, { id: 'app', inlineTemplate: true }).content
  const javascript = ts.transpileModule(compiled, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText
  const exports = {}
  let currentStore
  runInNewContext(javascript, {
    exports,
    require: (name) => {
      assert.equal(name, 'vue')
      return vue
    },
    computed: vue.computed,
    onMounted: vue.onMounted,
    onBeforeUnmount: vue.onBeforeUnmount,
    useGroupStore: () => currentStore,
    useHead: () => {},
    useSeoMeta: () => {}
  })

  const renderer = vue.createRenderer({
    createElement: tag => ({ tag, children: [] }),
    createText: text => ({ text }),
    createComment: text => ({ text }),
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.text = text },
    patchProp: () => {},
    insert: (node, parent, anchor) => {
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
  const hasSelector = node => node.tag === 'selector' || (node.children ?? []).some(hasSelector)
  const tree = node => ({ tag: node.tag, text: node.text, children: node.children?.map(tree) })
  let resolveGroups
  const fetchMock = t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === '/testsuite/groups') {
      return new Promise((resolve) => {
        resolveGroups = resolve
      })
    }
    return Response.json([])
  })

  for (const [saved, groups, expected] of [
    [{ activeGroupId: 2 }, [group(2)], false],
    [undefined, [group(2)], true],
    [{ activeGroupId: 3 }, [group(2)], true]
  ]) {
    currentStore = setup(saved).store
    const fetchGroups = currentStore.fetchGroups
    let fetchDone
    currentStore.fetchGroups = () => {
      fetchDone = fetchGroups()
      return fetchDone
    }
    currentStore.startHealthUpdates = () => {}
    currentStore.stopHealthUpdates = () => {}
    const app = renderer.createApp(exports.default)
    for (const name of ['UApp', 'NuxtLayout']) {
      app.component(name, {
        render() {
          return vue.h('div', this.$slots.default?.())
        }
      })
    }
    app.component('NuxtPage', { render: () => vue.h('div') })
    app.component('GroupSelectionModal', { render: () => vue.h('selector') })
    const root = { children: [] }
    app.mount(root)
    assert.equal(hasSelector(root), false)
    resolveGroups(Response.json(groups))
    await fetchDone
    await vue.nextTick()
    assert.equal(currentStore.initialized, true)
    assert.equal(hasSelector(root), expected, JSON.stringify(tree(root)))
    if (!expected) {
      currentStore.removeActiveGroup()
      await vue.nextTick()
      assert.equal(hasSelector(root), true)
      currentStore.setActiveGroup(2)
      await vue.nextTick()
      assert.equal(hasSelector(root), false)
    }
    app.unmount()
  }
  assert.equal(fetchMock.mock.callCount(), 6)
})
