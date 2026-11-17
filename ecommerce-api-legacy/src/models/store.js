const sqlite3 = require('sqlite3');

async function openStore() {
    const db = new sqlite3.Database(':memory:');
    const exec = sql => new Promise((resolve, reject) => {
        db.exec(sql, error => error ? reject(error) : resolve());
    });
    const run = (sql, params) => new Promise((resolve, reject) => {
        db.run(sql, params, function (error) {
            if (error) return reject(error);
            resolve({ id: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params) => new Promise((resolve, reject) => {
        db.get(sql, params, (error, row) => error ? reject(error) : resolve(row));
    });
    const all = (sql, params) => new Promise((resolve, reject) => {
        db.all(sql, params, (error, rows) => error ? reject(error) : resolve(rows));
    });
    const close = () => new Promise((resolve, reject) => {
        db.close(error => error ? reject(error) : resolve());
    });

    try {
        await exec(`
            PRAGMA foreign_keys = ON;
            CREATE TABLE users (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE,
                pass TEXT, active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
            CREATE TABLE enrollments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                course_id INTEGER NOT NULL REFERENCES courses(id)
            );
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY,
                enrollment_id INTEGER UNIQUE NOT NULL REFERENCES enrollments(id),
                amount REAL NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
            CREATE INDEX enrollments_by_course ON enrollments(course_id);
            INSERT INTO users (id, name, email) VALUES (1, 'Leonan', 'leonan@fullcycle.com.br');
            INSERT INTO courses (id, title, price, active)
                VALUES (1, 'Clean Architecture', 997.00, 1), (2, 'Docker', 497.00, 1);
            INSERT INTO enrollments (user_id, course_id) VALUES (1, 1);
            INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID');
        `);
    } catch (error) {
        await close();
        throw error;
    }

    // A transaction owns the connection until commit or rollback.
    let pending = Promise.resolve();
    function serialized(operation) {
        const result = pending.then(operation);
        pending = result.catch(() => {});
        return result;
    }

    return {
        close: () => serialized(close),
        transaction: operation => serialized(async () => {
            await exec('BEGIN IMMEDIATE');
            try {
                const result = await operation({
                    findCourse: id => get('SELECT id, price FROM courses WHERE id = ? AND active = 1', [id]),
                    findUser: email => get('SELECT id, pass FROM users WHERE email = ? AND active = 1', [email]),
                    createUser: (name, email, hash) => run(
                        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash]
                    ),
                    createEnrollment: (userId, courseId) => run(
                        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]
                    ),
                    recordPayment: (id, amount) => run(
                        "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, 'PAID')", [id, amount]
                    ),
                    auditCheckout: (courseId, userId) => run(
                        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                        [`Checkout curso ${courseId} por ${userId}`]
                    )
                });
                await exec('COMMIT');
                return result;
            } catch (error) {
                await exec('ROLLBACK');
                throw error;
            }
        }),
        financialRows: () => serialized(() => all(`
            SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
                   u.name AS student, p.amount, p.status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id AND u.active = 1
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `, [])),
        anonymizeUser: id => serialized(() => run(
            "UPDATE users SET active = 0, name = 'Unknown', email = NULL, pass = NULL WHERE id = ? AND active = 1",
            [id]
        ))
    };
}

module.exports = { openStore };
