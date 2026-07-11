import { Protocol, PMTiles } from 'pmtiles';
import fs from 'fs';
import http from 'http';
import url from 'url';

// Read the file into a buffer
const buf = fs.readFileSync('/home/havb/Documents/repos/NIDO_bigfish/public/data/nido.pmtiles');

// Use the actual PMTiles class to parse
const p = new PMTiles(buf.buffer);
const h = await p.getHeader();
console.log('Header:', JSON.stringify(h, null, 2));

// Try getZxy
const result = await p.getZxy(4, 5, 9);
if (result) {
  console.log('getZxy(4,5,9) FOUND, size:', result.data.length);
  console.log('First 20 hex:', Buffer.from(result.data.slice(0,20)).toString('hex'));
} else {
  console.log('getZxy(4,5,9): NOT FOUND');
}

const result2 = await p.getZxy(3, 2, 5);
if (result2) {
  console.log('getZxy(3,2,5) FOUND, size:', result2.data.length);
} else {
  console.log('getZxy(3,2,5): NOT FOUND');
}

const result3 = await p.getZxy(5, 10, 18);
if (result3) {
  console.log('getZxy(5,10,18) FOUND, size:', result3.data.length);
} else {
  console.log('getZxy(5,10,18): NOT FOUND');
}

// Test Protocol with mock MapLibre
const proto = new Protocol();
const mockCallback = (err, data, cacheControl, expires) => {
  if (err) {
    console.log('Protocol tile ERROR:', err);
  } else {
    console.log('Protocol tile FOUND, size:', data?.length);
  }
};

const mockParams = {
  type: 'vector',
  url: 'pmtiles:///data/nido.pmtiles',
  source: 'nido',
  tile: { z: 4, x: 5, y: 9 }
};

try {
  const tileFn = proto.tile(mockParams, mockCallback);
  console.log('Protocol tile returned:', typeof tileFn);
} catch(e) {
  console.log('Protocol tile threw:', e.message);
}
