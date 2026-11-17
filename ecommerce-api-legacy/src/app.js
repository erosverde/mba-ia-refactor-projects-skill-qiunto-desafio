const express = require('express');
const { loadConfig } = require('./config');
const { openStore } = require('./models/store');
const { createRoutes } = require('./routes/api');
const { CheckoutError } = require('./services/checkout');

async function createApp(config = loadConfig()) {
    const store = await openStore();
    const app = express();
    app.use(express.json());
    app.use(createRoutes(store, config));
    app.use((error, req, res, next) => {
        if (res.headersSent) return next(error);
        if (error instanceof CheckoutError) return res.status(error.status).send(error.message);
        if (error.type === 'entity.parse.failed') return res.status(400).send('JSON inválido');
        if (error.type === 'entity.too.large') return res.status(413).send('Corpo da requisição muito grande');
        console.error('Falha interna ao processar requisição');
        res.status(500).send('Erro interno');
    });
    return { app, close: store.close };
}

if (require.main === module) {
    const config = loadConfig();
    createApp(config).then(({ app }) => {
        const server = app.listen(config.port, config.host, () => {
            console.log(`API de cursos em http://${config.host}:${server.address().port}`);
        });
    }).catch(() => {
        console.error('Falha na inicialização da API');
        process.exitCode = 1;
    });
}

module.exports = { createApp };
