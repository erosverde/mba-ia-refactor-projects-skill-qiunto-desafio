const { hashPassword, verifyPassword } = require('./passwords');

class CheckoutError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

function checkout(store, config, body = {}) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};
    const required = [usr, eml, card].every(value => typeof value === 'string' && value.trim());
    if (!required || !Number.isSafeInteger(courseId) || courseId < 1) {
        throw new CheckoutError(400, 'Bad Request');
    }
    if (!config.simulatePayments) {
        throw new CheckoutError(503, 'Pagamento indisponível');
    }

    return store.transaction(async db => {
        const course = await db.findCourse(courseId);
        if (!course) throw new CheckoutError(404, 'Curso não encontrado');

        const user = await db.findUser(eml);
        const validPassword = typeof pwd === 'string' && pwd.length > 0 && pwd.length <= 256;
        if (user) {
            if (!validPassword || !(await verifyPassword(pwd, user.pass))) {
                throw new CheckoutError(401, 'Credenciais inválidas');
            }
        } else if (!validPassword) {
            throw new CheckoutError(400, 'Senha obrigatória para cadastro');
        }

        // The fixture only simulates a result. It never submits or stores card data.
        if (!card.startsWith('4')) throw new CheckoutError(400, 'Pagamento recusado');

        const userId = user ? user.id : (await db.createUser(usr, eml, await hashPassword(pwd))).id;
        const enrollment = await db.createEnrollment(userId, courseId);
        await db.recordPayment(enrollment.id, course.price);
        await db.auditCheckout(courseId, userId);
        return enrollment.id;
    });
}

module.exports = { checkout, CheckoutError };
