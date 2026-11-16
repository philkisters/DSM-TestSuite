import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { registerHooks, stripTypeScriptTypes } from 'node:module'
import test from 'node:test'
import { compileScript, parse } from '@vue/compiler-sfc'

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith('~~/')) {
      return nextResolve(new URL(`../${specifier.slice(3)}.ts`, import.meta.url).href, context)
    }
    if (specifier.startsWith('~/')) {
      return nextResolve(new URL(`../app/${specifier.slice(2)}.ts`, import.meta.url).href, context)
    }
    return nextResolve(specifier, context)
  },
  load(url, context, nextLoad) {
    if (url.endsWith('/Network/ImageModal.vue') || url.endsWith('/Util/HashHint.vue')) {
      const source = readFileSync(new URL(url), 'utf8')
      const script = compileScript(parse(source).descriptor, { id: url }).content
      return {
        format: 'module',
        source: stripTypeScriptTypes(`import { ref, computed, watch } from 'vue'\n${script}`, { mode: 'transform' }),
        shortCircuit: true
      }
    }
    if (url.endsWith('/shared/protocol.ts')) {
      return {
        format: 'module',
        source: stripTypeScriptTypes(readFileSync(new URL(url), 'utf8'), { mode: 'transform' }),
        shortCircuit: true
      }
    }
    return nextLoad(url, context)
  }
})

const { getPeerFingers, getPeerImages, putPeerImage } = await import('../app/services/backend/proxy.service.ts')
const { usePeerImages } = await import('../app/composables/usePeerImages.ts')
const { readPngAsBase64 } = await import('../app/utils/png.ts')
const { default: ImageModal } = await import('../app/components/Network/ImageModal.vue')
const { default: HashHint } = await import('../app/components/Util/HashHint.vue')
const { effectScope, reactive, ref } = await import('vue')
const envelope = {
  sender: { network_id: 'network', peer_id: 'peer-a' },
  receiver: { network_id: 'network', peer_id: 'Webtool' }
}

test('requests and deduplicates fingers for the selected peer', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json({
    ...envelope,
    code: 6,
    content: {
      fingers: [
        { network_id: 'network', peer_id: 'peer-b' },
        { network_id: 'network', peer_id: 'peer-b' },
        { network_id: 'network', peer_id: 'peer-a' }
      ]
    }
  }))
  const controller = new AbortController()
  assert.deepEqual(await getPeerFingers('network', 'peer-a', controller.signal), ['peer-b', 'peer-a'])
  const [url, options] = fetchMock.mock.calls[0].arguments
  assert.equal(url, '/proxy/message')
  assert.equal(options.method, 'POST')
  assert.equal(options.signal, controller.signal)
  assert.deepEqual(JSON.parse(options.body), {
    sender: { network_id: 'network', peer_id: 'Webtool' },
    receiver: { network_id: 'network', peer_id: 'peer-a' },
    code: 5,
    content: {}
  })
})

test('reports HTTP, peer, and malformed response errors', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 400 }))
  await assert.rejects(getPeerFingers('network', 'peer-a'), /400/)

  fetchMock.mock.mockImplementation(async () => Response.json({ ...envelope, code: -1, content: { message: 'not joined' } }))
  await assert.rejects(getPeerFingers('network', 'peer-a'), /not joined/)

  fetchMock.mock.mockImplementation(async () => Response.json({ ...envelope, code: 6, content: {} }))
  await assert.rejects(getPeerFingers('network', 'peer-a'), /fingers/)

  fetchMock.mock.mockImplementation(async () => Response.json({
    ...envelope,
    code: 6,
    content: { fingers: [{ network_id: 'other', peer_id: 'peer' }] }
  }))
  await assert.rejects(getPeerFingers('network', 'peer-a'), /different network/)

  fetchMock.mock.mockImplementation(async () => Response.json({
    ...envelope,
    sender: { network_id: 'network', peer_id: 'other' },
    code: 6,
    content: { fingers: [] }
  }))
  await assert.rejects(getPeerFingers('network', 'peer-a'), /incorrect sender or receiver/)
})

test('requests the selected peer’s image IDs, including an empty list', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json({
    ...envelope,
    code: 9,
    content: { images: ['image-1', 'image-2'] }
  }))
  assert.deepEqual(await getPeerImages('network', 'peer-a'), ['image-1', 'image-2'])
  const [url, options] = fetchMock.mock.calls[0].arguments
  assert.equal(url, '/proxy/message')
  assert.deepEqual(JSON.parse(options.body), {
    sender: { network_id: 'network', peer_id: 'Webtool' },
    receiver: { network_id: 'network', peer_id: 'peer-a' },
    code: 8,
    content: {}
  })

  fetchMock.mock.mockImplementation(async () => Response.json({ ...envelope, code: 9, content: { images: [] } }))
  assert.deepEqual(await getPeerImages('network', 'peer-a'), [])
})

test('rejects invalid image responses and propagates peer errors', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json({
    ...envelope, code: 9, content: { images: ['image-1', 42] }
  }))
  await assert.rejects(getPeerImages('network', 'peer-a'), /images/)

  fetchMock.mock.mockImplementation(async () => Response.json({
    ...envelope, code: 6, content: { images: [] }
  }))
  await assert.rejects(getPeerImages('network', 'peer-a'), /code/)

  fetchMock.mock.mockImplementation(async () => Response.json({
    ...envelope, code: -1, content: { message: 'not joined' }
  }))
  await assert.rejects(getPeerImages('network', 'peer-a'), /not joined/)
})

