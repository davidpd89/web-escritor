/**
 * Minimal, dependency-free ZIP writer (STORE method — no compression).
 *
 * Written to replace a third-party ZIP library (window.fflate) that the
 * original kit-prensa-escritor.js expected but that was never vendored
 * anywhere in this repository, and that this site does not load from a
 * CDN (strict script-src 'self', no third-party runtime dependencies).
 *
 * STORE (uncompressed) is a deliberate, valid choice here, not just a
 * workaround: press-kit payloads are short text files plus JPEG/PNG/WebP
 * images that are already compressed, so DEFLATE would save little to
 * nothing while adding real implementation risk. STORE is simpler to
 * get byte-correct and is universally supported by every ZIP reader.
 *
 * Implements just enough of the ZIP 2.0 (PKWARE) spec for small,
 * single-volume archives: local file headers, a central directory, and
 * the end-of-central-directory record. No ZIP64 (not needed under the
 * multi-GiB threshold), no encryption, no data descriptors.
 */

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table[n] = c >>> 0;
  }
  return table;
})();

export function crc32(bytes) {
  let crc = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) {
    crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

export function strToU8(str) {
  return new TextEncoder().encode(str);
}

function dosDateTime(date) {
  const time = ((date.getHours() & 0x1f) << 11) | ((date.getMinutes() & 0x3f) << 5) | ((date.getSeconds() >> 1) & 0x1f);
  const year = date.getFullYear() - 1980;
  const dosDate = ((year & 0x7f) << 9) | (((date.getMonth() + 1) & 0xf) << 5) | (date.getDate() & 0x1f);
  return { time: time & 0xffff, date: dosDate & 0xffff };
}

class ByteWriter {
  constructor() { this.chunks = []; this.length = 0; }
  u8(v) { this.chunks.push(Uint8Array.of(v & 0xff)); this.length += 1; return this; }
  u16(v) { this.chunks.push(Uint8Array.of(v & 0xff, (v >>> 8) & 0xff)); this.length += 2; return this; }
  u32(v) { this.chunks.push(Uint8Array.of(v & 0xff, (v >>> 8) & 0xff, (v >>> 16) & 0xff, (v >>> 24) & 0xff)); this.length += 4; return this; }
  bytes(b) { this.chunks.push(b); this.length += b.length; return this; }
  toU8() {
    const out = new Uint8Array(this.length);
    let offset = 0;
    for (const chunk of this.chunks) { out.set(chunk, offset); offset += chunk.length; }
    return out;
  }
}

/**
 * @param {Record<string, Uint8Array>} files - path -> file bytes. Options
 *   objects (as used by fflate's [bytes, {level}] tuple form) are also
 *   accepted and ignored, since STORE has no compression level.
 * @param {{mtime?: Date}} [options]
 * @returns {Uint8Array}
 */
export function zipStoreSync(files, options = {}) {
  const mtime = options.mtime instanceof Date ? options.mtime : new Date();
  const { time: dosTime, date: dosDate } = dosDateTime(mtime);
  const local = new ByteWriter();
  const central = new ByteWriter();
  let entryCount = 0;

  for (const path of Object.keys(files)) {
    const raw = files[path];
    const bytes = Array.isArray(raw) ? raw[0] : raw;
    if (!(bytes instanceof Uint8Array)) {
      throw new TypeError(`zipStoreSync: "${path}" must be a Uint8Array`);
    }
    const nameBytes = strToU8(path);
    const crc = crc32(bytes);
    const offset = local.length;

    local.u32(0x04034b50)
      .u16(20).u16(0x0800).u16(0).u16(dosTime).u16(dosDate)
      .u32(crc).u32(bytes.length).u32(bytes.length)
      .u16(nameBytes.length).u16(0)
      .bytes(nameBytes).bytes(bytes);

    central.u32(0x02014b50)
      .u16(20).u16(20).u16(0x0800).u16(0).u16(dosTime).u16(dosDate)
      .u32(crc).u32(bytes.length).u32(bytes.length)
      .u16(nameBytes.length).u16(0).u16(0).u16(0).u16(0).u32(0)
      .u32(offset)
      .bytes(nameBytes);

    entryCount += 1;
  }

  const centralBytes = central.toU8();
  const end = new ByteWriter();
  end.u32(0x06054b50)
    .u16(0).u16(0)
    .u16(entryCount).u16(entryCount)
    .u32(centralBytes.length).u32(local.length)
    .u16(0);

  const localBytes = local.toU8();
  const endBytes = end.toU8();
  const out = new Uint8Array(localBytes.length + centralBytes.length + endBytes.length);
  out.set(localBytes, 0);
  out.set(centralBytes, localBytes.length);
  out.set(endBytes, localBytes.length + centralBytes.length);
  return out;
}
