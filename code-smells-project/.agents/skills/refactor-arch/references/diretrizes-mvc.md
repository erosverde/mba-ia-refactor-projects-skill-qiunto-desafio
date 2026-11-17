# Diretrizes MVC para aplicações web

- **Models** representam entidades e operações de persistência. Concentre o acesso a dados, consultas parametrizadas e relacionamentos nessa fronteira.
- **Views/Routes** associam método e caminho ao controller e apresentam a resposta. Em APIs, a representação pode ser um serializador JSON com campos explícitos.
- **Controllers** traduzem a entrada HTTP em uma operação da aplicação e seu resultado em resposta. Extraia regras complexas para serviços quando isso simplificar as responsabilidades.
- **Configuração e inicialização** ficam junto ao ponto de composição da aplicação. Carregue segredos externamente e centralize tratamento de erros.
- Adapte a estrutura à stack e reaproveite módulos úteis já existentes. Preserve caminhos, métodos e formatos de resposta, exceto nas correções aprovadas que exijam alterar o contrato.
- Valide o ponto de entrada, o carregamento das rotas, as operações de persistência e os contratos HTTP com fixtures locais.
