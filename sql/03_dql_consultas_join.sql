-- ============================================================================
-- Disciplina: Gerenciamento e Desenvolvimento em Banco de Dados
-- Banco de Dados: LOJABD
-- SGBD Alvo: MySQL 5.6
-- Etapa 3: Consultas de Verificação e Consultas Relacionais com JOIN (DQL)
-- ============================================================================

-- Verificação dos registros inseridos na Etapa 2 (DML)
SELECT * FROM CLIENTE;
SELECT * FROM PRODUTO;
SELECT * FROM COMPRA;

-- ----------------------------------------------------------------------------
-- Consulta 1:
-- Retorna o número da venda, nome do cliente, nome do produto e valor da
-- compra, ordenando a saída pelo número da compra.
-- ----------------------------------------------------------------------------
SELECT
    co.numero AS numero_venda,
    cl.nome AS nome_cliente,
    p.nome AS nome_produto,
    co.valor_compra
FROM COMPRA co
INNER JOIN CLIENTE cl ON co.codigo_cliente = cl.codigo
INNER JOIN PRODUTO p ON co.id_produto = p.id
ORDER BY co.numero ASC;

-- ----------------------------------------------------------------------------
-- Consulta 2:
-- Demonstra o nome do(s) cliente(s) e o código da compra (exibindo NULL para
-- clientes que não realizaram compras na loja).
-- ----------------------------------------------------------------------------
SELECT
    cl.nome AS nome_cliente,
    co.numero AS codigo_compra
FROM CLIENTE cl
LEFT JOIN COMPRA co ON cl.codigo = co.codigo_cliente
ORDER BY cl.codigo ASC, co.numero ASC;

-- ----------------------------------------------------------------------------
-- Consulta 3:
-- Retorna o nome do cliente (sem repetições) e o telefone dos clientes que
-- realizaram compras na loja antes da data atual.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    cl.nome AS nome_cliente,
    cl.telefone
FROM CLIENTE cl
INNER JOIN COMPRA co ON cl.codigo = co.codigo_cliente
WHERE co.data_compra < CURRENT_DATE()
ORDER BY cl.nome ASC;
