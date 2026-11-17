const { randomBytes, scrypt, timingSafeEqual } = require('crypto');
const { promisify } = require('util');

const derive = promisify(scrypt);

async function hashPassword(password) {
    const salt = randomBytes(16).toString('hex');
    const hash = await derive(password, salt, 64);
    return `${salt}:${hash.toString('hex')}`;
}

async function verifyPassword(password, stored) {
    if (!stored) return false;
    const [salt, digest] = stored.split(':');
    const expected = Buffer.from(digest, 'hex');
    const actual = await derive(password, salt, expected.length);
    return timingSafeEqual(expected, actual);
}

module.exports = { hashPassword, verifyPassword };
