function loadConfig(env = process.env) {
    return {
        host: env.HOST || '127.0.0.1',
        port: Number(env.PORT || 3000),
        adminToken: env.ADMIN_API_TOKEN || '',
        simulatePayments: env.NODE_ENV === 'test' && env.PAYMENT_MODE === 'test'
    };
}

module.exports = { loadConfig };
