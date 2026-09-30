// Standalone fallback for the claude.ai artifact capabilities used by House BIM Studio.
// When the page runs outside claude.ai there is no window.claude, so projects are kept in
// this browser's localStorage and exports are downloaded with a Blob link.
(function () {
  'use strict';
  const KEY = 'hbs.projects.v1';
  const subs = [];

  const read = () => { try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { return {}; } };
  const write = obj => {
    try { localStorage.setItem(KEY, JSON.stringify(obj)); }
    catch (e) { const err = new Error('local storage is full or blocked'); err.code = 'quota_exceeded'; throw err; }
    notify();
  };
  const snapshot = () => ({
    docs: Object.entries(read())
      .map(([id, d]) => ({ id, data: () => d }))
      .sort((a, b) => String((b.data() || {}).updatedAt || '').localeCompare(String((a.data() || {}).updatedAt || '')))
  });
  function notify() { const s = snapshot(); subs.forEach(cb => { try { cb(s); } catch (e) { console.error(e); } }); }
  window.addEventListener('storage', e => { if (e.key === KEY) notify(); });

  const db = {
    doc(path) {
      const id = String(path).split('/').slice(1).join('/');
      return {
        async set(value) { const o = read(); o[id] = value; write(o); },
        async get() { const d = read()[id]; return { exists: d !== undefined, data: () => d }; },
        async delete() { const o = read(); delete o[id]; write(o); }
      };
    },
    collection() {
      const q = {
        orderBy() { return q; },
        onSnapshot(cb) { subs.push(cb); setTimeout(() => cb(snapshot()), 0); return () => { const i = subs.indexOf(cb); if (i >= 0) subs.splice(i, 1); }; }
      };
      return q;
    }
  };

  const MIME = { json: 'application/json', csv: 'text/csv;charset=utf-8', txt: 'text/plain;charset=utf-8',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' };
  const downloads = {
    async save({ filename, data }) {
      const ext = String(filename).split('.').pop().toLowerCase();
      const blob = data instanceof Blob ? data : new Blob([data], { type: MIME[ext] || 'application/octet-stream' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    }
  };

  let storageOk = true;
  try { localStorage.setItem('hbs.probe', '1'); localStorage.removeItem('hbs.probe'); } catch (e) { storageOk = false; }

  window.HBSLocalCaps = {
    use(name) {
      if (name === 'db') return Promise.resolve(storageOk ? db : null);
      if (name === 'downloads') return Promise.resolve(downloads);
      return Promise.resolve(null);
    }
  };
})();
