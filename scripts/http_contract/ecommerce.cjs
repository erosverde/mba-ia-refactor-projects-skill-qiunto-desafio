const assert = require('assert').strict;
const http = require('http');
const { once } = require('events');
const { join } = require('path');
const { createApp } = require(join(process.cwd(), 'src/app'));
const { loadConfig } = require(join(process.cwd(), 'src/config'));
const token = 'fixture-admin-token';

async function withServer(config, exercise) {
    const { app, close } = await createApp(config);
    const server = app.listen(0, '127.0.0.1');
    try {
        await once(server, 'listening');
        console.log('BOOT OK: Express com SQLite :memory:');
        const port = server.address().port;
        await exercise((method, path, expected, data, auth) => new Promise((resolve, reject) => {
            const body = data && JSON.stringify(data);
            const headers = {};
            if (body) {
                headers['Content-Type'] = 'application/json';
                headers['Content-Length'] = Buffer.byteLength(body);
            }
            if (auth) headers.Authorization = 'Bearer ' + auth;
            const req = http.request({ host: '127.0.0.1', port, method, path, headers }, res => {
                let text = '';
                res.setEncoding('utf8');
                res.on('data', chunk => { text += chunk; });
                res.on('end', () => {
                    try {
                        assert.equal(res.statusCode, expected, method + ' ' + path);
                        console.log(method, path, res.statusCode);
                        resolve((res.headers['content-type'] || '').includes('application/json') ? JSON.parse(text) : text);
                    } catch (err) { reject(err); }
                });
            });
            req.setTimeout(10000, () => req.destroy(new Error(method + ' ' + path + ': timeout')));
            req.on('error', reject);
            req.end(body);
        }));
    } finally {
        await new Promise(resolve => server.close(resolve));
        await close();
    }
}

const fixture = { usr: 'Teste Local', eml: 'checkout@example.test', pwd: 'primeira-senha', c_id: 2, card: '4000000000000000' };
const report = '/api/admin/financial-report';
const checkout = '/api/checkout';

(async () => {
    const config = { ADMIN_API_TOKEN: token, PAYMENT_MODE: 'test' };
    await withServer(loadConfig({ ...config, NODE_ENV: 'production' }), async req => {
        await req('POST', checkout, 503, fixture);
    });
    await withServer(loadConfig({ ...config, NODE_ENV: 'test' }), async req => {
        await req('GET', report, 401);
        await req('GET', report, 403, null, 'incorreto');
        await req('DELETE', '/api/users/1', 401);
        await req('DELETE', '/api/users/1', 403, null, 'incorreto');
        const before = await req('GET', report, 200, null, token);
        assert.equal(before[0].revenue, 997);
        assert.deepEqual(before[1].students, []);
        await req('POST', checkout, 400, { ...fixture, card: '5000000000000000' });
        assert.deepEqual(await req('GET', report, 200, null, token), before);
        await req('POST', checkout, 404, { ...fixture, c_id: 999 });
        const valid = { ...fixture, pwd: 'nova-senha-local' };
        const first = await req('POST', checkout, 200, valid);
        assert.equal(first.enrollment_id, 2);
        await req('POST', checkout, 401, fixture);
        await req('POST', checkout, 200, valid);
        const after = await req('GET', report, 200, null, token);
        assert.equal(after[1].revenue, 994);
        assert.equal(after[1].students.length, 2);
        assert.ok(after[1].students.every(student => student.student === fixture.usr && student.paid === 497));
        await req('DELETE', '/api/users/abc', 400, null, token);
        await req('DELETE', '/api/users/2', 200, null, token);
        await req('DELETE', '/api/users/2', 404, null, token);
        await req('DELETE', '/api/users/999', 404, null, token);
        const afterDelete = await req('GET', report, 200, null, token);
        assert.equal(afterDelete[1].revenue, 994);
        assert.deepEqual(afterDelete[1].students, [{ student: 'Unknown', paid: 497 }, { student: 'Unknown', paid: 497 }]);
        assert.equal(afterDelete[0].revenue, 997);
    });
    console.log('PASS 3/3 routes; authentication, declined checkout, and financial history');
})().catch(error => { console.error(error); process.exitCode = 1; });