test('keeps per-peer image lists across selections and ignores stale responses', async (t) => {
  const pending = []
  t.mock.method(globalThis, 'fetch', (_url, options) => new Promise((resolve) => {
    pending.push({ resolve, options })
  }))
  const network = ref('network')
  const selected = ref(null)
  const scope = effectScope()
  const images = scope.run(() => usePeerImages(network, selected))
  const respond = async (index, peer, images) => {
    pending[index].resolve(Response.json({
      sender: { network_id: 'network', peer_id: peer },
      receiver: envelope.receiver,
      code: 9,
      content: { images }
    }))
    await new Promise(resolve => setImmediate(resolve))
  }

  assert.equal(images.value.get('peer-a'), undefined)
  selected.value = 'peer-a'
  selected.value = 'peer-b'
  await respond(1, 'peer-b', [])
  await respond(0, 'peer-a', ['one'])
  assert.deepEqual(images.value.get('peer-a'), ['one'])
  assert.deepEqual(images.value.get('peer-b'), [])

  selected.value = 'peer-a'
  selected.value = null
  selected.value = 'peer-a'
  assert.equal(pending[2].options.signal.aborted, true)
  await respond(3, 'peer-a', ['one', 'two'])
  await respond(2, 'peer-a', [])
  assert.deepEqual(images.value.get('peer-a'), ['one', 'two'])

  selected.value = 'peer-b'
  network.value = 'another-network'
  assert.equal(pending[4].options.signal.aborted, true)
  assert.equal(images.value.size, 0)
  scope.stop()
  assert.equal(pending[5].options.signal.aborted, true)
})

test('sends a put image message and requires an acknowledgement', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json({
    ...envelope, code: 0, content: {}
  }))
  await putPeerImage('network', 'peer-a', 'image-0.png', 'iVBORw0KGgo=')
  const [url, options] = fetchMock.mock.calls[0].arguments
  assert.equal(url, '/proxy/message')
  assert.deepEqual(JSON.parse(options.body), {
    sender: { network_id: 'network', peer_id: 'Webtool' },
    receiver: { network_id: 'network', peer_id: 'peer-a' },
    code: 7,
    content: { image_id: 'image-0.png', image: 'iVBORw0KGgo=' }
  })

  fetchMock.mock.mockImplementation(async () => Response.json({ ...envelope, code: 9, content: {} }))
  await assert.rejects(putPeerImage('network', 'peer-a', 'image-0.png', 'abc'), /code/)
  fetchMock.mock.mockImplementation(async () => Response.json({
    ...envelope, code: -1, content: { message: 'image rejected' }
  }))
  await assert.rejects(putPeerImage('network', 'peer-a', 'image-0.png', 'abc'), /image rejected/)
})

test('encodes PNG files without the data URL prefix and rejects invalid files', async (t) => {
  const previousReader = globalThis.FileReader
  t.after(() => {
    if (previousReader === undefined) delete globalThis.FileReader
    else globalThis.FileReader = previousReader
  })
  globalThis.FileReader = class {
    async readAsDataURL(file) {
      this.result = `data:${file.type};base64,${Buffer.from(await file.arrayBuffer()).toString('base64')}`
      this.onload()
    }
  }
  const png = new File([Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10])], 'test.PNG', { type: 'image/png' })
  assert.equal(await readPngAsBase64(png), 'iVBORw0KGgo=')
  await assert.rejects(readPngAsBase64(new File(['not png'], 'test.png')), /valid PNG/)
  await assert.rejects(readPngAsBase64(new File([await png.arrayBuffer()], 'test.jpg')), /valid PNG/)
})

test('defaults the image ID to the filename without overwriting a custom ID', async (t) => {
  const previousReader = globalThis.FileReader
  t.after(() => {
    if (previousReader === undefined) delete globalThis.FileReader
    else globalThis.FileReader = previousReader
  })
  globalThis.FileReader = class {
    async readAsDataURL(file) {
      this.result = `data:image/png;base64,${Buffer.from(await file.arrayBuffer()).toString('base64')}`
      this.onload()
    }
  }
  const scope = effectScope()
  const modal = scope.run(() => ImageModal.setup({
    networkId: 'network', peers: [{ peerId: 'peer-a' }], selectedPeer: 'peer-a'
  }, { expose() {} }))
  const png = name => new File([Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10])], name)
  modal.openModal()
  modal.file.value = png('first.png')
  assert.equal(modal.imageId.value, 'first.png')
  modal.file.value = png('second.png')
  assert.equal(modal.imageId.value, 'second.png')
  modal.imageId.value = 'custom-id'
  modal.file.value = png('third.png')
  assert.equal(modal.imageId.value, 'custom-id')
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(modal.preview.value, 'data:image/png;base64,iVBORw0KGgo=')
  assert.equal(modal.canSubmit.value, false)
  scope.stop()
})

test('shared hash hint hashes the exact ID and updates when it changes', () => {
  const props = reactive({ value: '' })
  const scope = effectScope()
  const hint = scope.run(() => HashHint.setup(props, { expose() {} }))
  assert.equal(hint.hash.value, '-')
  props.value = 'image-0.png'
  assert.equal(hint.hash.value, createHash('sha256').update('image-0.png').digest('hex').slice(0, 8))
  props.value = ' image-0.png '
  assert.equal(hint.hash.value, createHash('sha256').update(' image-0.png ').digest('hex').slice(0, 8))
  scope.stop()
})
