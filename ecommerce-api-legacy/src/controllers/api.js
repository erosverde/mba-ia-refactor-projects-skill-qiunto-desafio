const { timingSafeEqual } = require('crypto');
const { checkout } = require('../services/checkout');
const { financialReport } = require('../services/financial-report');

function createControllers(store, config) {
    return {
        requireAdmin(req, res, next) {
            const supplied = req.get('Authorization');
            if (!supplied) return res.status(401).send('Autenticação obrigatória');
            const provided = Buffer.from(supplied);
            const expected = Buffer.from(`Bearer ${config.adminToken}`);
            if (!config.adminToken || provided.length !== expected.length || !timingSafeEqual(provided, expected)) {
                return res.status(403).send('Acesso negado');
            }
            next();
        },
        async checkout(req, res) {
            const id = await checkout(store, config, req.body);
            res.json({ msg: 'Sucesso', enrollment_id: id });
        },
        async report(req, res) {
            res.json(await financialReport(store));
        },
        async deleteUser(req, res) {
            const id = Number(req.params.id);
            if (!/^\d+$/.test(req.params.id) || !Number.isSafeInteger(id) || id < 1) {
                return res.status(400).send('ID inválido');
            }
            const result = await store.anonymizeUser(id);
            if (result.changes === 0) return res.status(404).send('Usuário não encontrado');
            res.send('Usuário excluído. Histórico financeiro preservado.');
        }
    };
}

module.exports = { createControllers };
