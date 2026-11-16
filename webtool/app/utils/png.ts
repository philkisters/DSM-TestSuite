export async function readPngAsBase64(file: File): Promise<string> {
  const signature = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  const pngSignature = [137, 80, 78, 71, 13, 10, 26, 10]
  if (!file.name.toLowerCase().endsWith('.png')
    || signature.length !== pngSignature.length
    || !pngSignature.every((byte, index) => signature[index] === byte)) {
    throw new Error('Choose a valid PNG file')
  }

  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') resolve(reader.result)
      else reject(new Error('Could not read PNG file'))
    }
    reader.onerror = () => reject(reader.error ?? new Error('Could not read PNG file'))
    reader.onabort = () => reject(new Error('Reading PNG file was cancelled'))
    reader.readAsDataURL(file)
  })
  const match = /^data:[^,]*;base64,(.+)$/.exec(dataUrl)
  if (!match) throw new Error('Could not encode PNG file')
  return match[1]!
}
