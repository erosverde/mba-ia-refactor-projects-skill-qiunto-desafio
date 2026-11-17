const express = require('express');
const { createControllers } = require('../controllers/api');

function createRoutes(store, config) {
    const router = express.Router();
    const handlers = createControllers(store, config);
    const wrap = handler => (req, res, next) => Promise.resolve(handler(req, res)).catch(next);
    router.post('/api/checkout', wrap(handlers.checkout));
    router.get('/api/admin/financial-report', handlers.requireAdmin, wrap(handlers.report));
    router.delete('/api/users/:id', handlers.requireAdmin, wrap(handlers.deleteUser));
    return router;
}

module.exports = { createRoutes };
