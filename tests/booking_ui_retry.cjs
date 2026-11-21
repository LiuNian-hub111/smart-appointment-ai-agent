// Exercise the actual page script with a dropped confirmation response.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
class Element {
    constructor() { this.children = []; this.disabled = false; this.value = ''; }
    append(...items) { this.children.push(...items); }
    appendChild(item) { this.append(item); }
    addEventListener() {}
    scrollTo() {}
    focus() {}
}
const elements = new Map();
const storage = new Map();
const requests = [];
const context = {
    document: {
        getElementById: id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
        createElement: () => new Element()
    },
    window: {addEventListener() {}},
    sessionStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)},
    crypto: {randomUUID: () => 'fixed-request'},
    AbortController, setTimeout, clearTimeout, console,
    requestAnimationFrame: callback => callback(),
    fetch: async (_, options) => {
        requests.push(JSON.parse(options.body));
        if (requests.length === 1) throw Error('response lost after server commit');
        return {ok: true, json: async () => ({schedule_id: 42})};
    }
};
const source = fs.readFileSync('web/templates/index.html', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
vm.createContext(context);
vm.runInContext(source, context);
(async () => {
    const proposal = {teacher_id: 1, teacher_name: '老师A', start_time: '2026-12-06T15:00:00+08:00', end_time: '2026-12-06T16:00:00+08:00', course: '物理'};
    context.receiveBooking('[BOOKING]' + JSON.stringify(proposal) + '[REPLY]请确认');
    const card = elements.get('chat-box').children.at(-1);
    const button = card.children[2];
    await button.onclick();
    assert.equal(button.textContent, '重试确认');
    assert.equal(JSON.parse(storage.get('pending-lesson-confirmations'))[0].request_id, 'fixed-request');
    await button.onclick();
    assert.deepEqual(requests[0], requests[1]);
    assert.equal(button.textContent, '已确认');
    assert.equal(storage.get('pending-lesson-confirmations'), '[]');
    console.log('PASS: lost reply retries with the same request ID and payload');
})().catch(error => { console.error(error); process.exitCode = 1; });
